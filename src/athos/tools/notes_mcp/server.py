"""FastMCP server exposing the note tools of athos.tools.note_taker.

It serves note_taker, list_notes and read_note unchanged, with the same
arguments, checks and replies, so the Slack bot reads their results as
before. With --read-only it serves only list_notes and read_note.

Run it over stdio (`python -m athos.tools.notes_mcp`). LangGraph flows open a
new MCP session for every tool call, so each call is a fresh process that
sees every note saved before it; note_taker's file lock keeps overlapping
calls from touching the database at once.

A stdio server inherits only a few environment variables (HOME, PATH, ...),
so pass the notes location with --notes-dir or --chroma-dir.
"""

from __future__ import annotations

import argparse
import os

from fastmcp import FastMCP

from athos.tools import note_taker as notes


def build_server(*, read_only: bool = False) -> FastMCP:
    """A FastMCP server with the note tools; only the read tools when read_only."""
    mcp = FastMCP("Notes")
    tools = [notes.list_notes, notes.read_note]
    if not read_only:
        tools.append(notes.note_taker)
    for note_tool in tools:
        mcp.tool(note_tool.func)
    return mcp


def main() -> None:
    parser = argparse.ArgumentParser(description="Saved consulting notes MCP server")
    parser.add_argument(
        "--notes-dir",
        help="Notes directory; the database is <notes dir>/chroma (sets ATHOS_NOTES_DIR)",
    )
    parser.add_argument(
        "--chroma-dir",
        help="Chroma database directory, overriding <notes dir>/chroma (sets ATHOS_NOTES_CHROMA_DIR)",
    )
    parser.add_argument(
        "--read-only",
        action="store_true",
        help="Serve only list_notes and read_note",
    )
    args = parser.parse_args()
    if args.notes_dir:
        os.environ["ATHOS_NOTES_DIR"] = os.path.abspath(args.notes_dir)
    if args.chroma_dir:
        os.environ["ATHOS_NOTES_CHROMA_DIR"] = os.path.abspath(args.chroma_dir)
    build_server(read_only=args.read_only).run(show_banner=False)
