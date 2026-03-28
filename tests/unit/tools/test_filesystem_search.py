"""Unit tests for the search_file_contents tool."""
import os
import pytest
from pathlib import Path


@pytest.fixture()
def corpus(tmp_path):
    """Small file tree for search tests."""
    (tmp_path / "a.md").write_text("step creation temporarily disabled\nother line\n")
    (tmp_path / "b.md").write_text("unrelated content here\n")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "c.md").write_text("STEP CREATION TEMPORARILY DISABLED (uppercase)\n")
    return tmp_path


def _invoke(pattern, path):
    from athos.tools.filesystem_search import search_file_contents
    return search_file_contents.invoke({"pattern": pattern, "path": str(path)})


def test_finds_matching_files(corpus):
    result = _invoke("step creation temporarily disabled", corpus)
    assert "a.md" in result
    assert "c.md" in result  # case-insensitive


def test_no_match_message(corpus):
    result = _invoke("xyzzy_no_match", corpus)
    assert "No matches found" in result


def test_case_insensitive(corpus):
    result = _invoke("STEP CREATION", corpus)
    assert "a.md" in result
    assert "c.md" in result


def test_excludes_non_matching_file(corpus):
    result = _invoke("step creation temporarily disabled", corpus)
    assert "b.md" not in result


def test_snippet_included(corpus):
    result = _invoke("step creation temporarily disabled", corpus)
    # Snippet should contain part of the matching line
    assert "disabled" in result.lower()


def test_non_directory_path(corpus):
    result = _invoke("anything", corpus / "a.md")
    assert "Error" in result
    assert "not a directory" in result


def test_path_outside_workspace(corpus, monkeypatch, tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    monkeypatch.setenv("ATHOS_WORKSPACE", str(workspace))
    # corpus is outside workspace
    result = _invoke("anything", corpus)
    assert "Error" in result
    assert "outside" in result
    assert "allowed bundle root" in result


def test_path_outside_bundle_root_rejected(monkeypatch, tmp_path):
    workspace = tmp_path / "workspace"
    bundle = workspace / "file_retrieval_corpus"
    bundle.mkdir(parents=True)
    outside_dir = workspace / "other"
    outside_dir.mkdir()
    (outside_dir / "note.md").write_text("step creation temporarily disabled\n")

    monkeypatch.setenv("ATHOS_WORKSPACE", str(workspace))

    result = _invoke("step creation temporarily disabled", outside_dir)
    assert "Error" in result
    assert "allowed bundle root" in result


def test_path_inside_bundle_root_allowed(monkeypatch, tmp_path):
    workspace = tmp_path / "workspace"
    bundle_docs = workspace / "file_retrieval_corpus" / "docs"
    bundle_docs.mkdir(parents=True)
    (bundle_docs / "policy.md").write_text("step creation temporarily disabled\n")

    monkeypatch.setenv("ATHOS_WORKSPACE", str(workspace))

    result = _invoke("step creation temporarily disabled", bundle_docs)
    assert "policy.md" in result


def test_no_workspace_env_allows_any_path(corpus, monkeypatch):
    monkeypatch.delenv("ATHOS_WORKSPACE", raising=False)
    result = _invoke("step creation temporarily disabled", corpus)
    assert "a.md" in result
