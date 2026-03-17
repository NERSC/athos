#!/usr/bin/env python3
"""Build a derived retrieval corpus from selected ServiceNow tickets."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import subprocess
from typing import Any, Mapping

from openai import OpenAI

from athos.config import ConfigLoader
from athos.config.models import ModelConfig
from athos.utils.derived_ticket_corpus import (
    DEFAULT_ATTACHMENT_TEXT_EXTENSIONS,
    DerivedFieldLimits,
    build_repair_prompt,
    derived_ticket_materialized_relpath,
    build_transform_prompt,
    render_derived_ticket_markdown,
    extract_json_object,
    find_derived_payload_violations,
    normalize_derived_payload,
    render_ticket_transform_input,
)
from athos.utils.ticket_ingest import compute_corpus_fingerprint, load_ticket_json, write_manifest


logger = logging.getLogger(__name__)

SCHEMA_VERSION = "athos.derived_ticket_record.v2"
PROMPT_VERSION = "athos.derived_ticket_prompt.v1"


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Transform selected ServiceNow tickets into a derived JSONL corpus"
    )
    parser.add_argument(
        "--selected-corpus-manifest",
        required=True,
        help="Path to stage-1 filter manifest with selected_files + source_path",
    )
    parser.add_argument(
        "--config",
        default="config/config.yaml",
        help="ATHOS config file used to resolve model settings",
    )
    parser.add_argument(
        "--model",
        default="cborg_coder",
        help="Model config key to use for the transform step",
    )
    parser.add_argument(
        "--output-jsonl",
        required=True,
        help="Path to write derived ticket records as JSONL",
    )
    parser.add_argument(
        "--materialize-dir",
        help="Optional directory to write one Markdown file per derived ticket for filesystem search",
    )
    parser.add_argument(
        "--manifest-out",
        help="Path to write run manifest JSON (default: <output-jsonl>.manifest.json)",
    )
    parser.add_argument(
        "--failures-out",
        help="Path to write failed transforms as JSONL (default: <output-jsonl>.failures.jsonl)",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume a previous run by appending to existing outputs and skipping records already in output-jsonl",
    )
    parser.add_argument(
        "--limit",
        type=_positive_int,
        help="Limit the number of selected tickets processed",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=2,
        help="Retry budget after the first transform attempt",
    )
    parser.add_argument(
        "--max-comment-chars",
        type=int,
        default=8000,
        help="Maximum chars kept from customer comments, biased toward latest messages",
    )
    parser.add_argument(
        "--max-work-note-chars",
        type=int,
        default=8000,
        help="Maximum chars kept from work notes, biased toward latest notes",
    )
    parser.add_argument(
        "--attachment-text-ext",
        default=",".join(sorted(DEFAULT_ATTACHMENT_TEXT_EXTENSIONS)),
        help="Comma-separated allowlist for text-like attachment extensions",
    )
    parser.add_argument(
        "--max-attachments",
        type=_positive_int,
        default=3,
        help="Maximum number of attachments to render into prompt input",
    )
    parser.add_argument(
        "--max-attachment-chars",
        type=_positive_int,
        default=20000,
        help="Maximum decoded chars read per attachment before snippet selection",
    )
    parser.add_argument(
        "--max-total-attachment-context-chars",
        type=_positive_int,
        default=2000,
        help="Maximum total attachment chars inserted into the prompt input",
    )
    parser.add_argument(
        "--max-snippets-per-attachment",
        type=_positive_int,
        default=3,
        help="Maximum snippets selected per attachment when not using full text",
    )
    parser.add_argument(
        "--max-snippet-chars",
        type=_positive_int,
        default=300,
        help="Maximum chars per selected attachment snippet",
    )
    parser.add_argument(
        "--full-attachment-max-chars",
        type=_positive_int,
        default=2000,
        help="If attachment text fits within this threshold and line cap, include it whole",
    )
    parser.add_argument(
        "--full-attachment-max-lines",
        type=_positive_int,
        default=40,
        help="Maximum lines for whole-attachment inclusion",
    )
    parser.add_argument(
        "--incident-summary-chars",
        type=_positive_int,
        default=1200,
        help="Maximum chars allowed for incident_summary",
    )
    parser.add_argument(
        "--resolution-summary-chars",
        type=_positive_int,
        default=800,
        help="Maximum chars allowed for resolution_summary",
    )
    parser.add_argument(
        "--max-keywords",
        type=_positive_int,
        default=12,
        help="Maximum retrieval_keywords entries",
    )
    parser.add_argument(
        "--max-evidence-snippets",
        type=_positive_int,
        default=8,
        help="Maximum evidence_snippets entries",
    )
    parser.add_argument(
        "--allow-file-errors",
        action="store_true",
        help="Exit successfully even when some ticket files fail to process",
    )
    parser.add_argument(
        "--allow-transform-errors",
        action="store_true",
        help="Exit successfully even when some model transforms fail validation",
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


def _load_selected_corpus_manifest(path: Path) -> tuple[Path, list[Path], dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object manifest at {path}")

    source_path = payload.get("source_path")
    selected_files = payload.get("selected_files")
    config = payload.get("config")
    if not isinstance(source_path, str) or not source_path.strip():
        raise ValueError(f"Manifest missing string source_path: {path}")
    if not isinstance(selected_files, list):
        raise ValueError(f"Manifest missing selected_files list: {path}")
    if isinstance(config, dict) and config.get("materialized") is False:
        raise ValueError(
            "Selected corpus manifest indicates dry-run/non-materialized output; "
            "rerun filter stage without --dry-run before derived transform"
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
            raise ValueError(
                f"Manifest selected_files entry escapes source_path: {item}"
            ) from exc
        if not candidate.exists():
            raise FileNotFoundError(
                f"Manifest-selected ticket file does not exist under source_path: {candidate}"
            )
        ticket_files.append(candidate)
    return source_root, ticket_files, payload


def _parse_extension_allowlist(value: str) -> set[str]:
    return {item.strip().lower().lstrip(".") for item in value.split(",") if item.strip()}


def _build_openai_client(model_cfg: ModelConfig) -> OpenAI:
    kwargs: dict[str, Any] = {}
    if model_cfg.api_key:
        kwargs["api_key"] = model_cfg.api_key.get_secret_value()
    if model_cfg.api_base:
        kwargs["base_url"] = model_cfg.api_base
    return OpenAI(**kwargs)


def _invoke_model_json(
    client: OpenAI,
    *,
    model_cfg: ModelConfig,
    prompt: str,
) -> str:
    response = client.chat.completions.create(
        model=model_cfg.model_id,
        temperature=model_cfg.temperature,
        max_tokens=model_cfg.max_tokens,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": "You produce compact retrieval-oriented JSON only.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )
    message = response.choices[0].message
    if not message.content:
        raise ValueError("Model returned empty content")
    return message.content


def _build_limits(args: argparse.Namespace) -> DerivedFieldLimits:
    return DerivedFieldLimits(
        incident_summary_chars=args.incident_summary_chars,
        resolution_summary_chars=args.resolution_summary_chars,
        max_keywords=args.max_keywords,
        max_evidence_snippets=args.max_evidence_snippets,
    )


def _transform_ticket(
    *,
    client: OpenAI,
    model_cfg: ModelConfig,
    rendered_input: str,
    limits: DerivedFieldLimits,
    max_retries: int,
) -> tuple[dict[str, Any], int]:
    prompt = build_transform_prompt(rendered_input)
    attempts = 0
    current_prompt = prompt
    last_violations: list[str] = []

    while attempts <= max_retries:
        attempts += 1
        raw_response = _invoke_model_json(
            client,
            model_cfg=model_cfg,
            prompt=current_prompt,
        )
        try:
            payload = json.loads(extract_json_object(raw_response))
        except Exception as exc:
            last_violations = [f"invalid_json: {exc}"]
            if attempts > max_retries:
                raise ValueError("; ".join(last_violations)) from exc
            current_prompt = build_repair_prompt(rendered_input, raw_response, last_violations)
            continue

        normalized = normalize_derived_payload(payload)
        violations = find_derived_payload_violations(normalized, limits=limits)
        if not violations:
            return normalized, attempts
        last_violations = violations
        if attempts > max_retries:
            raise ValueError("; ".join(violations))
        current_prompt = build_repair_prompt(rendered_input, raw_response, violations)

    raise ValueError("; ".join(last_violations) if last_violations else "unknown transform failure")


def _append_jsonl(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True))
        handle.write("\n")


def _load_completed_incident_numbers(path: Path) -> set[str]:
    completed: set[str] = set()
    if not path.exists():
        return completed
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                payload = json.loads(stripped)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, Mapping):
                incident_number = payload.get("incident_number")
                if isinstance(incident_number, str) and incident_number.strip():
                    completed.add(incident_number.strip())
    return completed


def _write_materialized_ticket(root: Path, record: Mapping[str, Any]) -> Path:
    rel_path = derived_ticket_materialized_relpath(record)
    destination = root / rel_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(render_derived_ticket_markdown(record), encoding="utf-8")
    return destination


def main() -> None:
    args = parse_args()
    configure_logging(args.verbose)

    selected_manifest_path = Path(args.selected_corpus_manifest).resolve()
    source_root, ticket_files, selected_manifest = _load_selected_corpus_manifest(selected_manifest_path)
    if args.limit is not None:
        ticket_files = ticket_files[: args.limit]

    output_jsonl = Path(args.output_jsonl).resolve()
    manifest_out = (
        Path(args.manifest_out).resolve()
        if args.manifest_out
        else output_jsonl.with_suffix(output_jsonl.suffix + ".manifest.json")
    )
    failures_out = (
        Path(args.failures_out).resolve()
        if args.failures_out
        else output_jsonl.with_suffix(output_jsonl.suffix + ".failures.jsonl")
    )
    materialize_dir = Path(args.materialize_dir).resolve() if args.materialize_dir else None
    output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    failures_out.parent.mkdir(parents=True, exist_ok=True)
    if args.resume:
        completed_incident_numbers = _load_completed_incident_numbers(output_jsonl)
        if not output_jsonl.exists():
            output_jsonl.write_text("", encoding="utf-8")
        if not failures_out.exists():
            failures_out.write_text("", encoding="utf-8")
    else:
        completed_incident_numbers = set()
        output_jsonl.write_text("", encoding="utf-8")
        failures_out.write_text("", encoding="utf-8")
    materialized_records = 0
    if materialize_dir is not None:
        materialize_dir.mkdir(parents=True, exist_ok=True)

    athos_config = ConfigLoader.load_config(args.config)
    if args.model not in athos_config.models:
        raise ValueError(f"Unknown model config key: {args.model}")
    model_cfg = athos_config.models[args.model]
    client = _build_openai_client(model_cfg)
    limits = _build_limits(args)
    attachment_extensions = _parse_extension_allowlist(args.attachment_text_ext)

    successful_records = 0
    failed_records = 0
    transform_failures = 0
    file_errors = 0
    retry_count = 0
    resumed_skipped = 0
    attachment_rendered_total = 0
    attachment_considered_total = 0
    kept_ticket_files: list[Path] = []

    for ticket_file in ticket_files:
        try:
            payload = load_ticket_json(ticket_file)
            rendered_input = render_ticket_transform_input(
                payload,
                source_json_path=ticket_file,
                source_root=source_root,
                max_comment_chars=args.max_comment_chars,
                max_work_note_chars=args.max_work_note_chars,
                attachment_allowed_extensions=attachment_extensions,
                max_attachments=args.max_attachments,
                max_attachment_chars=args.max_attachment_chars,
                max_total_attachment_context_chars=args.max_total_attachment_context_chars,
                max_snippets_per_attachment=args.max_snippets_per_attachment,
                max_snippet_chars=args.max_snippet_chars,
                full_attachment_max_chars=args.full_attachment_max_chars,
                full_attachment_max_lines=args.full_attachment_max_lines,
            )
        except Exception as exc:  # pragma: no cover - script-level failure handling
            logger.exception("Failed to prepare ticket input for %s", ticket_file)
            _append_jsonl(
                failures_out,
                {
                    "ticket_path": str(ticket_file),
                    "stage": "prepare_input",
                    "error": str(exc),
                },
            )
            failed_records += 1
            file_errors += 1
            continue

        metadata = payload.get("metadata")
        incident_fields = payload.get("incident_fields")
        metadata = metadata if isinstance(metadata, dict) else {}
        incident_fields = incident_fields if isinstance(incident_fields, dict) else {}
        incident_number = metadata.get("incident_number") or incident_fields.get("number") or ticket_file.stem
        sys_id = metadata.get("sys_id", "")
        if incident_number in completed_incident_numbers:
            resumed_skipped += 1
            continue

        try:
            derived_payload, attempts = _transform_ticket(
                client=client,
                model_cfg=model_cfg,
                rendered_input=rendered_input.text,
                limits=limits,
                max_retries=args.max_retries,
            )
            retry_count += max(0, attempts - 1)

            record = {
                "schema_version": SCHEMA_VERSION,
                "incident_number": incident_number,
                "sys_id": sys_id,
                "sys_created_on": incident_fields.get("sys_created_on", ""),
                "state": incident_fields.get("state", ""),
                "close_code": incident_fields.get("close_code", ""),
                "category": incident_fields.get("category", ""),
                "subcategory": incident_fields.get("subcategory", ""),
                "assignment_group": incident_fields.get("assignment_group", ""),
                "source_json_path": str(ticket_file),
                "incident_summary": derived_payload["incident_summary"],
                "resolution_summary": derived_payload["resolution_summary"],
                "retrieval_keywords": derived_payload["retrieval_keywords"],
                "evidence_snippets": derived_payload["evidence_snippets"],
                "attachment_context": {
                    "attachments_considered": rendered_input.attachment_context.attachments_considered,
                    "attachments_rendered": rendered_input.attachment_context.attachments_rendered,
                    "rendered_attachments": rendered_input.attachment_context.attachment_summaries,
                },
                "provenance": {
                    "source_manifest_path": str(selected_manifest_path),
                    "source_manifest_schema_version": selected_manifest.get("schema_version"),
                    "transform_timestamp_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    "model_config_key": args.model,
                    "model_id": model_cfg.model_id,
                    "model_temperature": model_cfg.temperature,
                    "model_max_tokens": model_cfg.max_tokens,
                    "prompt_version": PROMPT_VERSION,
                    "prompt_sha256": rendered_input.prompt_sha256,
                    "validation_attempts": attempts,
                },
            }
            _append_jsonl(output_jsonl, record)
            if materialize_dir is not None:
                _write_materialized_ticket(materialize_dir, record)
                materialized_records += 1
            successful_records += 1
            completed_incident_numbers.add(str(incident_number))
            kept_ticket_files.append(ticket_file)
            attachment_considered_total += rendered_input.attachment_context.attachments_considered
            attachment_rendered_total += rendered_input.attachment_context.attachments_rendered
        except Exception as exc:  # pragma: no cover - script-level failure handling
            logger.exception("Failed to derive record for %s", ticket_file)
            _append_jsonl(
                failures_out,
                {
                    "ticket_path": str(ticket_file),
                    "stage": "transform",
                    "error": str(exc),
                },
            )
            failed_records += 1
            transform_failures += 1

    fingerprint = compute_corpus_fingerprint(source_root, ticket_files)
    manifest = {
        "schema_version": "athos.derived_ticket_manifest.v1",
        "run_timestamp_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source_path": str(source_root),
        "selected_corpus_manifest": str(selected_manifest_path),
        "output_jsonl": str(output_jsonl),
        "failures_out": str(failures_out),
        "materialize_dir": str(materialize_dir) if materialize_dir is not None else None,
        "git_sha": _get_git_sha(),
        "config": {
            "config_path": str(Path(args.config).resolve()),
            "model": args.model,
            "model_id": model_cfg.model_id,
            "max_retries": args.max_retries,
            "max_comment_chars": args.max_comment_chars,
            "max_work_note_chars": args.max_work_note_chars,
            "attachment_text_ext": sorted(attachment_extensions),
            "max_attachments": args.max_attachments,
            "max_attachment_chars": args.max_attachment_chars,
            "max_total_attachment_context_chars": args.max_total_attachment_context_chars,
            "max_snippets_per_attachment": args.max_snippets_per_attachment,
            "max_snippet_chars": args.max_snippet_chars,
            "full_attachment_max_chars": args.full_attachment_max_chars,
            "full_attachment_max_lines": args.full_attachment_max_lines,
            "field_limits": {
                "incident_summary_chars": limits.incident_summary_chars,
                "resolution_summary_chars": limits.resolution_summary_chars,
                "max_keywords": limits.max_keywords,
                "max_evidence_snippets": limits.max_evidence_snippets,
            },
            "prompt_version": PROMPT_VERSION,
            "limit": args.limit,
            "resume": args.resume,
        },
        "counts": {
            "input_files": len(ticket_files),
            "successful_records": successful_records,
            "failed_records": failed_records,
            "file_errors": file_errors,
            "transform_failures": transform_failures,
            "transform_retries": retry_count,
            "resumed_skipped": resumed_skipped,
            "attachments_considered": attachment_considered_total,
            "attachments_rendered": attachment_rendered_total,
            "materialized_records": materialized_records,
        },
        "corpus_fingerprint": {
            "file_count": fingerprint.file_count,
            "sha256": fingerprint.sha256,
        },
    }
    if materialize_dir is not None:
        index_lines = [
            "# Derived Ticket Corpus",
            "",
            "This directory contains one Markdown file per derived ServiceNow ticket record.",
            "",
            "## Usage",
            "",
            "- Use `search_files` with a narrow error string, software name, filesystem name, or incident number.",
            "- Prefer reading one matching ticket file rather than scanning broad directory trees.",
            "- The canonical batch artifact remains the sibling JSONL output referenced in `manifest.json`.",
            "",
            "## Layout",
            "",
            "- Files are sharded by incident number prefix to avoid one huge flat directory.",
            "- Each file contains metadata, incident summary, resolution summary, retrieval keywords, and evidence snippets.",
            "",
            "See `manifest.json` for provenance and the source JSONL path.",
            "",
        ]
        write_manifest(
            materialize_dir / "manifest.json",
            {
                "schema_version": "athos.derived_ticket_materialized_manifest.v1",
                "generated_from_jsonl": str(output_jsonl),
                "selected_corpus_manifest": str(selected_manifest_path),
                "materialize_dir": str(materialize_dir),
                "record_count": materialized_records,
                "git_sha": _get_git_sha(),
            },
        )
        (materialize_dir / "INDEX.md").write_text("\n".join(index_lines), encoding="utf-8")
    write_manifest(manifest_out, manifest)

    print(
        f"successful_records={successful_records} "
        f"failed_records={failed_records} "
        f"file_errors={file_errors} "
        f"transform_retries={retry_count} "
        f"resumed_skipped={resumed_skipped}"
    )
    print(f"manifest={manifest_out}")

    if file_errors and not args.allow_file_errors:
        raise RuntimeError(
            f"Encountered {file_errors} file processing errors; rerun with --allow-file-errors to continue"
        )
    if transform_failures and not args.allow_transform_errors:
        raise RuntimeError(
            "Encountered derived transform failures; rerun with --allow-transform-errors to continue"
        )


if __name__ == "__main__":
    main()
