# CUG Experiments v0

Status: Draft v0.1

## Axes

### Agent Harness
- `smolagents`
- `langchain`
- `claude-code`

### Tool Type
- `llm_only` (no tools)
- `semantic_retrieval`: `docs_rag_mcp`, `chroma_mcp`, `websearch`, `langchain_tavily_search`
  - includes semantic retrieval over documentation and historical ServiceNow ticket corpus (via Chroma ingestion pipeline)
- `file_tools`: `filesystem_mcp`
  - includes file-based retrieval over documentation plus ticket JSON + attachments on filesystem

### Model
- Open-weight models: `cborg_coder` (gpt-oss-120b)
- Proprietary frontier models: claude-sonnet

### Datasets
- Q&A benchmark (expanded versions)
- Single-turn ticket benchmark (synthetic benchmark-ready)
- Additional categories (SRE / utilization), candidate track

### Variance
- Incremental runs via `--run-count` and `--run-start`

## Selected Experiments

| ID | Purpose | Config Pointer | Dataset Pointer | Status |
|---|---|---|---|---|
| E1 | No-tool baseline | `TBD` | `TBD` | Planned |
| E2 | Tool-enabled baseline | `TBD` | `TBD` | Planned |
| E3 | Coding-agent point | `TBD` | `TBD` | Planned |
| E4 | Open vs proprietary comparison | `TBD` | `TBD` | Planned |
| E5 | Variance run set | `TBD` | `TBD` | Planned |

## Changelog

### v0.2
- Recorded pipeline robustness update: canonical run generation now preflights target `run.json` paths before execution to avoid partial-write reruns.
- Added planning note to watch `skipped_missing_reference` when scoring imported runs whose dataset IDs may not match local dataset naming.

### v0.3
- Clarified that historical ServiceNow tickets are an additional retrieval corpus under existing tool-type experiments (`semantic_retrieval` and `file_tools`).
- Confirmed scope: no new evaluation datasets or metrics required for ticket-corpus integration; existing `test_cases`/Q&A benchmarks remain primary in v0.

### v0.1
- Created minimal experiments document with axes, selected experiments, and changelog only.
