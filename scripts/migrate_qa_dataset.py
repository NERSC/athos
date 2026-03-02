#!/usr/bin/env python3
"""Normalize QA JSONL datasets into eval schema v2."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def _coerce_case_id(data: dict[str, Any], line_num: int) -> str:
    raw_id = data.get("id") or data.get("name") or data.get("qa_id")
    if isinstance(raw_id, str):
        case_id = raw_id.strip()
    elif raw_id is not None:
        case_id = str(raw_id)
    else:
        question = data["question"]
        answer = data["answer"]
        digest = hashlib.sha1(
            f"{question}\n{answer}\n{line_num}".encode("utf-8")
        ).hexdigest()[:12]
        case_id = f"auto_{digest}"
    if not case_id:
        raise ValueError(f"line {line_num}: empty case id")
    return case_id


def migrate(input_path: Path, output_path: Path) -> None:
    total = 0
    valid = 0
    rejected = 0
    seen_ids: set[str] = set()

    with input_path.open("r", encoding="utf-8") as src, output_path.open(
        "w", encoding="utf-8"
    ) as dst:
        for line_num, line in enumerate(src, start=1):
            line = line.strip()
            if not line:
                continue
            total += 1

            try:
                data = json.loads(line)
            except json.JSONDecodeError as exc:
                rejected += 1
                raise ValueError(
                    f"{input_path}: invalid JSON on line {line_num}: {exc.msg}"
                ) from exc

            question = data.get("question")
            answer = data.get("answer")
            if not isinstance(question, str) or not question.strip():
                rejected += 1
                raise ValueError(
                    f"{input_path}: missing/empty 'question' on line {line_num}"
                )
            if not isinstance(answer, str) or not answer.strip():
                rejected += 1
                raise ValueError(
                    f"{input_path}: missing/empty 'answer' on line {line_num}"
                )

            case_id = _coerce_case_id(data, line_num)
            if case_id in seen_ids:
                rejected += 1
                raise ValueError(
                    f"{input_path}: duplicate case id '{case_id}' on line {line_num}"
                )
            seen_ids.add(case_id)

            output_record: dict[str, Any] = {
                "id": case_id,
                "question": question,
                "answer": answer,
            }
            for optional_key in (
                "difficulty",
                "source_doc",
                "section",
                "source_passage",
                "metadata",
            ):
                if optional_key in data:
                    output_record[optional_key] = data[optional_key]

            extra_fields = {
                key: value
                for key, value in data.items()
                if key
                not in {
                    "id",
                    "name",
                    "qa_id",
                    "question",
                    "answer",
                    "difficulty",
                    "source_doc",
                    "section",
                    "source_passage",
                    "metadata",
                }
            }
            if extra_fields:
                existing_metadata = output_record.get("metadata")
                if isinstance(existing_metadata, dict):
                    merged_metadata = dict(existing_metadata)
                    merged_metadata.update(extra_fields)
                    output_record["metadata"] = merged_metadata
                else:
                    output_record["metadata"] = extra_fields

            dst.write(json.dumps(output_record, ensure_ascii=True) + "\n")
            valid += 1

    print(
        f"Migrated dataset {input_path} -> {output_path}: total={total}, valid={valid}, rejected={rejected}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Input JSONL path")
    parser.add_argument(
        "--output", required=True, type=Path, help="Output canonical JSONL path"
    )
    args = parser.parse_args()
    migrate(args.input, args.output)


if __name__ == "__main__":
    main()
