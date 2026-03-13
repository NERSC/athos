# CUG Experiments v0 (M1)

Status: Draft v0.6 (M1 reference)

This document is the M1 baseline reference.
For expanded-study planning and execution, see `docs/cug_paper/EXPERIMENTS_M2.md`.

## Axes

### Agent Harness
- `langchain`
- external coding-agent baselines (run outside ATHOS; imported for scoring)

### Tool Type
- `llm_only` (no tools)
- `semantic_retrieval`: `chroma_mcp` (langchain)
  - includes semantic retrieval over documentation and historical ServiceNow ticket corpus (via Chroma ingestion pipeline)
- `file_based_retrieval`: `filesystem_mcp` (langchain; optional comparison row)
  - canonical paper configuration for this axis is the bundle-backed filesystem setup rooted at `ATHOS_WORKSPACE/file_retrieval_corpus`
  - this is intended to be a frozen, read-only, task-oriented file corpus rather than raw whole-workspace exposure

### Model
- Open-weight models: `gptoss` (`lbl/cborg-coder`, GPT-OSS-120B)
- Proprietary models: `claude_sonnet` (`anthropic/claude-sonnet`)

### Datasets (M1)
- `evals/test_cases`
- `evals/simple_qa.jsonl`
- Additional dataset expansion remains in the M2+ track.

### Variance
- Incremental runs via `--run-count` and `--run-start`

## Selected Experiments (M1)

| ID | Purpose | Config Pointer | Dataset Pointer | Status |
|---|---|---|---|---|
| E1 | No-tool baseline (LangChain) | `config/paper/cug_m1.yaml :: cug_lang_base_gptoss` | `evals/test_cases` + `evals/simple_qa.jsonl` | Ready |
| E2 | No-tool baseline (LangChain, Sonnet) | `config/paper/cug_m1.yaml :: cug_lang_base_sonnet` | `evals/test_cases` + `evals/simple_qa.jsonl` | Ready |
| E3 | Chroma retrieval baseline (LangChain) | `config/paper/cug_m1.yaml :: cug_lang_chroma_gptoss` | `evals/test_cases` + `evals/simple_qa.jsonl` | Ready |
| E4 | Chroma retrieval baseline (LangChain, Sonnet) | `config/paper/cug_m1.yaml :: cug_lang_chroma_sonnet` | `evals/test_cases` + `evals/simple_qa.jsonl` | Ready |
| E5 | Variance run set | E1-E4 with `--run-count` / `--run-start` | `evals/test_cases` + `evals/simple_qa.jsonl` | Planned |
| E6 | External coding-agent comparison point | External runner outputs imported via `evals/import_runs.py` and scored with `evals/score_runs.py` | Imported run dataset IDs must match local references | Planned |

Notes:
- M1 ATHOS-run experiments cover both open-weight (`gptoss`) and proprietary (`claude_sonnet`) model baselines through LangChain flows in `config/paper/cug_m1.yaml`.
- For retrieval experiments, run generation should include `--aggregate-manifest <path>` to capture retrieval corpus provenance in canonical run artifacts.
- File-based retrieval remains an optional comparison track; current lessons learned indicate that corpus shaping and explicit bundle indexing are critical for stable behavior.
- M1 closeout checklist and current status are tracked in `docs/cug_paper/PLAN.md`.

## Changelog

### v0.6
- Relabeled this doc as M1 reference scope.
- Added pointer to `EXPERIMENTS_M2.md` for expanded-study planning and execution.

### v0.5
- Replaced SmolAgents M1 matrix rows with LangChain Claude Sonnet baselines (no-tool + Chroma retrieval).
- Updated model-axis scope to include both `gptoss` and `claude_sonnet` for M1 ATHOS-run experiments.

### v0.4
- Added concrete M1 experiment matrix pointers to frozen config `config/paper/cug_m1.yaml`.
- Locked M1 ATHOS-run scope to open-weight `gptoss` model only.
- Added explicit external coding-agent experiment path (import + score workflow, not ATHOS flow execution).

### v0.2
- Recorded pipeline robustness update: canonical run generation now preflights target `run.json` paths before execution to avoid partial-write reruns.
- Added planning note to watch `skipped_missing_reference` when scoring imported runs whose dataset IDs may not match local dataset naming.

### v0.3
- Clarified that historical ServiceNow tickets are an additional retrieval corpus under existing tool-type experiments (`semantic_retrieval` and `file_tools`).
- Confirmed scope: no new evaluation datasets or metrics required for ticket-corpus integration; existing `test_cases`/Q&A benchmarks remain primary in v0.

### v0.1
- Created minimal experiments document with axes, selected experiments, and changelog only.
