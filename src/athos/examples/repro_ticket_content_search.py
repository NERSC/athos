"""Repro for ticket corpus content-search failure in the filesystem flow.

This script demonstrates that the filesystem flow cannot retrieve answers
from the ticket corpus when the answer requires searching file *content*
rather than file *names*.

Test prompt: a question about srun "step creation temporarily disabled,
retrying (Requested nodes are busy)" failures when running multiple
concurrent srun steps inside an sbatch script.
- The answer exists in 10 tickets under tickets/ (confirmed by grep).
- The answer does not exist anywhere in docs/ or consulting_docs/.
- search_files matches file names only, so the model cannot locate it.

Expected behavior WITHOUT a content-search tool:
  GraphRecursionError — the model loops searching for content it cannot find.

Expected behavior WITH a content-search tool:
  The model finds the relevant ticket(s), reads them, and answers correctly.
  Correct answer: add --overlap to srun invocations, or reduce concurrency /
  adjust resource requests to avoid node-busy throttling.

Usage:
  python src/athos/examples/repro_ticket_content_search.py
  python src/athos/examples/repro_ticket_content_search.py --flow cug_lang_filesystem_gptoss
  python src/athos/examples/repro_ticket_content_search.py --out /tmp/events.jsonl
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import uuid
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv

from athos.runtime.builder import build_config
from athos.runtime.runner import FlowRunner


PROMPT = (
    "Some of my srun steps fail with:\n"
    "  srun: Job <jobid> step creation temporarily disabled, retrying "
    "(Requested nodes are busy)\n"
    "This happens when I run multiple concurrent srun commands inside an "
    "sbatch script. What is the cause and how do I fix it?"
)

# What a correct answer must contain — checked after the run.
EXPECTED_KEYWORDS = ["overlap", "concurrent", "parallel", "node", "busy"]


def _emit(out_path: Path | None, payload: Dict[str, Any]) -> None:
    if out_path is None:
        return
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, default=str) + "\n")


def _check_answer(text: str) -> bool:
    """Return True if the answer contains the expected signal keywords."""
    lower = text.lower()
    return any(kw in lower for kw in EXPECTED_KEYWORDS)


async def run(
    *,
    config_path: str,
    flow_name: str,
    out_path: Path | None,
) -> None:
    cfg = build_config(config_path)
    runner = FlowRunner(cfg)

    session_id = f"repro-ticket-search-{uuid.uuid4().hex[:8]}"
    print(f"config : {config_path}")
    print(f"flow   : {flow_name}")
    print(f"session: {session_id}")
    print(f"prompt : {PROMPT[:80]}...")
    print()

    tool_calls: list[str] = []
    answer_chunks: list[str] = []
    error: str | None = None

    try:
        async for chunk in runner.stream(
            flow_name=flow_name,
            message=PROMPT,
            session_id=session_id,
            user_id="repro",
            interface="repro",
            metadata={
                "reset_agent_memory": True,
                "verbosity_level": 2,
                "debug_include_steps": True,
            },
        ):
            meta = chunk.metadata or {}
            content = chunk.content or ""
            event_type = meta.get("event_type")

            if event_type == "tool_call_start":
                msg = meta.get("status_message", "")
                tool_calls.append(msg)
                print(f"CALL  : {msg}")
            elif event_type == "tool_call_complete":
                result = str(meta.get("tool_result", ""))
                print(f"RESULT: {result[:120]!r}")
            elif meta.get("error"):
                error = content
                print(f"\nERROR : {content[:300]}")
            elif meta.get("chunk") and content:
                answer_chunks.append(content)
                sys.stdout.write(content)
                sys.stdout.flush()

            _emit(out_path, {"content": content, "metadata": meta})

    finally:
        await runner.cleanup()

    answer = "".join(answer_chunks)

    print("\n\n--- verdict ---")
    print(f"tool calls  : {len(tool_calls)}")
    if error:
        print(f"outcome     : FAIL ({error[:120]})")
    elif _check_answer(answer):
        print("outcome     : PASS — answer contains expected signal")
    else:
        print("outcome     : WRONG — ran without error but answer missing expected content")
        print(f"answer      : {answer[:300]}")


def main() -> None:
    load_dotenv()
    if not os.getenv("ATHOS_WORKSPACE"):
        raise RuntimeError(
            "ATHOS_WORKSPACE is not set. Export it or add it to .env."
        )

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config/paper/cug_m1.yaml")
    parser.add_argument("--flow", default="cug_lang_filesystem_gptoss")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    asyncio.run(run(config_path=args.config, flow_name=args.flow, out_path=args.out))


if __name__ == "__main__":
    main()
