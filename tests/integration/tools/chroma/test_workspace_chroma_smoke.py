from __future__ import annotations

import os
from pathlib import Path

import chromadb
import pytest


@pytest.mark.skipif(
    os.getenv("ATHOS_CHROMA_INTEGRATION") != "1",
    reason="Set ATHOS_CHROMA_INTEGRATION=1 to run workspace Chroma integration checks.",
)
def test_workspace_chroma_expected_collection_exists():
    """Smoke test against a real workspace Chroma DB.

    This is intentionally opt-in because it depends on local, persistent state.
    """

    workspace = Path(os.getenv("ATHOS_WORKSPACE", "/tmp/athos_workspace"))
    db_dir = workspace / "chroma"
    expected_collection = os.getenv("ATHOS_CHROMA_EXPECTED_COLLECTION", "nersc-docs")

    assert db_dir.exists(), f"Chroma DB directory does not exist: {db_dir}"

    client = chromadb.PersistentClient(path=str(db_dir))
    names = [c.name for c in client.list_collections()]
    assert expected_collection in names, (
        f"Expected collection '{expected_collection}' not found in {db_dir}. "
        f"Found collections: {names}"
    )

