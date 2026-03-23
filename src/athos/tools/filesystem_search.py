"""Content search tool for the filesystem eval flow.

Provides grep-style file content search over an allowed directory tree.
Uses ripgrep when available, falls back to a pure-Python implementation.

Intended for use alongside the filesystem MCP server, which only supports
filename pattern matching (search_files). This tool fills the gap by
searching file *content*.
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Optional

from langchain_core.tools import tool


_MAX_RESULTS = 20
_CONTEXT_CHARS = 120


def _rg_available() -> bool:
    try:
        subprocess.run(
            ["rg", "--version"],
            capture_output=True,
            check=True,
        )
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def _search_with_rg(root: Path, pattern: str, max_results: int) -> list[tuple[str, str]]:
    """Return list of (relative_path, snippet) pairs via ripgrep."""
    result = subprocess.run(
        [
            "rg",
            "--ignore-case",
            "--with-filename",
            "--line-number",
            "--max-count", "2",          # max matches per file
            "--max-filesize", "500K",
            "-e", pattern,
            str(root),
        ],
        capture_output=True,
        text=True,
    )
    hits: list[tuple[str, str]] = []
    seen_files: set[str] = set()
    for line in result.stdout.splitlines():
        try:
            file_part, rest = line.split(":", 1)
        except ValueError:
            continue
        rel = os.path.relpath(file_part, root)
        snippet = rest[:_CONTEXT_CHARS]
        if rel not in seen_files:
            hits.append((rel, snippet))
            seen_files.add(rel)
        if len(hits) >= max_results:
            break
    return hits


def _search_python(root: Path, pattern: str, max_results: int) -> list[tuple[str, str]]:
    """Pure-Python fallback: walk files and search for pattern."""
    try:
        rx = re.compile(pattern, re.IGNORECASE)
    except re.error:
        rx = re.compile(re.escape(pattern), re.IGNORECASE)

    hits: list[tuple[str, str]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        m = rx.search(text)
        if m:
            start = max(0, m.start() - 40)
            snippet = text[start : m.end() + 80].replace("\n", " ")[:_CONTEXT_CHARS]
            hits.append((str(path.relative_to(root)), snippet))
        if len(hits) >= max_results:
            break
    return hits


@tool
def search_file_contents(pattern: str, path: str) -> str:
    """Search file *contents* for a pattern within an allowed directory.

    Unlike search_files (which matches file names), this tool searches the
    text inside files using a case-insensitive string or regex pattern.

    Args:
        pattern: Search string or regular expression to find in file content.
        path: Directory to search under (must be within allowed directories).

    Returns:
        Matching file paths with a short surrounding snippet, or a message
        indicating no matches were found.
    """
    root = Path(path).resolve()

    # Basic path safety: refuse to search outside ATHOS_WORKSPACE
    workspace = os.environ.get("ATHOS_WORKSPACE", "")
    if workspace:
        try:
            root.relative_to(Path(workspace).resolve())
        except ValueError:
            return f"Error: path '{path}' is outside the allowed workspace."

    if not root.is_dir():
        return f"Error: '{path}' is not a directory."

    use_rg = _rg_available()
    hits = (
        _search_with_rg(root, pattern, _MAX_RESULTS)
        if use_rg
        else _search_python(root, pattern, _MAX_RESULTS)
    )

    if not hits:
        return f"No matches found for '{pattern}' under {path}"

    lines = [f"Found {len(hits)} file(s) matching '{pattern}':"]
    for rel, snippet in hits:
        lines.append(f"  {rel}")
        lines.append(f"    ...{snippet}...")
    if len(hits) == _MAX_RESULTS:
        lines.append(f"(results capped at {_MAX_RESULTS}; refine pattern if needed)")
    return "\n".join(lines)
