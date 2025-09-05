"""Utilities for ingesting markdown documentation into a ChromaDB collection."""
from __future__ import annotations

from pathlib import Path
from datetime import datetime
import logging
import re
from typing import List, Tuple


logger = logging.getLogger(__name__)


def parse_title(text: str) -> str:
    """Return the first H1 title in the document if present."""
    match = re.search(r"^#\s+(.*)", text, flags=re.MULTILINE)
    return match.group(1).strip() if match else ""


def chunk_markdown(text: str, chunk_size: int = 15000) -> List[Tuple[str, str]]:
    """Chunk a markdown document.

    If the document exceeds ``chunk_size`` characters, split it by H2 headings.
    For documents without H2 headings, fall back to simple length based chunks.

    Returns a list of tuples ``(chunk_title, chunk_text)``.
    """
    logger.debug("Chunking markdown of length %d with chunk size %d", len(text), chunk_size)
    if len(text) <= chunk_size:
        logger.debug("Document within chunk size; returning full text")
        return [("full", text)]

    # Split by H2 headings
    lines = text.splitlines()
    chunks: List[Tuple[str, str]] = []
    current_title = "intro"
    current_lines: List[str] = []

    for line in lines:
        if line.startswith("## "):
            if current_lines:
                chunks.append((current_title, "\n".join(current_lines).strip()))
                logger.debug("Added chunk titled '%s'", current_title)
            current_title = line[3:].strip()
            current_lines = [line]
        else:
            current_lines.append(line)

    if current_lines:
        chunks.append((current_title, "\n".join(current_lines).strip()))
        logger.debug("Added chunk titled '%s'", current_title)

    if len(chunks) == 1:  # no H2 headings, fallback to size-based chunks
        text = chunks[0][1]
        chunks = []
        for i in range(0, len(text), chunk_size):
            part = text[i : i + chunk_size]
            title = f"part_{i//chunk_size}"
            chunks.append((title, part))
            logger.debug("Added fallback chunk '%s'", title)

    logger.debug("Produced %d chunks", len(chunks))
    return [c for c in chunks if c[1]]


def build_collection(
    docs_path: Path,
    persist_dir: Path,
    collection_name: str,
    chunk_size: int = 15000,
) -> None:
    """Ingest markdown files under ``docs_path`` into a ChromaDB collection."""
    import chromadb
    from chromadb.utils import embedding_functions

    logger.info(
        "Building collection '%s' from docs at '%s'", collection_name, docs_path
    )
    client = chromadb.PersistentClient(path=str(persist_dir))
    embed_fn = embedding_functions.DefaultEmbeddingFunction()
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={
            "source": str(Path(docs_path).resolve()),
            "created": datetime.utcnow().isoformat(),
        },
        embedding_function=embed_fn,
    )

    files = sorted(Path(docs_path).rglob("*.md"))
    logger.debug("Found %d markdown files", len(files))
    for file in files:
        logger.info("Processing %s", file)
        text = file.read_text(encoding="utf-8")
        title = parse_title(text) or file.stem
        last_modified = datetime.fromtimestamp(file.stat().st_mtime).isoformat()
        rel_path = file.relative_to(docs_path)
        section = rel_path.parts[0] if len(rel_path.parts) > 1 else ""

        chunks = chunk_markdown(text, chunk_size)
        for idx, (chunk_title, chunk_text) in enumerate(chunks):
            doc_id = f"{rel_path.as_posix()}_{idx}"
            metadata = {
                "file_path": rel_path.as_posix(),
                "title": title,
                "section": section,
                "chunk_index": idx,
                "chunk_title": chunk_title,
                "last_modified": last_modified,
            }
            logger.debug("Adding chunk %s", doc_id)
            collection.add(ids=[doc_id], documents=[chunk_text], metadatas=[metadata])

    logger.info(
        "Ingested %d documents into collection '%s' at '%s'",
        collection.count(),
        collection_name,
        persist_dir,
    )
