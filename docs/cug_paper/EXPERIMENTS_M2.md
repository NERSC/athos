# CUG Experiments v1 (M2)

Status: Draft v0.1 (2026-03-09)

This document defines the M2 expanded experiment set. M1 remains documented in `EXPERIMENTS_V0.md`.

## Scope

M2 goals:
- Evaluate the M1 flow matrix on expanded datasets.
- Add variance runs for leading configurations.
- Focus expanded-study signal on new datasets (ticket cases + expanded QA).

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
| M2-E1 | No-tool baseline (LangChain, GPTOSS) | `config/paper/cug_m1.yaml :: cug_lang_base_gptoss` | `nersc_qa.v2` + ticket cases | `run_count=1` | Planned |
| M2-E2 | No-tool baseline (LangChain, Sonnet) | `config/paper/cug_m1.yaml :: cug_lang_base_sonnet` | same as M2-E1 | `run_count=1` | Planned |
| M2-E3 | Chroma retrieval baseline (LangChain, GPTOSS) | `config/paper/cug_m1.yaml :: cug_lang_chroma_gptoss` | same as M2-E1 | `run_count=1` | Planned |
| M2-E4 | Chroma retrieval baseline (LangChain, Sonnet) | `config/paper/cug_m1.yaml :: cug_lang_chroma_sonnet` | same as M2-E1 | `run_count=1` | Planned |
| M2-E5 | Variance on leading configs | top-2 from M2-E1..E4 | same as M2-E1 | `run_count>=3` | Planned |
| M2-E6 | External coding-agent carry-forward | imported via `evals/import_runs.py` | dataset IDs must align with local references | per external runner | Planned |

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
