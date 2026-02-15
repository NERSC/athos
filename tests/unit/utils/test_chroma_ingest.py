from athos.utils.chroma_ingest import chunk_markdown


def test_chunk_markdown_split_by_h2():
    text = """# Title

Intro text
## Section One
Content one
## Section Two
Content two"""
    chunks = chunk_markdown(text, chunk_size=20)
    titles = [t for t, _ in chunks]
    assert titles[0] == "intro"
    assert titles[1] == "Section One"
    assert titles[2] == "Section Two"
    assert len(chunks) == 3
