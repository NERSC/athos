#!/usr/bin/env python3
"""Build a QA JSONL subset from an explicit case-id list."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--case-list",
        required=True,
        help="Text file containing one case_id/name per line.",
    )
    parser.add_argument(
        "--source-qa-file",
        required=True,
        help="Source QA JSONL file.",
    )
    parser.add_argument(
        "--output-qa-file",
        required=True,
        help="Destination QA JSONL subset path.",
    )
    return parser.parse_args()


def _load_case_ids(path: Path) -> list[str]:
    case_ids: list[str] = []
    seen: set[str] = set()
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line in seen:
            continue
        seen.add(line)
        case_ids.append(line)
    return case_ids


def main() -> None:
    args = parse_args()

    case_list_path = Path(args.case_list).resolve()
    source_qa_path = Path(args.source_qa_file).resolve()
    output_qa_path = Path(args.output_qa_file).resolve()

    if not case_list_path.is_file():
        raise FileNotFoundError(f"case list not found: {case_list_path}")
    if not source_qa_path.is_file():
        raise FileNotFoundError(f"source QA file not found: {source_qa_path}")

    requested_case_ids = _load_case_ids(case_list_path)
    if not requested_case_ids:
        raise ValueError(f"no case IDs found in {case_list_path}")
    requested = set(requested_case_ids)

    selected_rows: list[str] = []
    found: set[str] = set()
    for raw_line in source_qa_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        payload = json.loads(line)
        case_id = payload.get("id")
        name = payload.get("name")
        match_id = isinstance(case_id, str) and case_id in requested
        match_name = isinstance(name, str) and name in requested
        if match_id or match_name:
            selected_rows.append(json.dumps(payload))
            if match_id:
                found.add(case_id)
            if match_name:
                found.add(name)

    output_qa_path.parent.mkdir(parents=True, exist_ok=True)
    output_qa_path.write_text(
        ("\n".join(selected_rows) + "\n") if selected_rows else "",
        encoding="utf-8",
    )

    missing = [case_id for case_id in requested_case_ids if case_id not in found]
    print(f"case_ids_requested={len(requested_case_ids)}")
    print(f"matched_rows={len(selected_rows)}")
    print(f"missing_case_ids={len(missing)}")
    print(f"output_qa_file={output_qa_path}")
    if missing:
        print("missing_case_ids_list:")
        for case_id in missing:
            print(f"  {case_id}")


if __name__ == "__main__":
    main()
