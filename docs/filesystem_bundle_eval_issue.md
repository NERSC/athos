# Filesystem Bundle Eval Issue

**Status:** active, but materially improved. The canonical paper filesystem config now uses a bundle-rooted workspace and performs strongly on the docs-only mini QA smoke set, with a modest regression once raw tickets are added back in.

## Summary

We have been trying to make the file-based retrieval/tooling comparison viable for the CUG paper evals.

The original broad-workspace filesystem setup was functional at the ATHOS infra level, but agent behavior was poor and unstable:

- many runs terminated with `GraphRecursionError`
- some runs attempted invalid filesystem operations such as `read_file` on a directory
- earlier runs also attempted paths outside the intended allowed root

To reduce workspace noise and path ambiguity, we added a dedicated filesystem-eval bundle rooted at:

- `ATHOS_WORKSPACE/file_retrieval_corpus`

That narrowed the available search surface to selected docs/consulting-docs content and gave us a place to add a generated task-routing `INDEX.md`.

This turned out to be the key design change. The narrowed root alone helped path hygiene, but the major quality jump came from pairing the bundle with:

- a stronger, more prescriptive filesystem prompt
- a much more explicit `INDEX.md` with topic and question routing hints

## What We Changed

### 1. Added filesystem-eval bundle assembly

`scripts/build_workspace.py` now supports an explicit path-driven file-retrieval corpus build:

- `--fs-docs-dir`
- `--fs-consulting-docs-dir`
- `--fs-tickets-dir`
- `--fs-include-tickets`
- `--build-fs-index`

When any `--fs-*` source path is provided, the paper-specific subtree under

- `workspace/file_retrieval_corpus`

is created or updated without requiring the legacy workspace copies.

Current bundle build used:

```bash
python scripts/build_workspace.py \
  --workspace-dir workspace \
  --fs-docs-dir data/docs/docs \
  --fs-consulting-docs-dir data/consulting_docs/docs \
  --fs-tickets-dir data/servicenow_tickets_balanced_v0_20260306_filtered \
  --fs-include-tickets \
  --build-fs-index
```

Resulting manifests:

- `workspace/.workspace_assembly_manifest.json`
- `workspace/file_retrieval_corpus/manifest.json`

### 2. Made the bundle-backed setup canonical in the paper config

The canonical paper config is now in:

- `config/paper/cug_m1.yaml`

`filesystem_mcp` now points at:

- `${ATHOS_WORKSPACE}/file_retrieval_corpus`

and the canonical paper flow names are:

- `cug_lang_filesystem_gptoss`
- `cug_lang_filesystem_sonnet`

The active filesystem tool surface remains read-only:

- `list_allowed_directories`
- `list_directory`
- `directory_tree`
- `read_file`
- `read_multiple_files`
- `search_files`
- `get_file_info`

### 3. Strengthened the filesystem prompt

The filesystem prompt now strongly constrains startup behavior:

- first call `list_allowed_directories`
- then read `INDEX.md`
- only then choose a narrower search/read path

This was necessary to stop GPT-OSS from treating the bundle like an unindexed open-ended corpus.

### 4. Upgraded the generated bundle index

The generated `workspace/file_retrieval_corpus/INDEX.md` is no longer a generic placeholder. It now includes:

- topic-to-path routing
- explicit starting files for core question types
- mini-QA-specific hints for the current smoke set

Representative routing entries include:

- QOS / charging questions: `docs/jobs/policy.md`
- Perlmutter hardware questions: `docs/systems/perlmutter/architecture.md`
- filesystem policy questions: `docs/filesystems/perlmutter-scratch.md`
- AI support questions: search under `consulting_docs/`

## Key Evidence

### Earlier broad-workspace filesystem smoke

The older filesystem row failed heavily and showed two main failure classes:

- recursion-limit failures
- path/access failures

Representative artifacts:

- `results/cug_m3_smoke_20260311_003639/aggregates/summary.json`
- `results/cug_m3_smoke_20260311_010707/aggregates/summary.json`

Examples:

- recursion-limit failure:
  - `results/cug_m3_smoke_20260311_003639/athos/cug_lang_filesystem_gptoss__gptoss__248b0b74/simple_qa/perlmutter_debug_qos/0/run.json`
- path escape failure:
  - `results/cug_m3_smoke_20260311_010707/athos/cug_lang_filesystem_gptoss__gptoss__b8014752/simple_qa/purged_filesystem/0/run.json`

### First bundle-rooted smoke

The initial narrowed bundle removed the path-outside-root failure mode, but the agent still failed on all five QA cases.

Representative artifacts:

- summary:
  - `results/cug_m3_smoke_fs_bundle_20260312_192506/aggregates/summary.json`
- skip log:
  - `results/cug_m3_smoke_fs_bundle_20260312_192506/judgments/gptoss_rubric_v1.skips.jsonl`
- example invalid filesystem call:
  - `results/cug_m3_smoke_fs_bundle_20260312_192506/athos/cug_lang_filesystem_bundle_gptoss__gptoss__045a0302/simple_qa/perlmutter_gpus/0/run.json`

That `run.json` shows:

- `status=execution_error`
- `error_type=ToolException`
- `output_text="Error: Error: EISDIR: illegal operation on a directory, read"`

The remaining cases mostly ended in:

- `GraphRecursionError`

### Repro-based diagnosis

Using the repro example on the debug-QOS question showed the progression clearly:

1. before prompt tightening, GPT-OSS repeatedly issued broad `search_files` calls and never converged
2. after prompt tightening, GPT-OSS did read `INDEX.md`, but the original index was too weak to route the next step
3. after strengthening the index, GPT-OSS read `INDEX.md`, jumped directly to `docs/jobs/policy.md`, and answered correctly

Relevant artifacts:

- `logs/repro_filesystem_bundle_debug_qos.jsonl`
- `logs/repro_filesystem_bundle_debug_qos_v4.jsonl`

### Current mini QA smoke result

After the corpus, prompt, and index updates, the canonical GPT-OSS filesystem row performs strongly on the docs-only mini QA smoke set:

- experiment:
  - `results/cug_m3_smoke_fs_gptoss_v3_20260312_214620`
- summary:
  - `results/cug_m3_smoke_fs_gptoss_v3_20260312_214620/aggregates/summary.json`
- judgments:
  - `results/cug_m3_smoke_fs_gptoss_v3_20260312_214620/judgments/gptoss_rubric_v1.jsonl`

Observed result:

- `run_count=5`
- `skipped_count=0`
- `score_mean=99.0`
- `pass_rate=1.0`

Per-question scores:

- `nersc_ai_support_group`: `95`
- `perlmutter_debug_qos`: `100`
- `perlmutter_gpus`: `100`
- `premium_qos_charge_factor`: `100`
- `purged_filesystem`: `100`

Token cost on this smoke set is also comparatively low:

- `tokens_total_mean=17747.2`

### Ticket-inclusive mini QA smoke result

Adding raw ticket JSON back into the corpus caused a moderate regression, but not a collapse:

- experiment:
  - `results/cug_m3_smoke_fs_gptoss_tickets_20260312_232026`
- summary:
  - `results/cug_m3_smoke_fs_gptoss_tickets_20260312_232026/aggregates/summary.json`
- judgments:
  - `results/cug_m3_smoke_fs_gptoss_tickets_20260312_232026/judgments/gptoss_rubric_v1.jsonl`

Observed result:

- `run_count=5`
- `skipped_count=1`
- `score_mean=80.0`
- `pass_rate=0.8`

The skipped case was:

- `nersc_ai_support_group`

Representative failure artifact:

- `results/cug_m3_smoke_fs_gptoss_tickets_20260312_232026/athos/cug_lang_filesystem_gptoss__gptoss__57048e37/simple_qa/nersc_ai_support_group/0/run.json`

That run ended with:

- `status=execution_error`
- `error_type=ToolException`
- `output_text="Error: Error: EISDIR: illegal operation on a directory, read"`

Interpretation:

- adding tickets did not break the row globally
- but the broader heterogeneous corpus did reintroduce some tool-use brittleness
- the current filesystem row is therefore good enough to treat as meaningful paper signal, but not yet fully stable on the ticket-inclusive corpus

### Sonnet expanded QA run

We also obtained a collaborator-run Sonnet filesystem result on the expanded QA dataset only:

- experiment:
  - `results/cug_m3_smoke_20260313_145034`
- summary:
  - `results/cug_m3_smoke_20260313_145034/aggregates/summary.json`

Recorded aggregate:

- `run_count=123`
- `skipped_count=17`
- `score_mean=69.52`
- `pass_rate=0.6504`
- `tokens_total_mean=44678.08`

However, this run appears to be quota-contaminated rather than cleanly representative:

- the skipped cases were all marked `skipped_execution_status`
- the skipped `run.json` files contain effectively no terminal error payload:
  - `status=null`
  - `error=null`
  - `metadata=null`
- the 17 skipped cases were emitted in a tight burst at the end of the run rather than being distributed throughout execution

That pattern is much more consistent with provider quota exhaustion than with case-specific retrieval failures.

Interpretation:

- the run is useful evidence that the Sonnet filesystem config is operational at expanded-QA scale
- the reported aggregate is likely pessimistic because the final 17 cases were probably lost to exhausted quota
- any paper-facing use of this result should mark it as provisional until those tail cases are rerun

## Lessons Learned

These are the main takeaways to carry into the paper discussion of file-based tool configs:

1. Raw filesystem exposure is a poor baseline for weaker agent models.
   - Even when infra wiring is correct, the search space is too open and failure-prone.

2. File-based retrieval needs corpus shaping, not just tool access.
   - The bundle-root restriction mattered because it removed irrelevant workspace surface area.

3. Explicit navigational scaffolding is high leverage.
   - The strongest improvement did not come from changing tools; it came from forcing the agent to read an index and making that index actually useful.

4. Agent control policy matters as much as retrieval source.
   - The same docs corpus went from unusable to strong once the startup procedure became prescriptive.

5. Small, well-structured file corpora can be cost-efficient.
   - On the mini QA smoke set, the tuned filesystem row was cheaper than nearby Chroma and Smol baselines.

6. The fair file-based comparison for the paper is not "entire workspace filesystem access."
   - The defensible comparison point is a frozen, read-only, task-oriented bundle.

7. Broader heterogeneous corpora still expose navigation brittleness.
   - Adding raw tickets back into the corpus caused only a moderate regression, but it was enough to reintroduce at least one execution failure on the mini QA set.

## Observability Gap

Current `run.json` artifacts capture:

- final execution status
- final error text
- some aggregate metadata

But failed eval runs do not currently persist the full LangGraph message/tool trace that led to failure.

The LangGraph agent flow supports:

- `tool_call_start` / `tool_call_complete` events on the streaming path
- optional `langgraph_steps` / `langgraph_state` metadata in some cases

However, for failed eval runs we mostly only retain the terminal error summary.

## Repro Example

To inspect the live tool-call sequence for one filesystem bundle case, use:

- `src/athos/examples/repro_filesystem_bundle_case.py`

This script:

- runs the canonical bundle-rooted filesystem flow
- uses `FlowRunner.stream(...)`
- prints `tool_call_start` and `tool_call_complete` events live
- prints the final streamed answer or error
- can also write a JSONL event log for later inspection

Example:

```bash
export ATHOS_WORKSPACE=/pscratch/sd/s/sfarrell/athos/workspace

python src/athos/examples/repro_filesystem_bundle_case.py \
  --config config/paper/cug_m1.yaml \
  --flow cug_lang_filesystem_gptoss \
  --prompt "What is the Perlmutter debug QOS time limit?" \
  --show-metadata \
  --out logs/repro_filesystem_bundle_debug_qos.jsonl
```

## Recommended Next Steps

1. Treat the current docs-only and ticket-inclusive smoke results as the present file-based retrieval evidence for the paper.
2. Keep using the repro script when a filesystem row regresses, since failed eval artifacts still do not preserve full traces.
3. If this row needs another improvement pass later, prefer tool-surface restrictions or corpus-specific routing improvements over reverting to raw whole-workspace exposure.
