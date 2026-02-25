from __future__ import annotations

import json
from pathlib import Path

import chromadb
import pytest

from athos.utils.chroma_aggregate import AggregateSpecError, build_aggregate, load_aggregate_spec


def _write_spec(
    path: Path,
    source_a_dir: Path,
    source_b_dir: Path,
    output_dir: Path,
    manifest_path: Path,
    *,
    missing_second_collection: bool = False,
) -> None:
    second_collection = "missing_collection" if missing_second_collection else "source_b"
    path.write_text(
        f"""
aggregate:
  name: test_bundle
  version: "20260225"
output:
  persist_dir: {output_dir}
  manifest_out: {manifest_path}
  overwrite: false
components:
  - logical_name: alpha_docs
    source:
      persist_dir: {source_a_dir}
      collection: source_a
      version: "20260220"
    target_collection: alpha
  - logical_name: beta_docs
    source:
      persist_dir: {source_b_dir}
      collection: {second_collection}
      version: "20260221"
    target_collection: beta
validation:
  require_unique_target_collections: true
  fail_on_missing_collection: true
  fail_on_doc_count_zero: true
  batch_size: 2
""".strip()
    )


def test_build_aggregate_copies_collections_and_writes_manifest(tmp_path: Path):
    source_a_dir = tmp_path / "source_a_db"
    source_b_dir = tmp_path / "source_b_db"
    output_dir = tmp_path / "aggregate_db"
    manifest_path = tmp_path / "aggregate_manifest.json"
    spec_path = tmp_path / "aggregate_spec.yaml"

    source_a_client = chromadb.PersistentClient(path=str(source_a_dir))
    source_a = source_a_client.get_or_create_collection("source_a")
    source_a.add(
        ids=["a1", "a2"],
        documents=["alpha doc one", "alpha doc two"],
        metadatas=[{"owner": "docs"}, {"owner": "docs"}],
        embeddings=[[0.1, 0.2], [0.2, 0.3]],
    )

    source_b_client = chromadb.PersistentClient(path=str(source_b_dir))
    source_b = source_b_client.get_or_create_collection("source_b")
    source_b.add(
        ids=["b1"],
        documents=["beta doc one"],
        metadatas=[{"owner": "tickets"}],
        embeddings=[[0.9, 0.1]],
    )

    _write_spec(spec_path, source_a_dir, source_b_dir, output_dir, manifest_path)
    spec = load_aggregate_spec(spec_path)
    manifest = build_aggregate(spec)

    assert manifest["status"] == "success"
    assert manifest["total_copied_count"] == 3
    assert manifest_path.exists()

    loaded_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert loaded_manifest["aggregate_name"] == "test_bundle"
    assert len(loaded_manifest["components"]) == 2

    output_client = chromadb.PersistentClient(path=str(output_dir))
    names = {collection.name for collection in output_client.list_collections()}
    assert names == {"alpha", "beta"}
    assert output_client.get_collection("alpha").count() == 2
    assert output_client.get_collection("beta").count() == 1

    alpha_docs = output_client.get_collection("alpha").get(include=["documents", "metadatas"])
    assert set(alpha_docs["ids"]) == {"a1", "a2"}
    assert alpha_docs["metadatas"][0]["owner"] == "docs"


def test_build_aggregate_fails_fast_on_missing_collection(tmp_path: Path):
    source_a_dir = tmp_path / "source_a_db"
    source_b_dir = tmp_path / "source_b_db"
    output_dir = tmp_path / "aggregate_db"
    manifest_path = tmp_path / "aggregate_manifest.json"
    spec_path = tmp_path / "aggregate_spec.yaml"

    source_a_client = chromadb.PersistentClient(path=str(source_a_dir))
    source_a = source_a_client.get_or_create_collection("source_a")
    source_a.add(
        ids=["a1"],
        documents=["alpha doc one"],
        metadatas=[{"owner": "docs"}],
        embeddings=[[0.1, 0.2]],
    )

    chromadb.PersistentClient(path=str(source_b_dir))
    _write_spec(
        spec_path,
        source_a_dir,
        source_b_dir,
        output_dir,
        manifest_path,
        missing_second_collection=True,
    )
    spec = load_aggregate_spec(spec_path)

    with pytest.raises(AggregateSpecError, match="Missing source collection"):
        build_aggregate(spec)
