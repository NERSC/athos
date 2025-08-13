from athos.tools.rag_mcp.rag_bm25 import RAGBM25


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
