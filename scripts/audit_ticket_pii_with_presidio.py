#!/usr/bin/env python3
"""Audit ticket JSON for residual PII using Presidio."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import tempfile
from typing import Any, Iterable, Iterator


DEFAULT_ENTITIES = (
    "EMAIL_ADDRESS",
    "PERSON",
    "PHONE_NUMBER",
    "URL",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "source_path",
        help="Ticket JSON file or directory to audit",
    )
    parser.add_argument(
        "--report-out",
        help="Write full JSON report to this path",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Maximum number of JSON files to audit",
    )
    parser.add_argument(
        "--entity",
        action="append",
        default=None,
        help="Presidio entity type to include (repeatable). Defaults to a small residual-PII set.",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=0.35,
        help="Minimum Presidio confidence score to keep",
    )
    parser.add_argument(
        "--sample-text-chars",
        type=int,
        default=160,
        help="Maximum number of characters to keep for each finding snippet",
    )
    parser.add_argument(
        "--max-findings",
        type=int,
        default=200,
        help="Maximum findings to retain in the JSON report",
    )
    parser.add_argument(
        "--fail-on-findings",
        action="store_true",
        help="Exit non-zero if any matching findings are detected",
    )
    return parser.parse_args()


def iter_ticket_json_files(source_path: Path) -> Iterable[Path]:
    if source_path.is_file():
        return [source_path]
    return sorted(source_path.rglob("*.json"))


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object at {path}, got {type(payload).__name__}")
    return payload


def iter_string_fields(value: Any, *, path: str = "$") -> Iterator[tuple[str, str]]:
    if isinstance(value, dict):
        for key, item in value.items():
            child_path = f"{path}.{key}"
            yield from iter_string_fields(item, path=child_path)
    elif isinstance(value, list):
        for idx, item in enumerate(value):
            child_path = f"{path}[{idx}]"
            yield from iter_string_fields(item, path=child_path)
    elif isinstance(value, str):
        stripped = value.strip()
        if stripped:
            yield path, stripped


def build_analyzer():
    # Keep tldextract from attempting to populate ~/.cache in restricted environments.
    os.environ.setdefault(
        "TLDEXTRACT_CACHE",
        tempfile.mkdtemp(prefix="athos-tldextract-cache-"),
    )

    try:
        from presidio_analyzer import AnalyzerEngine
        from presidio_analyzer.nlp_engine import NlpEngineProvider
    except ImportError as exc:  # pragma: no cover - environment-dependent
        raise SystemExit(
            "Presidio dependencies are not installed. Install with `pip install -e .[presidio]` "
            "and make sure `en_core_web_sm` is available in that environment."
        ) from exc

    configuration = {
        "nlp_engine_name": "spacy",
        "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
    }
    provider = NlpEngineProvider(nlp_configuration=configuration)
    try:
        nlp_engine = provider.create_engine()
    except OSError as exc:  # pragma: no cover - environment-dependent
        raise SystemExit(
            "spaCy model `en_core_web_sm` is not installed in this environment. "
            "Install it with `python -m spacy download en_core_web_sm`."
        ) from exc
    return AnalyzerEngine(nlp_engine=nlp_engine)


def _snippet(text: str, start: int, end: int, *, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    half = max(20, max_chars // 2)
    left = max(0, start - half)
    right = min(len(text), end + half)
    snippet = text[left:right]
    if left > 0:
        snippet = "..." + snippet
    if right < len(text):
        snippet = snippet + "..."
    return snippet


def main() -> None:
    args = parse_args()
    source_path = Path(args.source_path).resolve()
    if not source_path.exists():
        raise FileNotFoundError(f"Source path not found: {source_path}")

    entities = tuple(args.entity) if args.entity else DEFAULT_ENTITIES
    analyzer = build_analyzer()

    ticket_files = list(iter_ticket_json_files(source_path))
    if args.limit is not None:
        ticket_files = ticket_files[: args.limit]

    aggregate_counts: Counter[str] = Counter()
    per_file_counts: dict[str, dict[str, int]] = {}
    findings: list[dict[str, Any]] = []
    error_count = 0

    for ticket_file in ticket_files:
        try:
            payload = load_json(ticket_file)
            file_counter: Counter[str] = Counter()
            for field_path, text in iter_string_fields(payload):
                results = analyzer.analyze(
                    text=text,
                    language="en",
                    entities=list(entities),
                    score_threshold=args.min_score,
                )
                for result in results:
                    file_counter[result.entity_type] += 1
                    aggregate_counts[result.entity_type] += 1
                    if len(findings) < args.max_findings:
                        findings.append(
                            {
                                "file": str(ticket_file),
                                "field_path": field_path,
                                "entity_type": result.entity_type,
                                "score": result.score,
                                "start": result.start,
                                "end": result.end,
                                "text": text[result.start : result.end],
                                "snippet": _snippet(
                                    text,
                                    result.start,
                                    result.end,
                                    max_chars=args.sample_text_chars,
                                ),
                            }
                        )
            if file_counter:
                per_file_counts[str(ticket_file)] = dict(sorted(file_counter.items()))
        except Exception:  # pragma: no cover - CLI/runtime path
            error_count += 1

    report = {
        "run_timestamp_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source_path": str(source_path),
        "entities": list(entities),
        "min_score": args.min_score,
        "counts": {
            "input_files": len(ticket_files),
            "files_with_findings": len(per_file_counts),
            "findings_total": int(sum(aggregate_counts.values())),
            "errors": error_count,
        },
        "counts_by_entity": dict(sorted(aggregate_counts.items())),
        "per_file_counts": per_file_counts,
        "findings": findings,
    }

    if args.report_out:
        report_path = Path(args.report_out).resolve()
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with report_path.open("w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2, sort_keys=True)
            handle.write("\n")

    print(
        f"files={len(ticket_files)} "
        f"files_with_findings={len(per_file_counts)} "
        f"findings_total={sum(aggregate_counts.values())} "
        f"errors={error_count}"
    )
    if aggregate_counts:
        print(f"counts_by_entity={json.dumps(dict(sorted(aggregate_counts.items())), sort_keys=True)}")
    if args.report_out:
        print(f"report={Path(args.report_out).resolve()}")

    if args.fail_on_findings and aggregate_counts:
        raise SystemExit(1)
    if error_count:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
