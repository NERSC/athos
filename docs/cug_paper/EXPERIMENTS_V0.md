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
- `file_tools`: `filesystem_mcp`

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

### v0.1
- Created minimal experiments document with axes, selected experiments, and changelog only.
