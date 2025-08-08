import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "rag_bm25", Path("src/athos/tools/rag_mcp/rag_bm25.py")
)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)
RAGBM25 = module.RAGBM25


def test_query_returns_relevant_chunk():
    docs = [
        ("doc1.md", "apple banana"),
        ("doc2.md", "banana orange"),
    ]
    rag = RAGBM25(docs)
    results = rag.query("apple", k=1)
    assert results
    path, text = results[0]
    assert path == "doc1.md"
    assert "apple" in text
