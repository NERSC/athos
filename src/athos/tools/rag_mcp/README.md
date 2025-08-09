# RAG MCP Server

This MCP server exposes a single `query` tool that searches the NERSC
user documentation hosted at
<https://gitlab.com/NERSC/nersc.gitlab.io>.

On startup the server clones the repository (if needed), chunks all
Markdown files and builds a BM25 index. Queries return the top-k chunks
with file path context.

## Running

```bash
python rag_mcp_server.py
```

Use `--rebuild` to force re-cloning and re-indexing the repository.
