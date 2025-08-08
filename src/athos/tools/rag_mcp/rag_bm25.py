import math
import subprocess
from pathlib import Path
from typing import List, Tuple, Sequence, Dict


def _chunk_text(text: str, chunk_size: int = 200, overlap: int = 50) -> List[str]:
    """Split text into overlapping word chunks.

    Args:
        text: Input text.
        chunk_size: Number of words per chunk.
        overlap: Number of overlapping words between chunks.

    Returns:
        List of text chunks.
    """
    words = text.split()
    if not words:
        return []
    chunks = []
    step = max(chunk_size - overlap, 1)
    for i in range(0, len(words), step):
        chunk = " ".join(words[i : i + chunk_size])
        if chunk:
            chunks.append(chunk)
        if i + chunk_size >= len(words):
            break
    return chunks


class RAGBM25:
    """BM25 retrieval over Markdown documents."""

    def __init__(self, docs: Sequence[Tuple[str, str]]):
        self.docs = docs
        self.chunks: List[Tuple[str, str]] = []
        self.tokenized_chunks: List[List[str]] = []
        for path, text in docs:
            for chunk in _chunk_text(text):
                self.chunks.append((path, chunk))
                self.tokenized_chunks.append(chunk.lower().split())

        self.N = len(self.tokenized_chunks)
        self.avgdl = (
            sum(len(toks) for toks in self.tokenized_chunks) / self.N
            if self.N
            else 0
        )
        self.doc_freq: Dict[str, int] = {}
        for tokens in self.tokenized_chunks:
            for term in set(tokens):
                self.doc_freq[term] = self.doc_freq.get(term, 0) + 1
        self.k1 = 1.5
        self.b = 0.75

    @classmethod
    def from_repo(
        cls,
        repo_url: str,
        local_path: str,
    ) -> "RAGBM25":
        """Clone repo if needed and build index from Markdown files."""
        repo_dir = Path(local_path)
        if not repo_dir.exists():
            subprocess.run(["git", "clone", repo_url, str(repo_dir)], check=True)
        docs: List[Tuple[str, str]] = []
        for md_file in repo_dir.rglob("*.md"):
            try:
                text = md_file.read_text(encoding="utf-8")
                docs.append((str(md_file), text))
            except Exception:
                continue
        return cls(docs)

    def query(self, question: str, k: int = 5) -> List[Tuple[str, str]]:
        """Return top-k chunks for query."""
        if not self.tokenized_chunks:
            return []
        query_tokens = question.lower().split()
        scores: List[float] = []
        for doc_tokens in self.tokenized_chunks:
            score = 0.0
            doc_len = len(doc_tokens)
            for term in query_tokens:
                df = self.doc_freq.get(term)
                if not df:
                    continue
                idf = math.log(1 + (self.N - df + 0.5) / (df + 0.5))
                freq = doc_tokens.count(term)
                denom = freq + self.k1 * (1 - self.b + self.b * doc_len / self.avgdl)
                score += idf * (freq * (self.k1 + 1) / denom)
            scores.append(score)
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:k]
        return [self.chunks[i] for i, _ in ranked]
