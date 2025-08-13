"""FastMCP server providing BM25-based retrieval over NERSC docs."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
from typing import Optional

from fastmcp import FastMCP
from pydantic import Field

from .rag_bm25 import RAGBM25

DEFAULT_REPO_URL = "https://gitlab.com/NERSC/nersc.gitlab.io.git"
DEFAULT_LOCAL_PATH = Path(__file__).resolve().parent / "nersc_docs"


class RAGMCPServer:
    """FastMCP-based server for RAG BM25 retrieval."""

    def __init__(
        self,
        repo_url: str | None = DEFAULT_REPO_URL,
        docs_path: str | Path | None = DEFAULT_LOCAL_PATH,
        *,
        chunk_size: int = 200,
        overlap: int = 50,
        query_docstring: str = "Search NERSC documentation using BM25.",
    ) -> None:
        self.mcp = FastMCP("RAG")
        self.rag_index: Optional[RAGBM25] = None
        self.repo_url = repo_url
        self.docs_path = Path(docs_path) if docs_path is not None else None
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.query_docstring = query_docstring
        self._setup_tools()

    def _setup_tools(self) -> None:
        @self.mcp.tool()
        async def query(
            query: str = Field(description="Search query string"),
            k: int = Field(5, description="Number of results to return", ge=1, le=100),
        ) -> str:
            """Placeholder docstring overwritten at runtime."""

            if self.rag_index is None:
                return "Index not ready"

            results = await asyncio.to_thread(self.rag_index.query, query, k=k)
            texts = [f"{path}: {chunk}" for path, chunk in results]
            return "\n\n".join(texts) if texts else "No results found"

        # Allow custom documentation for this tool
        query.__doc__ = self.query_docstring

    def build_index(self, rebuild: bool = False) -> None:
        """Build or rebuild the BM25 index."""

        if self.docs_path is not None and rebuild and self.docs_path.exists():
            import shutil

            shutil.rmtree(self.docs_path)

        if self.repo_url:
            path = self.docs_path or DEFAULT_LOCAL_PATH
            self.rag_index = RAGBM25.from_repo(
                self.repo_url,
                str(path),
                chunk_size=self.chunk_size,
                overlap=self.overlap,
            )
            self.docs_path = Path(path)
        elif self.docs_path is not None:
            self.rag_index = RAGBM25.from_path(
                self.docs_path,
                chunk_size=self.chunk_size,
                overlap=self.overlap,
            )
        else:
            raise ValueError("Either repo_url or docs_path must be provided")

    def run(self) -> None:
        """Run the MCP server."""

        self.mcp.run()


def main() -> None:
    parser = argparse.ArgumentParser(description="RAG MCP Server")
    parser.add_argument("--repo-url", default=None, help="Git repository URL to index")
    parser.add_argument(
        "--docs-path",
        "--local-dir",
        dest="docs_path",
        default=None,
        help="Local directory containing documentation",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=200,
        help="Text chunk size for indexing",
    )
    parser.add_argument(
        "--overlap",
        type=int,
        default=50,
        help="Token overlap between chunks",
    )
    parser.add_argument("--rebuild", action="store_true", help="Rebuild index")
    args = parser.parse_args()

    server = RAGMCPServer(
        repo_url=args.repo_url,
        docs_path=args.docs_path,
        chunk_size=args.chunk_size,
        overlap=args.overlap,
    )
    server.build_index(rebuild=args.rebuild)
    server.run()


def cli() -> None:
    """Command-line entry point for the RAG MCP server."""
    asyncio.run(main())


if __name__ == "__main__":
    cli()
