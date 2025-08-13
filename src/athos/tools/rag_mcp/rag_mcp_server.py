"""FastMCP server providing BM25-based retrieval over NERSC docs."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
from typing import Optional

from fastmcp import FastMCP
from pydantic import BaseModel, Field

from .rag_bm25 import RAGBM25

REPO_URL = "https://gitlab.com/NERSC/nersc.gitlab.io.git"
LOCAL_PATH = Path(__file__).resolve().parent / "nersc_docs"


class QueryParams(BaseModel):
    """Parameters for the query tool."""

    query: str = Field(..., description="Search query")
    k: int = Field(5, description="Number of results to return")


class RAGMCPServer:
    """FastMCP-based server for RAG BM25 retrieval."""

    def __init__(self) -> None:
        self.mcp = FastMCP("RAG")
        self.rag_index: Optional[RAGBM25] = None
        self._setup_tools()

    def _setup_tools(self) -> None:
        @self.mcp.tool()
        async def query(params: QueryParams) -> str:
            """Search NERSC documentation using BM25."""

            if self.rag_index is None:
                return "Index not ready"

            results = await asyncio.to_thread(
                self.rag_index.query, params.query, k=params.k
            )
            texts = [f"{path}: {chunk}" for path, chunk in results]
            return "\n\n".join(texts) if texts else "No results found"

    def build_index(self, rebuild: bool = False) -> None:
        """Build or rebuild the BM25 index."""

        if rebuild and LOCAL_PATH.exists():
            import shutil

            shutil.rmtree(LOCAL_PATH)

        self.rag_index = RAGBM25.from_repo(REPO_URL, str(LOCAL_PATH))

    def run(self) -> None:
        """Run the MCP server."""

        self.mcp.run()


def main() -> None:
    parser = argparse.ArgumentParser(description="RAG MCP Server")
    parser.add_argument("--rebuild", action="store_true", help="Rebuild index")
    args = parser.parse_args()

    server = RAGMCPServer()
    server.build_index(rebuild=args.rebuild)
    server.run()


def cli() -> None:
    """Command-line entry point for the RAG MCP server."""
    asyncio.run(main())


if __name__ == "__main__":
    cli()
