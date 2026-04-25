#!/usr/bin/env python3
"""Render a reviewer-friendly markdown packet from the human audit worksheet."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


JUDGMENT_FILES = [
    REPO_ROOT / "results/cug_m2_canonical/judgments/llama_4_maverick_rubric_v1_cug_m2_canonical.jsonl",
    REPO_ROOT / "results/cug_m4/judgments/llama_4_maverick_rubric_v1.jsonl",
]


def load_qa_reference_map(path: Path) -> dict[str, dict]:
    refs: dict[str, dict] = {}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            case_id = row.get("id")
            if isinstance(case_id, str):
                refs[case_id] = row
    return refs


def load_judgments(paths: list[Path]) -> dict[str, dict]:
    by_run_path: dict[str, dict] = {}
    for path in paths:
        if not path.exists():
            continue
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                run_path = row.get("run_path")
                if not isinstance(run_path, str):
                    continue
                normalized = normalize_run_path(run_path)
                by_run_path[normalized] = row
    return by_run_path


def normalize_run_path(run_path: str) -> str:
    marker = "/results/"
    if marker in run_path:
        return "results/" + run_path.split(marker, 1)[1]
    if run_path.startswith("results/"):
        return run_path
    return run_path


def load_run_payload(run_path: Path) -> dict:
    with run_path.open(encoding="utf-8") as handle:
        return json.load(handle)


def load_ticket_reference(case_id: str) -> str:
    path = REPO_ROOT / "data/ticket_cases" / case_id / "solution.md"
    if not path.exists():
        return "_Reference solution not found in data/ticket_cases._"
    return path.read_text(encoding="utf-8").strip()


def qa_reference_markdown(case_id: str, qa_refs: dict[str, dict]) -> str:
    ref = qa_refs.get(case_id)
    if ref is None:
        return "_Reference answer not found in evals/nersc_qa.v2.jsonl._"
    parts = [
        f"Answer: {ref.get('answer', '')}".strip(),
        f"Source doc: {ref.get('source_doc', '')}".strip(),
        f"Section: {ref.get('section', '')}".strip(),
        f"Source passage: {ref.get('source_passage', '')}".strip(),
    ]
    return "\n\n".join(part for part in parts if part and not part.endswith(": "))


def build_packet(
    worksheet_path: Path,
    output_path: Path,
    qa_refs: dict[str, dict],
    judgments: dict[str, dict],
) -> None:
    rows = list(csv.DictReader(worksheet_path.open(encoding="utf-8")))

    out: list[str] = []
    out.append("# Human Audit Review Packet")
    out.append("")
    out.append("This packet is generated from the audit worksheet and is intended to let a reviewer inspect each sampled case without opening raw `run.json` files manually.")
    out.append("")
    out.append("Primary worksheet:")
    out.append(f"- `{worksheet_path.relative_to(REPO_ROOT)}`")
    out.append("")
    out.append(f"Total rows: {len(rows)}")
    out.append("")

    for idx, row in enumerate(rows, start=1):
        run_rel = row["run_path"]
        run_path = REPO_ROOT / run_rel
        payload = load_run_payload(run_path)
        judgment = judgments.get(run_rel, {})

        out.append(f"## {idx}. {row['config']} | {row['dataset']} | {row['stratum']} | {row['case_id']}")
        out.append("")
        out.append(f"- Judge score: `{row['judge_score']}`")
        out.append(f"- Judge pass: `{row['judge_pass']}`")
        out.append(f"- Judgment status: `{row['judgment_status']}`")
        out.append(f"- Run path: `{run_rel}`")
        out.append("")
        out.append("### User Prompt")
        out.append("")
        out.append("````text")
        out.append((payload.get("request", {}) or {}).get("input_text", "").strip())
        out.append("````")
        out.append("")
        out.append("### Model Answer")
        out.append("")
        out.append("````text")
        out.append((payload.get("response", {}) or {}).get("output_text", "").strip())
        out.append("````")
        out.append("")
        out.append("### Reference Answer")
        out.append("")
        if row["dataset"] == "qa":
            out.append(qa_reference_markdown(row["case_id"], qa_refs))
        else:
            out.append(load_ticket_reference(row["case_id"]))
        out.append("")
        out.append("### Automated Judgment")
        out.append("")
        out.append(f"- Status: `{judgment.get('judgment_status', row['judgment_status'])}`")
        out.append(f"- Score: `{judgment.get('score', row['judge_score'])}`")
        out.append(f"- Pass: `{judgment.get('pass', row['judge_pass'])}`")
        rationale = judgment.get("rationale", "")
        out.append("")
        out.append("Rationale:")
        out.append("")
        out.append("````text")
        out.append(str(rationale).strip())
        out.append("````")
        out.append("")
        out.append("---")
        out.append("")

    output_path.write_text("\n".join(out), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--worksheet",
        default="docs/cug_paper/human_audit_review_sheet.csv",
        help="Path to the audit worksheet CSV.",
    )
    parser.add_argument(
        "--output",
        default="docs/cug_paper/human_audit_review_packet.md",
        help="Path to the output markdown packet.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    worksheet_path = (REPO_ROOT / args.worksheet).resolve()
    output_path = (REPO_ROOT / args.output).resolve()
    qa_refs = load_qa_reference_map(REPO_ROOT / "evals/nersc_qa.v2.jsonl")
    judgments = load_judgments(JUDGMENT_FILES)
    build_packet(worksheet_path, output_path, qa_refs, judgments)
    print(f"Wrote review packet to {output_path}")


if __name__ == "__main__":
    main()
