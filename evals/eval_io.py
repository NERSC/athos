"""I/O helpers for evaluation datasets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


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
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            cases.append(
                {
                    "name": data.get("name"),
                    "description": data.get("question"),
                    "solution": data.get("answer"),
                }
            )
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
