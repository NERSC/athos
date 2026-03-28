"""Unit tests for the configured search_file_contents tool factory."""

from pathlib import Path

import pytest

from athos.tools.filesystem_search import create_search_file_contents_tool


@pytest.fixture()
def workspace(tmp_path):
    workspace = tmp_path / "workspace"
    bundle_docs = workspace / "file_retrieval_corpus" / "docs"
    bundle_docs.mkdir(parents=True)
    (bundle_docs / "a.md").write_text("step creation temporarily disabled\nother line\n")
    (bundle_docs / "b.md").write_text("unrelated content here\n")
    sub = bundle_docs / "sub"
    sub.mkdir()
    (sub / "c.md").write_text("STEP CREATION TEMPORARILY DISABLED (uppercase)\n")
    outside = workspace / "other"
    outside.mkdir()
    (outside / "note.md").write_text("step creation temporarily disabled\n")
    return workspace


def _invoke(tool, pattern, path):
    return tool.invoke({"pattern": pattern, "path": str(path)})


def test_requires_non_empty_allowed_root():
    with pytest.raises(ValueError, match="non-empty allowed_root"):
        create_search_file_contents_tool(allowed_root="")


def test_finds_matching_files(workspace):
    docs = workspace / "file_retrieval_corpus" / "docs"
    tool = create_search_file_contents_tool(
        allowed_root=str(workspace / "file_retrieval_corpus")
    )
    result = _invoke(tool, "step creation temporarily disabled", docs)
    assert "a.md" in result
    assert "c.md" in result


def test_no_match_message(workspace):
    docs = workspace / "file_retrieval_corpus" / "docs"
    tool = create_search_file_contents_tool(
        allowed_root=str(workspace / "file_retrieval_corpus")
    )
    result = _invoke(tool, "xyzzy_no_match", docs)
    assert "No matches found" in result


def test_case_insensitive(workspace):
    docs = workspace / "file_retrieval_corpus" / "docs"
    tool = create_search_file_contents_tool(
        allowed_root=str(workspace / "file_retrieval_corpus")
    )
    result = _invoke(tool, "STEP CREATION", docs)
    assert "a.md" in result
    assert "c.md" in result


def test_excludes_non_matching_file(workspace):
    docs = workspace / "file_retrieval_corpus" / "docs"
    tool = create_search_file_contents_tool(
        allowed_root=str(workspace / "file_retrieval_corpus")
    )
    result = _invoke(tool, "step creation temporarily disabled", docs)
    assert "b.md" not in result


def test_snippet_included(workspace):
    docs = workspace / "file_retrieval_corpus" / "docs"
    tool = create_search_file_contents_tool(
        allowed_root=str(workspace / "file_retrieval_corpus")
    )
    result = _invoke(tool, "step creation temporarily disabled", docs)
    assert "disabled" in result.lower()


def test_non_directory_path(workspace):
    docs = workspace / "file_retrieval_corpus" / "docs"
    tool = create_search_file_contents_tool(
        allowed_root=str(workspace / "file_retrieval_corpus")
    )
    result = _invoke(tool, "anything", docs / "a.md")
    assert "Error" in result
    assert "not a directory" in result


def test_path_outside_bundle_root_rejected(workspace):
    outside = workspace / "other"
    tool = create_search_file_contents_tool(
        allowed_root=str(workspace / "file_retrieval_corpus")
    )
    result = _invoke(tool, "anything", outside)
    assert "Error" in result
    assert "allowed bundle root" in result


def test_path_inside_bundle_root_allowed(workspace):
    docs = workspace / "file_retrieval_corpus" / "docs"
    tool = create_search_file_contents_tool(
        allowed_root=str(workspace / "file_retrieval_corpus")
    )
    result = _invoke(tool, "step creation temporarily disabled", docs)
    assert "a.md" in result
