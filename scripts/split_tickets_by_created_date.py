#!/usr/bin/env python3
"""Split a selected ticket corpus manifest into candidate/retrieval date slices."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import date, datetime, timezone
import json
import logging
from pathlib import Path
import shutil
from typing import Any, Iterable, Mapping
import unicodedata

from athos.utils.ticket_ingest import (
    compute_corpus_fingerprint,
    load_ticket_json,
    write_manifest,
)


logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Split selected ticket corpus by sys_created_on cutoff into candidate/retrieval outputs"
    )
    parser.add_argument(
        "--selected-corpus-manifest",
        required=True,
        help="Path to existing selected corpus manifest JSON",
    )
    parser.add_argument(
        "--cutoff-date",
        required=True,
        help="Cutoff date YYYY-MM-DD; candidate is >= cutoff, retrieval is < cutoff",
    )
    parser.add_argument(
        "--candidate-output-root",
        required=True,
        help="Destination root for candidate split copy",
    )
    parser.add_argument(
        "--retrieval-output-root",
        required=True,
        help="Destination root for retrieval split copy",
    )
    parser.add_argument(
        "--candidate-manifest-out",
        help="Path to candidate split manifest JSON (default: <candidate-output-root>/split_manifest.json)",
    )
    parser.add_argument(
        "--retrieval-manifest-out",
        help="Path to retrieval split manifest JSON (default: <retrieval-output-root>/split_manifest.json)",
    )
    parser.add_argument(
        "--split-report-out",
        help="Optional path for aggregate split report JSON",
    )
    parser.add_argument(
        "--allow-file-errors",
        action="store_true",
        help="Exit successfully even when some ticket files fail to parse/process",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Evaluate and write manifests only; do not copy files",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase output verbosity",
    )
    return parser.parse_args()


def configure_logging(verbosity: int) -> None:
    level = logging.WARNING
    if verbosity >= 2:
        level = logging.DEBUG
    elif verbosity == 1:
        level = logging.INFO
    logging.basicConfig(level=level)


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, Mapping):
        stable = value.get("value")
        if isinstance(stable, str) and stable.strip():
            return stable.strip()
        display = value.get("display_value")
        if isinstance(display, str) and display.strip():
            return display.strip()
    return ""


def _parse_date(value: str) -> date | None:
    if not value:
        return None
    raw = value.strip()
    if not raw:
        return None
    if len(raw) >= 10:
        try:
            return datetime.strptime(raw[:10], "%Y-%m-%d").date()
        except ValueError:
            pass
    try:
        return datetime.fromisoformat(raw).date()
    except ValueError:
        return None


def _extract_created_date(record: Mapping[str, Any]) -> date | None:
    metadata = record.get("metadata")
    incident_fields = record.get("incident_fields")
    meta = metadata if isinstance(metadata, Mapping) else {}
    fields = incident_fields if isinstance(incident_fields, Mapping) else {}
    raw = (
        _stringify(fields.get("sys_created_on"))
        or _stringify(meta.get("sys_created_on"))
        or _stringify(fields.get("created_on"))
        or _stringify(meta.get("created_on"))
    )
    return _parse_date(raw)


def _extract_incident_number(record: Mapping[str, Any], default: str) -> str:
    metadata = record.get("metadata")
    incident_fields = record.get("incident_fields")
    meta = metadata if isinstance(metadata, Mapping) else {}
    fields = incident_fields if isinstance(incident_fields, Mapping) else {}
    return (
        _stringify(meta.get("incident_number"))
        or _stringify(fields.get("number"))
        or default
    )


def _extract_attachment_local_paths(record: Mapping[str, Any]) -> list[str]:
    attachments = record.get("attachments")
    if not isinstance(attachments, list):
        return []
    local_paths: list[str] = []
    for entry in attachments:
        if not isinstance(entry, Mapping):
            continue
        local_path = _stringify(entry.get("local_path"))
        if local_path:
            local_paths.append(local_path)
    return local_paths


def _iter_attachment_dir_candidates(ticket_file: Path) -> Iterable[Path]:
    expected_prefix = f"{ticket_file.stem}_"
    for child in sorted(ticket_file.parent.iterdir()):
        if not child.is_dir():
            continue
        name_lower = child.name.lower()
        if name_lower.endswith("_attachements") or name_lower.endswith("_attachments"):
            if child.name.startswith(expected_prefix):
                yield child


def _resolve_attachment_candidate(
    local_path: str,
    *,
    source_root: Path,
) -> Path | None:
    source_root_resolved = source_root.resolve()

    def _resolve_if_allowed(candidate: Path) -> Path | None:
        resolved = candidate.resolve()
        if not resolved.exists():
            return None
        try:
            resolved.relative_to(source_root_resolved)
        except ValueError:
            return None
        return resolved

    def _normalized_variants(candidate: Path) -> list[Path]:
        text = str(candidate)
        variants: list[Path] = []
        seen: set[str] = set()
        for form in ("NFC", "NFD"):
            normalized = unicodedata.normalize(form, text)
            if normalized not in seen:
                seen.add(normalized)
                variants.append(Path(normalized))
        return variants

    def _resolve_via_normalized_filename(candidate: Path) -> Path | None:
        parent = candidate.parent
        if not parent.exists() or not parent.is_dir():
            return None
        target_name_nfc = unicodedata.normalize("NFC", candidate.name)
        target_name_nfd = unicodedata.normalize("NFD", candidate.name)
        for child in parent.iterdir():
            child_name_nfc = unicodedata.normalize("NFC", child.name)
            child_name_nfd = unicodedata.normalize("NFD", child.name)
            if child_name_nfc == target_name_nfc or child_name_nfd == target_name_nfd:
                return _resolve_if_allowed(child)
        return None

    candidate = Path(local_path)
    if candidate.is_absolute():
        return None

    raw_candidates = [source_root / candidate]
    parts = list(candidate.parts)
    if parts and parts[0] == source_root.name:
        raw_candidates.append(source_root / Path(*parts[1:]))

    for raw_candidate in raw_candidates:
        joined = _resolve_if_allowed(raw_candidate)
        if joined is not None:
            return joined
        for normalized_candidate in _normalized_variants(raw_candidate):
            resolved = _resolve_if_allowed(normalized_candidate)
            if resolved is not None:
                return resolved
        filename_match = _resolve_via_normalized_filename(raw_candidate)
        if filename_match is not None:
            return filename_match
    return None


def _copy_file(src: Path, dst: Path, *, dry_run: bool) -> None:
    if dry_run:
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def _load_selected_manifest(path: Path) -> tuple[dict[str, Any], Path, list[Path]]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object at {path}")

    source_path = payload.get("source_path")
    selected_files = payload.get("selected_files")
    config = payload.get("config")
    if not isinstance(source_path, str) or not source_path.strip():
        raise ValueError(f"Manifest missing string source_path: {path}")
    if not isinstance(selected_files, list):
        raise ValueError(f"Manifest missing selected_files list: {path}")
    if isinstance(config, dict) and config.get("materialized") is False:
        raise ValueError(
            "Input selected corpus manifest indicates dry-run/non-materialized output"
        )

    source_root = Path(source_path).resolve()
    ticket_files: list[Path] = []
    for item in selected_files:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"Manifest selected_files entries must be non-empty strings: {path}")
        candidate = (source_root / Path(item)).resolve()
        try:
            candidate.relative_to(source_root)
        except ValueError as exc:
            raise ValueError(f"selected_files entry escapes source_path: {item}") from exc
        if not candidate.exists():
            raise FileNotFoundError(f"Manifest-selected file does not exist: {candidate}")
        ticket_files.append(candidate)
    return payload, source_root, ticket_files


def _build_split_manifest(
    *,
    base_manifest_path: Path,
    base_manifest: Mapping[str, Any],
    source_root: Path,
    output_root: Path,
    output_ticket_files: list[Path],
    config: Mapping[str, Any],
    counts: Mapping[str, Any],
    dry_run: bool,
) -> dict[str, Any]:
    if dry_run:
        fingerprint = compute_corpus_fingerprint(source_root, output_ticket_files)
    else:
        materialized = [output_root / p.relative_to(source_root) for p in output_ticket_files]
        fingerprint = compute_corpus_fingerprint(output_root, materialized)

    selected_rel_paths = [str(path.relative_to(source_root)) for path in output_ticket_files]
    parent_fingerprint = base_manifest.get("corpus_fingerprint")
    return {
        "schema_version": "athos.ticket_split_manifest.v1",
        "run_timestamp_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source_path": str(output_root),
        "upstream_source_path": str(source_root),
        "parent_manifest": {
            "path": str(base_manifest_path.resolve()),
            "schema_version": base_manifest.get("schema_version"),
            "corpus_fingerprint": parent_fingerprint if isinstance(parent_fingerprint, Mapping) else None,
        },
        "config": dict(config),
        "counts": dict(counts),
        "corpus_fingerprint": {
            "file_count": fingerprint.file_count,
            "sha256": fingerprint.sha256,
        },
        "selected_files": selected_rel_paths,
    }


def main() -> None:
    args = parse_args()
    configure_logging(args.verbose)

    cutoff_date = datetime.strptime(args.cutoff_date, "%Y-%m-%d").date()
    base_manifest_path = Path(args.selected_corpus_manifest).resolve()
    base_manifest, source_root, ticket_files = _load_selected_manifest(base_manifest_path)

    candidate_output_root = Path(args.candidate_output_root).resolve()
    retrieval_output_root = Path(args.retrieval_output_root).resolve()
    candidate_manifest_out = (
        Path(args.candidate_manifest_out).resolve()
        if args.candidate_manifest_out
        else candidate_output_root / "split_manifest.json"
    )
    retrieval_manifest_out = (
        Path(args.retrieval_manifest_out).resolve()
        if args.retrieval_manifest_out
        else retrieval_output_root / "split_manifest.json"
    )
    split_report_out = Path(args.split_report_out).resolve() if args.split_report_out else None

    if not args.dry_run:
        candidate_output_root.mkdir(parents=True, exist_ok=True)
        retrieval_output_root.mkdir(parents=True, exist_ok=True)

    candidate_files: list[Path] = []
    retrieval_files: list[Path] = []
    candidate_incidents: set[str] = set()
    retrieval_incidents: set[str] = set()

    candidate_copied: set[Path] = set()
    retrieval_copied: set[Path] = set()
    candidate_attachments_copied = 0
    retrieval_attachments_copied = 0
    attachment_refs_total = 0
    attachment_unresolved_local_paths = 0
    reason_counts: Counter[str] = Counter()
    error_count = 0

    for ticket_file in ticket_files:
        try:
            payload = load_ticket_json(ticket_file)
            created_date = _extract_created_date(payload)
            if created_date is None:
                reason_counts["missing_or_invalid_created_date"] += 1
                continue

            incident = _extract_incident_number(payload, default=str(ticket_file.relative_to(source_root)))
            incident_rel = ticket_file.relative_to(source_root)

            is_candidate = created_date >= cutoff_date
            if is_candidate:
                output_root = candidate_output_root
                bucket_files = candidate_files
                bucket_incidents = candidate_incidents
                copied_set = candidate_copied
            else:
                output_root = retrieval_output_root
                bucket_files = retrieval_files
                bucket_incidents = retrieval_incidents
                copied_set = retrieval_copied

            bucket_files.append(ticket_file)
            bucket_incidents.add(incident)

            ticket_dst = output_root / incident_rel
            if ticket_dst not in copied_set:
                _copy_file(ticket_file, ticket_dst, dry_run=args.dry_run)
                copied_set.add(ticket_dst)

            attachment_sources: set[Path] = set()
            for local_path in _extract_attachment_local_paths(payload):
                attachment_refs_total += 1
                resolved = _resolve_attachment_candidate(local_path, source_root=source_root)
                if resolved is None or not resolved.is_file():
                    attachment_unresolved_local_paths += 1
                    logger.debug("Unresolved attachment local_path=%s for %s", local_path, ticket_file)
                    continue
                attachment_sources.add(resolved)

            for attachment_dir in _iter_attachment_dir_candidates(ticket_file):
                for file_path in sorted(attachment_dir.rglob("*")):
                    if not file_path.is_file():
                        continue
                    resolved_path = file_path.resolve()
                    try:
                        resolved_path.relative_to(source_root)
                    except ValueError:
                        logger.warning(
                            "Skipping out-of-root attachment discovered under %s: %s",
                            attachment_dir,
                            file_path,
                        )
                        continue
                    attachment_sources.add(resolved_path)

            for attachment_src in sorted(attachment_sources):
                attachment_rel = attachment_src.relative_to(source_root)
                attachment_dst = output_root / attachment_rel
                if attachment_dst in copied_set:
                    continue
                _copy_file(attachment_src, attachment_dst, dry_run=args.dry_run)
                copied_set.add(attachment_dst)
                if is_candidate:
                    candidate_attachments_copied += 1
                else:
                    retrieval_attachments_copied += 1
        except Exception:
            error_count += 1
            logger.exception("Failed to process %s", ticket_file)

    overlap = candidate_incidents.intersection(retrieval_incidents)
    if overlap:
        raise RuntimeError(f"Candidate/retrieval incident overlap detected: count={len(overlap)}")

    processed = len(candidate_files) + len(retrieval_files) + reason_counts["missing_or_invalid_created_date"] + error_count
    if processed != len(ticket_files):
        raise RuntimeError(
            f"Split accounting mismatch: processed={processed} input={len(ticket_files)}"
        )

    common_config = {
        "input_mode": "split_by_created_date",
        "cutoff_date": cutoff_date.isoformat(),
        "candidate_rule": "sys_created_on >= cutoff_date",
        "retrieval_rule": "sys_created_on < cutoff_date",
        "dry_run": args.dry_run,
        "materialized": not args.dry_run,
    }

    candidate_counts = {
        "input_files": len(ticket_files),
        "selected_files": len(candidate_files),
        "excluded": len(retrieval_files) + reason_counts["missing_or_invalid_created_date"],
        "excluded_by_reason": {
            "before_cutoff": len(retrieval_files),
            "missing_or_invalid_created_date": reason_counts["missing_or_invalid_created_date"],
        },
        "errors": error_count,
        "attachment_references": attachment_refs_total,
        "attachments_copied": candidate_attachments_copied,
        "unresolved_attachment_local_paths": attachment_unresolved_local_paths,
    }
    retrieval_counts = {
        "input_files": len(ticket_files),
        "selected_files": len(retrieval_files),
        "excluded": len(candidate_files) + reason_counts["missing_or_invalid_created_date"],
        "excluded_by_reason": {
            "on_or_after_cutoff": len(candidate_files),
            "missing_or_invalid_created_date": reason_counts["missing_or_invalid_created_date"],
        },
        "errors": error_count,
        "attachment_references": attachment_refs_total,
        "attachments_copied": retrieval_attachments_copied,
        "unresolved_attachment_local_paths": attachment_unresolved_local_paths,
    }

    candidate_manifest = _build_split_manifest(
        base_manifest_path=base_manifest_path,
        base_manifest=base_manifest,
        source_root=source_root,
        output_root=candidate_output_root,
        output_ticket_files=candidate_files,
        config={**common_config, "split": "candidate"},
        counts=candidate_counts,
        dry_run=args.dry_run,
    )
    retrieval_manifest = _build_split_manifest(
        base_manifest_path=base_manifest_path,
        base_manifest=base_manifest,
        source_root=source_root,
        output_root=retrieval_output_root,
        output_ticket_files=retrieval_files,
        config={**common_config, "split": "retrieval"},
        counts=retrieval_counts,
        dry_run=args.dry_run,
    )

    write_manifest(candidate_manifest_out, candidate_manifest)
    write_manifest(retrieval_manifest_out, retrieval_manifest)

    report = {
        "schema_version": "athos.ticket_split_report.v1",
        "run_timestamp_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "parent_manifest": str(base_manifest_path),
        "cutoff_date": cutoff_date.isoformat(),
        "counts": {
            "input_files": len(ticket_files),
            "candidate_files": len(candidate_files),
            "retrieval_files": len(retrieval_files),
            "missing_or_invalid_created_date": reason_counts["missing_or_invalid_created_date"],
            "errors": error_count,
            "incident_overlap": len(overlap),
        },
        "outputs": {
            "candidate_output_root": str(candidate_output_root),
            "retrieval_output_root": str(retrieval_output_root),
            "candidate_manifest": str(candidate_manifest_out),
            "retrieval_manifest": str(retrieval_manifest_out),
        },
    }
    if split_report_out:
        write_manifest(split_report_out, report)

    print(
        "split_done "
        f"cutoff={cutoff_date.isoformat()} "
        f"candidate_files={len(candidate_files)} "
        f"retrieval_files={len(retrieval_files)} "
        f"missing_or_invalid_created_date={reason_counts['missing_or_invalid_created_date']} "
        f"errors={error_count}"
    )
    print(f"candidate_manifest={candidate_manifest_out}")
    print(f"retrieval_manifest={retrieval_manifest_out}")
    if split_report_out:
        print(f"split_report={split_report_out}")

    if error_count and not args.allow_file_errors:
        raise RuntimeError(
            f"Encountered {error_count} file processing errors; rerun with --allow-file-errors to continue"
        )


if __name__ == "__main__":
    main()
