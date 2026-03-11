"""Standalone repro for a Chroma collection-name tool failure.

This script runs one flow turn against the CUG Chroma GPT-OSS flow using a
ticket prompt known to trigger incorrect collection-name usage in some runs.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import uuid

from dotenv import load_dotenv

from athos import build_config
from athos.models.enums import ExecutionMode
from athos.runtime.runner import FlowRunner


DEFAULT_PROMPT = """I am rerunning old calculations on Perlmutter with a VASP executable saved in my home directory, and now it fails with:

/global/homes/.../vasp_std: error while loading shared libraries: libmkl_scalapack_lp64.so.2: cannot open shared object file: No such file or directory

Context:
- The same binary worked months ago.
- I only have the executable (no source) for this in-house build.
- This started after a software stack update.

What is the likely cause and what should I do?
"""


async def run_once(config_path: str, flow_name: str, prompt: str) -> None:
    cfg = build_config(config_path)
    runner = FlowRunner(cfg)
    session_id = f"repro-{flow_name}-{uuid.uuid4().hex[:8]}"

    try:
        result = await runner.execute(
            flow_name=flow_name,
            message=prompt,
            session_id=session_id,
            user_id="example",
            mode=ExecutionMode.SYNC,
            interface="example",
            metadata={"reset_agent_memory": True},
        )
    finally:
        await runner.cleanup()

    print(f"flow={flow_name}")
    print(f"success={result.success}")
    print(f"execution_time_s={result.execution_time:.3f}")

    if result.success and result.output:
        output_text = result.output.content or ""
        print("--- output_text ---")
        print(output_text)
        print("--- end output_text ---")
        lowered = output_text.lower()
        if "collection" in lowered and "does not exist" in lowered:
            print("detected_collection_lookup_failure=true")
    else:
        print(f"error={result.error}")


def main() -> None:
    # Match CLI behavior: load environment variables from .env for examples.
    load_dotenv()
    if not os.getenv("ATHOS_WORKSPACE"):
        raise RuntimeError(
            "ATHOS_WORKSPACE is not set. Export it or define it in .env before "
            "running this example."
        )

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config/paper/cug_m1.yaml")
    parser.add_argument("--flow", default="cug_lang_chroma_gptoss")
    parser.add_argument("--prompt", default=DEFAULT_PROMPT)
    args = parser.parse_args()

    print(f"config={args.config}")
    print(f"flow={args.flow}")
    print(f"prompt_len={len(args.prompt)}")
    asyncio.run(run_once(args.config, args.flow, args.prompt))


if __name__ == "__main__":
    main()
