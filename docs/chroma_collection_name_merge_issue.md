# Chroma Collection Name Merge Issue

## Summary

When running CUG Chroma flows, both `cug_lang_chroma_sonnet` and `cug_lang_chroma_gptoss` intermittently (and often consistently) call Chroma tools with an invalid merged collection name:

- `ticketsdocsconsulting_docs`

The actual DB has three separate collections:

- `tickets`
- `docs`
- `consulting_docs`

This is not a Chroma DB storage issue. The bad value is produced in the model tool-call arguments after `chroma_list_collections` returns results.

## Primary Evidence

From streaming tool telemetry:

1. `chroma_list_collections` returns three distinct text items:
   - `tickets`
   - `docs`
   - `consulting_docs`
2. The next model tool call uses:
   - `collection_name="ticketsdocsconsulting_docs"`
3. Chroma fails with:
   - `Collection [ticketsdocsconsulting_docs] does not exist`

Observed in both model-backed flows:

- `cug_lang_chroma_sonnet` (calls `chroma_query_documents`)
- `cug_lang_chroma_gptoss` (calls `chroma_peek_collection` in one repro)

Additional direct instrumentation (post-tool, pre-next-model-call):

- A standalone `astream_events` probe captured `on_chat_model_start` payloads.
- In that payload, `ToolMessage.content` remains a structured list with 3 distinct blocks:
  - `tickets`
  - `docs`
  - `consulting_docs`
- Therefore, the merge is **not** occurring in ATHOS flow state before model invocation.
- Remaining boundary: merge happens later (provider/adaptor message serialization and/or model tool-argument synthesis).

## Minimal Reproducer

Run from repo root:

```bash
python - <<'PY'
import asyncio, uuid
from dotenv import load_dotenv
from athos.runtime.builder import build_config
from athos.runtime.runner import FlowRunner

load_dotenv(".env")

async def run_once(flow):
    cfg = build_config("config/paper/cug_m1.yaml")
    runner = FlowRunner(cfg)
    sid = f"dbg_{flow}_{uuid.uuid4().hex[:8]}"
    print("\n" + "=" * 80)
    print("FLOW:", flow)
    print("SESSION:", sid)
    try:
        async for out in runner.stream(
            flow_name=flow,
            message="What type of GPUs are in the Perlmutter supercomputer?",
            session_id=sid,
            user_id="cli_user",
            interface="cli",
            metadata={"verbosity_level": 0},
        ):
            md = out.metadata or {}
            if md.get("event_type") == "tool_call_start":
                print("TOOL_CALL_START:", md.get("status_message"))
            if md.get("event_type") == "tool_call_complete":
                print("TOOL_CALL_DONE :", md.get("tool_name"))
                print("TOOL_RESULT_RAW:", repr(md.get("tool_result")))
            if md.get("error"):
                print("ERROR:", out.content)
    finally:
        await runner.cleanup()

async def main():
    await run_once("cug_lang_chroma_sonnet")
    await run_once("cug_lang_chroma_gptoss")

asyncio.run(main())
PY
```

## Standalone Probe Reproducer (One-off Study)

Run from repo root:

```bash
python scripts/chroma_toolmessage_probe.py \
  --flow cug_lang_chroma_sonnet \
  --attempts 1 \
  --out logs/chroma_toolmessage_probe_sonnet.jsonl
```

What it captures:

- `on_chat_model_start` / `on_chat_model_end`
- `on_tool_start` / `on_tool_end`
- extracted `ToolMessage` blocks seen at model-start

Key result from probe output:

- `on_chat_model_start` after `chroma_list_collections` contains `ToolMessage.content` as list-of-blocks (not merged string).
- This narrows root-cause scope to downstream serialization/model behavior.

## Expected vs Actual

Expected:

- model should pick one valid collection name per call, e.g. `docs`, `tickets`, or `consulting_docs`

Actual:

- model sometimes concatenates all names into one string: `ticketsdocsconsulting_docs`

## Why This Looks Systematic

- The same merged token appears across different models.
- It appears immediately after a multi-item MCP tool result.
- The merged value ordering matches list output order (`tickets`, `docs`, `consulting_docs`), suggesting flattening/concatenation behavior in message interpretation or tool-argument synthesis.

## Non-Causes Ruled Out

- Not a missing collection in Chroma DB (collections are present).
- Not collection creation/ingestion corruption.
- Not flow config using merged names.

## Useful Existing Logs

- `/global/u2/s/sfarrell/WorkAreas/agentic-ops/athos/logs/repro_chroma_perlmutter_gpus.log`
- `/global/u2/s/sfarrell/WorkAreas/agentic-ops/athos/logs/repro_chroma_question_sonnet.log`
- `/global/u2/s/sfarrell/WorkAreas/agentic-ops/athos/logs/repro_chroma_question_gptoss.log`
- `/global/u2/s/sfarrell/WorkAreas/agentic-ops/athos/logs/repro_chroma_list_collections.log`
- `/global/u2/s/sfarrell/WorkAreas/agentic-ops/athos/logs/chroma_toolmessage_probe_sonnet.jsonl`

## Relevant Probe Script

- `/global/u2/s/sfarrell/WorkAreas/agentic-ops/athos/scripts/chroma_toolmessage_probe.py`

## Next Steps

1. Inspect release notes and git history for likely regression points.
   - Targets:
     - `langchain-mcp-adapters`
     - `langchain-openai`
     - `langgraph`
     - `chroma-mcp`
   - Focus areas:
     - MCP/tool result content structure
     - ToolMessage/content-block serialization
     - Tool call argument synthesis/parsing

2. Run a controlled dependency matrix with isolated environments.
   - Use separate throwaway virtualenvs per cell; do not mutate primary dev env.
   - Keep prompt, input question, and flow config fixed.
   - Record full version manifest per run.
   - Use probe JSONL as canonical artifact.

3. Pin MCP tool version explicitly during matrix runs.
   - Current config uses unpinned `uvx chroma-mcp` and can drift.
   - Test with explicit versions (for example `0.2.6` vs `0.2.7`) to isolate MCP-side behavior.

4. Prioritized minimal matrix (first pass).
   - Baseline current stack.
   - Change only `langchain-mcp-adapters` (e.g. `0.2.1` vs `0.1.11`).
   - Change only LangChain/LangGraph family (current vs `1.0.0` generation).
   - Keep ATHOS stack fixed while varying `chroma-mcp` version.

5. Add a non-MCP control path in LangGraph.
   - Create thin LangChain-native wrappers around local Chroma Python calls.
   - Run same prompt/query without MCP transport.
   - If merge disappears, issue likely tied to MCP output-shape + downstream serialization/model interaction.

6. Define success metric for comparison.
   - `merged_collection_name_rate = merged-name failures / total attempts`
   - Run multiple attempts per cell and compare rates, not single outcomes.

## Release/Git History Findings (2026-03-01)

Completed investigation of release notes and git history for:

- `langchain-mcp-adapters`
- `langchain-openai`
- `langchain-core`
- `langgraph`
- `chroma-mcp`

### Environment Snapshot Used for Correlation

Installed in active ATHOS environment at time of analysis:

- `langchain-mcp-adapters==0.2.1`
- `langchain-openai==1.0.3`
- `langchain-core==1.0.7`
- `langgraph==1.0.9`

### Strongest Suspect: `langchain-mcp-adapters` 0.2.0+

`langchain-mcp-adapters==0.2.0` includes a breaking behavior change:

- "structured output support, using LC standard content blocks"
- conversion behavior changed from prior text simplification into standard LC content blocks

PR `#379` explicitly describes:

- population of `ToolMessage.content` with standard content blocks
- removal of prior simplification of text content blocks

This aligns directly with symptom timing:

- issue appears immediately after multi-item `chroma_list_collections` output
- merged collection token ordering follows returned list ordering

`langchain-mcp-adapters==0.2.1` appears to be dependency-boundary follow-up (`langchain-core>=1.0.0`) rather than new logic for tool-result conversion.

### Lower-Probability Candidates from Same Pass

- `chroma-mcp`:
  - `v0.2.6` release notes focus on chromadb update, regex tool prompts, and collection fork support.
  - there is list-collection related history (`PR #33`), but no direct evidence of downstream merged-token synthesis.
- `langgraph==1.0.9`:
  - release notes do not indicate relevant tool-message/content serialization changes for this symptom.
- `langchain-openai==1.0.3` and `langchain-core==1.0.7`:
  - no release-note signal directly matching this specific merged-collection-name behavior.

### Updated Priority Action

Before broader matrix expansion, run a tight A/B with everything fixed except `langchain-mcp-adapters`:

1. baseline with current (`0.2.1`)
2. downgrade cell (`0.1.11` or `0.1.14`)
3. compare `merged_collection_name_rate` across multiple attempts per cell

If merged-name failures drop materially in the downgraded cell, treat `0.2.0` content-block transition as primary regression boundary.

## Controlled Matrix Results (2026-03-01)

Test design used:

- flow: `cug_lang_chroma_sonnet`
- prompt: `"What type of GPUs are in the Perlmutter supercomputer?"`
- attempts per cell: `10`
- pinned MCP server package in config: `chroma-mcp==0.2.6`
- held constant across cells:
  - `langchain-openai==1.0.3`
  - `langchain-core==1.0.7`
  - `langgraph==1.0.9`
- varied only:
  - `langchain-mcp-adapters`

Results:

1. Baseline cell (`langchain-mcp-adapters==0.2.1`)
   - merged attempts: `5/10`
   - `merged_collection_name_rate = 0.500`
   - `attempt_error` events: `5` (`Collection [ticketsdocsconsulting_docs] does not exist`)

2. Downgrade cell (`langchain-mcp-adapters==0.1.14`)
   - merged attempts: `0/10`
   - `merged_collection_name_rate = 0.000`
   - `attempt_error` events: `0`

3. Downgrade cell (`langchain-mcp-adapters==0.1.11`)
   - merged attempts: `0/10`
   - `merged_collection_name_rate = 0.000`
   - `attempt_error` events: `0`

Interpretation:

- This A/B strongly supports `langchain-mcp-adapters` `0.2.0+` as the regression boundary for merged collection-name synthesis in this workflow.
- Specifically, behavior reproduces with `0.2.1` and disappears in both pre-`0.2.0` cells under otherwise fixed stack and prompt conditions.

Artifacts:

- `/tmp/athos_chroma_matrix/logs/baseline_probe.jsonl`
- `/tmp/athos_chroma_matrix/logs/mcpadapters_0_1_14_probe.jsonl`
- `/tmp/athos_chroma_matrix/logs/mcpadapters_0_1_11_probe.jsonl`
- `/tmp/athos_chroma_matrix/logs/baseline_versions.txt`
- `/tmp/athos_chroma_matrix/logs/mcpadapters_0_1_14_versions.txt`
- `/tmp/athos_chroma_matrix/logs/mcpadapters_0_1_11_versions.txt`

## Post-Pin Validation in ATHOS Env (2026-03-01)

After pinning:

- project dependency set to `langchain-mcp-adapters==0.1.14`
- active `athos` environment updated to `langchain-mcp-adapters==0.1.14`

Minimal reproducer rerun (from this document, unchanged prompt and flows):

- `cug_lang_chroma_sonnet`
- `cug_lang_chroma_gptoss`

Observed behavior:

- `chroma_list_collections` returned: `["tickets", "docs", "consulting_docs"]`
- subsequent tool calls used valid collection names (`docs`, `consulting_docs`, `tickets`)
- no merged token (`ticketsdocsconsulting_docs`) observed
- no `Collection [ticketsdocsconsulting_docs] does not exist` errors observed

Interpretation:

- In this environment, pinning to `langchain-mcp-adapters==0.1.14` mitigates the merged-collection-name failure in the documented minimal reproducer.

## Notes

- If `.env` is not loaded in ad-hoc Python runs, `${ATHOS_WORKSPACE}` can resolve incorrectly and make the DB appear empty; that is a separate issue from this merged-name bug.
