# CUG Experiments v1 (M2)

Status: Complete for current paper results (2026-03-10)

This document defines the M2 expanded experiment set. M1 remains documented in `EXPERIMENTS_V0.md`.

## Scope

M2 goals:
- Evaluate the M1 flow matrix on expanded datasets.
- Add variance runs for leading configurations.
- Focus expanded-study signal on new datasets (ticket cases + expanded QA).

M2 completion note:
- Current paper result set includes:
  - `lang_gptoss_base`
  - `lang_gptoss_chroma`
  - `lang_sonnet_base`
  - `lang_sonnet_chroma`

## Axes

### Agent Harness
- `langchain`
- external coding-agent baselines (import + score path)

### Tool Type
- `llm_only` (no tools)
- `semantic_retrieval` (Chroma-backed)

### Models
- `gptoss`
- `claude_sonnet`

### Datasets
- Expanded QA:
  - `evals/nersc_qa.v2.jsonl`
- Expanded ticket-style cases:
  - `${SCRATCH}/athos/data/ticket_cases` (or site-specific equivalent)

### Variance
- Incremental runs via `--run-count` and `--run-start`

## Selected Experiments

| ID | Purpose | Config Pointer | Dataset Pointer | Run Policy | Status |
|---|---|---|---|---|---|
| M2-E1 | No-tool baseline (LangChain, GPTOSS) | `config/paper/cug_m1.yaml :: cug_lang_base_gptoss` | `nersc_qa.v2` + ticket cases | `run_count=1` | Complete |
| M2-E2 | No-tool baseline (LangChain, Sonnet) | `config/paper/cug_m1.yaml :: cug_lang_base_sonnet` | same as M2-E1 | `run_count=1` | Complete |
| M2-E3 | Chroma retrieval baseline (LangChain, GPTOSS) | `config/paper/cug_m1.yaml :: cug_lang_chroma_gptoss` | same as M2-E1 | `run_count=1` | Complete |
| M2-E4 | Chroma retrieval baseline (LangChain, Sonnet) | `config/paper/cug_m1.yaml :: cug_lang_chroma_sonnet` | same as M2-E1 | `run_count=1` | Complete (stitched) |
| M2-E5 | Variance on leading configs | top-2 from M2-E1..E4 | same as M2-E1 | `run_count>=3` | Deferred to M3 planning |
| M2-E6 | External coding-agent carry-forward | imported via `evals/import_runs.py`; scored via `scripts/score_cug_external.sh` + `config/paper/cug_m1.yaml` (mini harness; later superseded by M4 full filesystem-bundle reruns) | dataset IDs must align with local references | per external runner | Complete |

## Execution Notes

- Use `scripts/run_cug_m2.sh` for canonical run generation and `scripts/score_cug_m2.sh` for scoring/summarization.
- Defaults include expanded datasets with path preflight and warnings for missing optional paths.
- Set `STRICT_DATASET_PATHS=1` to fail fast when any referenced dataset path is missing.
- For retrieval experiments, pass `--aggregate-manifest` (or set `AGGREGATE_MANIFEST`) so run artifacts include retrieval provenance.

## Retrieval Gate (Required for M2 Retrieval Claims)

Before freezing retrieval comparisons:
- Confirm expected Chroma collection names exist in the selected aggregate DB.
- Run a retrieval smoke check with representative queries.
- If collections are missing/mismatched, rerun affected retrieval experiments after fixing ingestion/config wiring.

## M2 Execution Caveats and Fixes

- Some scoring runs failed intermittently; this was patched by enabling judge retries.
- `lang_sonnet_chroma` exhausted CBorg quota mid-run; remaining work switched to AmSC I2 API and results were stitched using `scripts/materialize_stitched_sonnet_runs.py`.
- Many Chroma flow eval failures were due to collection retrieval errors; current LangChain flow behavior can abort when a wrong collection name is retrieved.
- Runtime overhead was amplified by repeated chroma-mcp `uvx` environment creation; M3 should use a local `chroma-mcp` install in the ATHOS environment.

## M3 Carry-Forward Note (2026-03-11)

- M3 smoke identified an additional retrieval stability issue in the MCP/LangChain path:
  - `chroma_peek_collection` intermittently returned non-JSON-serializable content (`numpy.ndarray`) and caused execution failures.
- For current paper-facing M3 runs, `chroma_peek_collection` is excluded from active retrieval toolsets.
- Active retrieval subset for these runs is: `chroma_list_collections`, `chroma_get_collection_info`, `chroma_get_collection_count`, `chroma_query_documents`, `chroma_get_documents`.
- M1 small-dataset harness comparison (`results/cug_m3_var_20260311_231139`) adds a four-row LangChain vs SmolAgents view:
  - `langchain + claude_sonnet` was strongest overall,
  - `smolagents + claude_sonnet` was competitive but weaker and more token-expensive,
  - both `gptoss` rows underperformed materially, with `smolagents + gptoss` weakest.
- Current interpretation for paper framing:
  - model choice dominated harness choice on M1,
  - SmolAgents should not be judged from the GPTOSS row alone,
  - Sonnet-backed SmolAgents is viable as an auxiliary comparison row rather than part of the main six-row LangChain table.

## M3 Variance Status (2026-03-12)

- Collaborator-run variance artifact for `cug_lang_chroma_gptoss_opt` is now available at:
  - `madan_results/cug_m3_var_20260312_093435`
- Scope matches the planned small-dataset variance study:
  - `evals/test_cases`
  - `evals/simple_qa.jsonl`
  - `run_count=10`
- Current interpretation:
  - keep observed execution/output failures in the variance story rather than cleaning them away with targeted reruns
  - the GPTOSS artifact includes `3` such failures over `120` total attempts
- Collaborator-run variance artifact for `cug_lang_chroma_sonnet_opt` is now available at:
  - `madan_results/cug_m3_var_20260312_130318`
  - `120` total attempts, `0` execution/output skips
- Manuscript status:
  - the repeated-run variance study is now visualized in the paper as a dedicated side-by-side figure
  - Sonnet's consistent miss on `salloc-account-error` is retained as a qualitative failure-analysis example rather than treated as run noise
- Bookkeeping caveat:
  - current summaries use `skipped_count` as the visible failure count while also zero-penalizing those failed attempts in score/pass metrics
  - follow-up cleanup is tracked separately in GitHub issue `#87`

## Main Table Assembly Note (2026-03-11)

For manuscript main-results table assembly, combine:
- M2 baseline/no-tool + M2 Chroma rows (4 configs total), and
- M3 Chroma-optimized full expanded-set rows (2 configs):
  - `cug_m3_full_gptoss_opt_20260311_013848`
  - `cug_m3_full_sonnet_opt_20260311_081645`

This yields the intended six-config LangChain main table.
Filesystem-tool rows are optional and should be included only if run stability is acceptable.
