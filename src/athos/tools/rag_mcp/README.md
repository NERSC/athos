# RAG MCP Server

This FastMCP server exposes a single `query` tool that searches the NERSC
user documentation hosted at
<https://gitlab.com/NERSC/nersc.gitlab.io>.
If `ATHOS_WORKSPACE` is set, documentation will be cached in
`$ATHOS_WORKSPACE/docs`; otherwise a package-local directory is used.

On startup the server clones the repository (if needed), chunks all
Markdown files and builds a BM25 index. Queries return the top-k chunks
with file path context.

## Running

```bash
python rag_mcp_server.py [--repo-url URL] [--docs-path PATH] \
                         [--chunk-size N] [--overlap M] [--rebuild]
```

Use `--rebuild` to force re-cloning and re-indexing the repository. The
`--repo-url` and `--docs-path` arguments control which repository and local
directory are indexed. `--chunk-size` and `--overlap` tune how the
documentation is split into chunks for retrieval.
