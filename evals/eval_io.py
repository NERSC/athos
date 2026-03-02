"""I/O helpers for evaluation datasets."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


def load_test_cases(cases_dir: Path) -> List[Dict[str, Any]]:
    tests: List[Dict[str, Any]] = []
    for case_dir in sorted(cases_dir.iterdir()):
        if not case_dir.is_dir():
            continue
        desc_file = case_dir / "user_description.txt"
        sol_file = case_dir / "solution.md"
        files_dir = case_dir / "files"
        if not desc_file.exists() or not sol_file.exists():
            continue
        description = desc_file.read_text()
        solution = sol_file.read_text()
        tests.append(
            {
                "name": case_dir.name,
                "description": description,
                "solution": solution,
                "files_dir": files_dir if files_dir.exists() else None,
            }
        )
    return tests


def load_qa_cases(path: Path) -> List[Dict[str, Any]]:
    """Load question/answer cases from a JSON Lines file."""
    cases: List[Dict[str, Any]] = []
    seen_ids: set[str] = set()
    total = 0
    valid = 0
    rejected = 0

    def _raise(msg: str) -> None:
        raise ValueError(
            f"{path}: {msg} (summary before failure: total={total}, valid={valid}, rejected={rejected + 1})"
        )

    with path.open() as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            total += 1
            try:
                data = json.loads(line)
            except json.JSONDecodeError as exc:
                _raise(f"invalid JSON on line {line_num}: {exc.msg}")

            question = data.get("question")
            answer = data.get("answer")
            if not isinstance(question, str) or not question.strip():
                _raise(f"missing/empty string field 'question' on line {line_num}")
            if not isinstance(answer, str) or not answer.strip():
                _raise(f"missing/empty string field 'answer' on line {line_num}")

            raw_id = data.get("id") or data.get("name") or data.get("qa_id")
            if isinstance(raw_id, str):
                case_id = raw_id.strip()
            elif raw_id is not None:
                case_id = str(raw_id)
            else:
                digest = hashlib.sha1(
                    f"{question}\n{answer}\n{line_num}".encode("utf-8")
                ).hexdigest()[:12]
                case_id = f"auto_{digest}"
            if not case_id:
                _raise(f"missing/empty case id on line {line_num}")
            if case_id in seen_ids:
                _raise(f"duplicate case id '{case_id}' on line {line_num}")
            seen_ids.add(case_id)

            metadata = {
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
            if isinstance(data.get("metadata"), dict):
                metadata = {**data["metadata"], **metadata}

            cases.append(
                {
                    "id": case_id,
                    "name": case_id,
                    "description": question,
                    "solution": answer,
                    "metadata": metadata,
                }
            )
            valid += 1
    print(f"Loaded QA dataset {path}: total={total}, valid={valid}, rejected={rejected}")
    return cases


def build_input(description: str, files_dir: Optional[Path]) -> str:
    input_data = description.strip()
    if files_dir:
        blocks = []
        for f in sorted(files_dir.rglob("*")):
            if not f.is_file():
                continue
            rel = f.relative_to(files_dir.parent)
            content = f.read_text()
            blocks.append(f"### {rel}\n```\n{content}\n```")
        if blocks:
            input_data += "\n\nAttached files:\n" + "\n\n".join(blocks)
    return input_data
