"""Build curated aggregate ChromaDB artifacts from versioned source DBs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from typing import Any, Mapping

import yaml


SCRIPT_VERSION = "1.0.0"


@dataclass(frozen=True)
class AggregateIdentity:
    name: str
    version: str
    description: str = ""


@dataclass(frozen=True)
class OutputConfig:
    persist_dir: Path
    manifest_out: Path
    overwrite: bool = False


@dataclass(frozen=True)
class SourceComponent:
    persist_dir: Path
    collection: str
    version: str


@dataclass(frozen=True)
class ComponentSpec:
    logical_name: str
    source: SourceComponent
    target_collection: str


@dataclass(frozen=True)
class ValidationConfig:
    require_unique_target_collections: bool = True
    fail_on_missing_collection: bool = True
    fail_on_doc_count_zero: bool = True
    batch_size: int = 500


@dataclass(frozen=True)
class AggregateSpec:
    aggregate: AggregateIdentity
    output: OutputConfig
    components: list[ComponentSpec]
    validation: ValidationConfig


class AggregateSpecError(ValueError):
    """Raised when an aggregate spec is invalid."""


def _expect_mapping(value: Any, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise AggregateSpecError(f"Expected mapping for '{field_name}'")
    return value


def _expect_str(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AggregateSpecError(f"Expected non-empty string for '{field_name}'")
    return value.strip()


def _expect_bool(value: Any, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise AggregateSpecError(f"Expected boolean for '{field_name}'")
    return value


def _coerce_str(value: Any, field_name: str) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    if isinstance(value, (int, float)):
        return str(value)
    raise AggregateSpecError(f"Expected non-empty string-like value for '{field_name}'")


def load_aggregate_spec(path: Path) -> AggregateSpec:
    with path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}

    data = _expect_mapping(raw, "root")
    aggregate_data = _expect_mapping(data.get("aggregate"), "aggregate")
    output_data = _expect_mapping(data.get("output"), "output")
    validation_data = _expect_mapping(data.get("validation", {}), "validation")

    raw_components = data.get("components")
    if not isinstance(raw_components, list) or not raw_components:
        raise AggregateSpecError("Expected non-empty list for 'components'")

    aggregate = AggregateIdentity(
        name=_expect_str(aggregate_data.get("name"), "aggregate.name"),
        version=_coerce_str(aggregate_data.get("version"), "aggregate.version"),
        description=str(aggregate_data.get("description", "")).strip(),
    )

    output = OutputConfig(
        persist_dir=Path(_expect_str(output_data.get("persist_dir"), "output.persist_dir")),
        manifest_out=Path(_expect_str(output_data.get("manifest_out"), "output.manifest_out")),
        overwrite=_expect_bool(output_data.get("overwrite", False), "output.overwrite"),
    )

    components: list[ComponentSpec] = []
    for index, item in enumerate(raw_components):
        component_data = _expect_mapping(item, f"components[{index}]")
        source_data = _expect_mapping(component_data.get("source"), f"components[{index}].source")
        components.append(
            ComponentSpec(
                logical_name=_expect_str(
                    component_data.get("logical_name"),
                    f"components[{index}].logical_name",
                ),
                source=SourceComponent(
                    persist_dir=Path(
                        _expect_str(
                            source_data.get("persist_dir"),
                            f"components[{index}].source.persist_dir",
                        )
                    ),
                    collection=_expect_str(
                        source_data.get("collection"),
                        f"components[{index}].source.collection",
                    ),
                    version=_coerce_str(
                        source_data.get("version"),
                        f"components[{index}].source.version",
                    ),
                ),
                target_collection=_expect_str(
                    component_data.get("target_collection"),
                    f"components[{index}].target_collection",
                ),
            )
        )

    validation = ValidationConfig(
        require_unique_target_collections=_expect_bool(
            validation_data.get("require_unique_target_collections", True),
            "validation.require_unique_target_collections",
        ),
        fail_on_missing_collection=_expect_bool(
            validation_data.get("fail_on_missing_collection", True),
            "validation.fail_on_missing_collection",
        ),
        fail_on_doc_count_zero=_expect_bool(
            validation_data.get("fail_on_doc_count_zero", True),
            "validation.fail_on_doc_count_zero",
        ),
        batch_size=int(validation_data.get("batch_size", 500)),
    )

    if validation.batch_size <= 0:
        raise AggregateSpecError("validation.batch_size must be > 0")

    if validation.require_unique_target_collections:
        seen: set[str] = set()
        for component in components:
            if component.target_collection in seen:
                raise AggregateSpecError(
                    f"Duplicate target_collection found: {component.target_collection}"
                )
            seen.add(component.target_collection)

    return AggregateSpec(
        aggregate=aggregate,
        output=output,
        components=components,
        validation=validation,
    )


def _get_git_sha() -> str | None:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return None
    sha = completed.stdout.strip()
    return sha or None


def _prepare_output_dir(output_dir: Path, overwrite: bool) -> None:
    if output_dir.exists():
        has_content = any(output_dir.iterdir())
        if has_content and not overwrite:
            raise AggregateSpecError(
                f"Output persist_dir already exists and is not empty: {output_dir}. "
                "Set output.overwrite=true to replace it."
            )
        if overwrite:
            shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)


def _write_manifest(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _copy_component(
    source_collection: Any,
    target_collection: Any,
    batch_size: int,
) -> tuple[int, str]:
    copied_count = 0
    id_hash = hashlib.sha256()
    offset = 0
    while True:
        batch = source_collection.get(
            limit=batch_size,
            offset=offset,
            include=["documents", "metadatas", "embeddings"],
        )
        ids = batch.get("ids") or []
        if not ids:
            break

        upsert_payload: dict[str, Any] = {"ids": ids}
        documents = batch.get("documents")
        metadatas = batch.get("metadatas")
        embeddings = batch.get("embeddings")
        if documents is not None:
            upsert_payload["documents"] = documents
        if metadatas is not None:
            upsert_payload["metadatas"] = metadatas
        if embeddings is not None:
            upsert_payload["embeddings"] = embeddings

        target_collection.upsert(**upsert_payload)

        for doc_id in ids:
            id_hash.update(str(doc_id).encode("utf-8"))
            id_hash.update(b"\n")
        copied_count += len(ids)
        offset += len(ids)

    return copied_count, id_hash.hexdigest()


def build_aggregate(spec: AggregateSpec) -> dict[str, Any]:
    import chromadb

    errors: list[str] = []
    created_utc = datetime.now(timezone.utc).isoformat()
    git_sha = _get_git_sha()

    _prepare_output_dir(spec.output.persist_dir, spec.output.overwrite)
    output_client = chromadb.PersistentClient(path=str(spec.output.persist_dir))

    component_payloads: list[dict[str, Any]] = []
    total_copied_count = 0
    status = "success"

    for component in spec.components:
        source_client = chromadb.PersistentClient(path=str(component.source.persist_dir))
        try:
            source_collection = source_client.get_collection(component.source.collection)
        except Exception as exc:
            message = (
                f"Missing source collection '{component.source.collection}' in "
                f"{component.source.persist_dir}: {exc}"
            )
            if spec.validation.fail_on_missing_collection:
                raise AggregateSpecError(message) from exc
            errors.append(message)
            status = "partial_success"
            continue

        source_count = source_collection.count()
        if source_count == 0 and spec.validation.fail_on_doc_count_zero:
            raise AggregateSpecError(
                f"Source collection '{component.source.collection}' has zero documents"
            )

        target_collection = output_client.get_or_create_collection(component.target_collection)
        copied_count, copied_ids_sha256 = _copy_component(
            source_collection=source_collection,
            target_collection=target_collection,
            batch_size=spec.validation.batch_size,
        )
        total_copied_count += copied_count

        component_payloads.append(
            {
                "logical_name": component.logical_name,
                "source_persist_dir": str(component.source.persist_dir),
                "source_collection": component.source.collection,
                "source_version": component.source.version,
                "target_collection": component.target_collection,
                "source_count": source_count,
                "copied_count": copied_count,
                "copied_ids_sha256": copied_ids_sha256,
            }
        )

    manifest = {
        "aggregate_name": spec.aggregate.name,
        "aggregate_version": spec.aggregate.version,
        "aggregate_description": spec.aggregate.description,
        "output_persist_dir": str(spec.output.persist_dir),
        "created_utc": created_utc,
        "git_sha": git_sha,
        "script_version": SCRIPT_VERSION,
        "components": component_payloads,
        "total_copied_count": total_copied_count,
        "status": status if not errors else "partial_success",
        "errors": errors,
    }
    _write_manifest(spec.output.manifest_out, manifest)
    return manifest
