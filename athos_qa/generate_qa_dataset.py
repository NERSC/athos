#!/usr/bin/env python3
"""
ATHOS Q&A Dataset Generation Pipeline
======================================
Generates factual Q&A pairs from NERSC documentation for use in
ATHOS benchmark evaluation datasets.

Uses CBORG (LBNL's internal LLM gateway) by default at NERSC/LBNL, and can
also use Anthropic or OpenAI directly.

Usage:
    # Test with 5 chunks first (recommended)
    python generate_qa_dataset.py --url https://docs.nersc.gov/filesystems/ --max-chunks 5 --output qa_test.jsonl

    # Full run from a URL
    python generate_qa_dataset.py --url https://docs.nersc.gov/filesystems/ --output qa_dataset.jsonl

    # From a directory of markdown/text files
    python generate_qa_dataset.py --input-dir ./docs --output qa_dataset.jsonl

    # From a single file
    python generate_qa_dataset.py --input-file userguide.md --output qa_dataset.jsonl

    # Validate / report stats on an existing dataset
    python generate_qa_dataset.py --validate qa_dataset.jsonl

    # Use Anthropic API directly
    python generate_qa_dataset.py --backend anthropic --url https://docs.nersc.gov/filesystems/ --output qa_dataset.jsonl

    # Use OpenAI API directly
    python generate_qa_dataset.py --backend openai --url https://docs.nersc.gov/filesystems/ --output qa_dataset.jsonl

Setup (CBORG - recommended at NERSC/LBNL):
    export CBORG_API_KEY=your_cborg_key   # from https://api.cborg.lbl.gov
    pip install --user openai tiktoken beautifulsoup4 requests scikit-learn numpy tqdm

Setup (Anthropic direct - fallback):
    export ANTHROPIC_API_KEY=sk-ant-...
    pip install --user anthropic tiktoken beautifulsoup4 requests scikit-learn numpy tqdm

Setup (OpenAI direct - fallback):
    export OPENAI_API_KEY=sk-...
    pip install --user openai tiktoken beautifulsoup4 requests scikit-learn numpy tqdm
"""

import os
import re
import json
import sys
import time
import hashlib
import argparse
import logging
from pathlib import Path
from dataclasses import dataclass, asdict, fields
from typing import Any

import tiktoken
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# CBORG (default - works at NERSC/LBNL without a personal Anthropic key)
CBORG_BASE_URL = "https://api.cborg.lbl.gov"
CBORG_MODEL    = "anthropic/claude-sonnet"   # swap to "lbl/cborg-coder-v3" for open-weight

# Anthropic direct (fallback)
ANTHROPIC_MODEL = "claude-sonnet-4-6"

# OpenAI direct (fallback)
OPENAI_MODEL = "gpt-4o-mini"

MAX_TOKENS_OUT             = 2048   # max tokens per generation call
CHUNK_SIZE_TOKENS          = 600    # target tokens per chunk
CHUNK_OVERLAP_TOKENS       = 100    # overlap between chunks
MIN_CHUNK_TOKENS           = 80     # discard chunks smaller than this
MAX_RETRIES                = 3      # API retry attempts
RETRY_DELAY                = 5      # seconds between retries
DEDUP_SIMILARITY_THRESHOLD = 0.92   # cosine similarity threshold for dedup

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class DocChunk:
    text: str
    source_doc: str
    section: str
    chunk_id: str  # hash of text

@dataclass
class QAPair:
    question: str
    answer: str
    difficulty: str       # easy | medium | hard
    source_passage: str
    source_doc: str
    section: str
    chunk_id: str
    qa_id: str            # hash of question


QA_PAIR_FIELDS = {f.name for f in fields(QAPair)}

LOCAL_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in",
    "is", "it", "of", "on", "or", "that", "the", "to", "with", "you", "your",
}


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

PROMPT_TEMPLATE = """You are an expert technical writer helping build an evaluation dataset for AI systems that assist HPC (High-Performance Computing) operations and user support at NERSC (National Energy Research Scientific Computing Center).

Your task is to generate factual question-and-answer pairs from a provided documentation passage. These Q&A pairs will be used to benchmark agentic AI systems on realistic HPC support tasks.

Given the documentation passage below, generate between 3 and 6 Q&A pairs following these rules:

**Question rules:**
- Ask about specific, verifiable facts directly stated in the passage (e.g., limits, names, paths, commands, policies, deadlines)
- Write questions as a user or operator would naturally ask them -- not "According to the passage..." phrasing
- Vary the question style: some should be direct lookups, some should be task-oriented
- Avoid questions whose answers require information outside the passage
- Avoid yes/no questions unless they test a genuinely important fact

**Answer rules:**
- Answers must be short and verifiable -- ideally 1-2 sentences, never more than 3
- Answers must be directly supported by the passage -- do not infer or extrapolate
- Include specific values, paths, commands, or policy language where relevant

**Difficulty levels:**
- easy: direct single-fact lookup
- medium: requires synthesizing 2 facts or understanding a policy
- hard: requires understanding a workflow or tradeoff

Return a JSON array only -- no preamble, no markdown fences, no explanation outside the JSON.

[
  {{
    "question": "...",
    "answer": "...",
    "difficulty": "easy" | "medium" | "hard",
    "source_passage": "REQUIRED: exact verbatim quote from the passage (10-80 words) that directly supports this answer. Must be non-empty."
  }},
  ...
]

Documentation passage:
---
{passage}
---
Source document: {source_doc}
Section: {section}
"""


# ---------------------------------------------------------------------------
# LLM client factory
# ---------------------------------------------------------------------------

def resolve_backend(backend: str) -> str:
    """Resolve backend selection, including auto mode from available API keys."""
    if backend != "auto":
        return backend

    if os.environ.get("CBORG_API_KEY"):
        return "cborg"
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "anthropic"
    if os.environ.get("OPENAI_API_KEY"):
        return "openai"

    log.warning(
        "No API key found for --backend auto. Falling back to local backend."
    )
    return "local"


def _extract_passage_from_prompt(prompt: str) -> str:
    m = re.search(
        r"Documentation passage:\s*---\s*(.*?)\s*---\s*Source document:",
        prompt,
        flags=re.DOTALL,
    )
    return (m.group(1) if m else prompt).strip()


def _pick_topic(sentence: str) -> str:
    words = re.findall(r"[A-Za-z0-9_/$.-]+", sentence)
    filtered = [w for w in words if w.lower() not in LOCAL_STOPWORDS and len(w) > 2]
    if not filtered:
        filtered = words
    topic = " ".join(filtered[:6]).strip()
    return topic or "this topic"


def _score_sentence(sentence: str) -> tuple[int, str]:
    score = 0
    if re.search(r"\d", sentence):
        score += 2
    if re.search(r"/|--|\\$|[A-Z]{2,}", sentence):
        score += 2
    if len(sentence.split()) >= 10:
        score += 1
    if ":" in sentence:
        score += 1
    clean = " ".join(sentence.split())
    return score, clean


def _local_generate_pairs(prompt: str) -> list[dict[str, Any]]:
    passage = _extract_passage_from_prompt(prompt)
    raw_parts = re.split(r"(?<=[.!?])\s+|\n+", passage)
    candidates = []
    seen = set()
    for part in raw_parts:
        sentence = part.strip()
        if len(sentence.split()) < 8:
            continue
        score, clean = _score_sentence(sentence)
        if not clean:
            continue
        key = clean.lower()
        if key in seen:
            continue
        seen.add(key)
        candidates.append((score, clean))

    candidates.sort(key=lambda x: x[0], reverse=True)
    selected = [text for _, text in candidates[:4]]
    if not selected and passage:
        selected = [" ".join(passage.split()[:30]).strip()]

    pairs = []
    for idx, sent in enumerate(selected):
        topic = _pick_topic(sent)
        words = sent.split()
        answer = " ".join(words[:45]).strip()
        if len(answer.split()) < 3:
            continue
        if len(answer.split()) > 80:
            answer = " ".join(answer.split()[:80])

        difficulty = "easy"
        if len(words) >= 24:
            difficulty = "hard"
        elif len(words) >= 14:
            difficulty = "medium"

        question = f"What does NERSC documentation say about {topic}?"
        if idx == 1:
            question = f"How is {topic} described in NERSC docs?"
        elif idx == 2:
            question = f"What details are provided for {topic}?"
        elif idx == 3:
            question = f"For operators, what should be known about {topic}?"

        pairs.append(
            {
                "question": question,
                "answer": answer,
                "difficulty": difficulty,
                "source_passage": sent,
            }
        )

    return pairs


def make_client(backend: str):
    """Return a callable: prompt_str -> response_str"""
    backend = resolve_backend(backend)

    if backend == "cborg":
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "openai package required for CBORG backend.\n"
                "Run: pip install --user openai"
            )

        api_key = os.environ.get("CBORG_API_KEY")
        if not api_key:
            raise ValueError(
                "CBORG_API_KEY not set.\n"
                "Get your key from https://api.cborg.lbl.gov then run:\n"
                "  export CBORG_API_KEY=your_key"
            )

        client = OpenAI(base_url=CBORG_BASE_URL, api_key=api_key)
        log.info(f"Using CBORG backend: {CBORG_BASE_URL}  model={CBORG_MODEL}")

        def call(prompt: str) -> str:
            response = client.chat.completions.create(
                model=CBORG_MODEL,
                max_tokens=MAX_TOKENS_OUT,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content

        return call

    elif backend == "anthropic":
        try:
            import anthropic as _anthropic
        except ImportError:
            raise ImportError(
                "anthropic package required for Anthropic backend.\n"
                "Run: pip install --user anthropic"
            )

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not set.\n"
                "export ANTHROPIC_API_KEY=sk-ant-..."
            )

        client = _anthropic.Anthropic(api_key=api_key)
        log.info(f"Using Anthropic backend, model={ANTHROPIC_MODEL}")

        def call(prompt: str) -> str:
            response = client.messages.create(
                model=ANTHROPIC_MODEL,
                max_tokens=MAX_TOKENS_OUT,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text

        return call

    elif backend == "openai":
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "openai package required for OpenAI backend.\n"
                "Run: pip install --user openai"
            )

        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY not set.\n"
                "export OPENAI_API_KEY=sk-..."
            )

        client = OpenAI(api_key=api_key)
        log.info(f"Using OpenAI backend, model={OPENAI_MODEL}")

        def call(prompt: str) -> str:
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                max_tokens=MAX_TOKENS_OUT,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content or ""

        return call

    elif backend == "local":
        log.info("Using local backend (extractive heuristic generator)")

        def call(prompt: str) -> str:
            pairs = _local_generate_pairs(prompt)
            return json.dumps(pairs)

        return call

    else:
        raise ValueError(
            f"Unknown backend '{backend}'. Choose 'auto', 'cborg', 'anthropic', 'openai', or 'local'."
        )


# ---------------------------------------------------------------------------
# Document loading
# ---------------------------------------------------------------------------

def load_markdown_file(path: Path) -> list[dict]:
    """Load a markdown file, splitting by headings into sections."""
    text = path.read_text(encoding="utf-8", errors="ignore")
    sections = re.split(r"\n(?=#{1,3} )", text)
    results = []
    for sec in sections:
        lines = sec.strip().splitlines()
        if not lines:
            continue
        heading = lines[0].lstrip("#").strip() if lines[0].startswith("#") else "Introduction"
        body = "\n".join(lines[1:]).strip()
        if body:
            results.append({"section": heading, "text": body, "source_doc": path.name})
    return results


def load_text_file(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    return [{"section": "Document", "text": text, "source_doc": path.name}]


def load_url(url: str) -> list[dict]:
    """Fetch a NERSC docs page and extract text sections."""
    log.info(f"Fetching {url}")
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    for tag in soup(["nav", "footer", "script", "style"]):
        tag.decompose()

    results = []
    main = soup.find("main") or soup.find("article") or soup.body
    current_section = "Introduction"
    current_text = []

    for elem in main.find_all(["h1", "h2", "h3", "p", "li", "pre", "code"]):
        if elem.name in ("h1", "h2", "h3"):
            if current_text:
                results.append({
                    "section": current_section,
                    "text": "\n".join(current_text).strip(),
                    "source_doc": url,
                })
                current_text = []
            current_section = elem.get_text(strip=True)
        else:
            t = elem.get_text(strip=True)
            if t:
                current_text.append(t)

    if current_text:
        results.append({
            "section": current_section,
            "text": "\n".join(current_text).strip(),
            "source_doc": url,
        })

    return results


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

def chunk_section(section: dict, enc) -> list[DocChunk]:
    """Split a section into overlapping token-bounded chunks."""
    tokens = enc.encode(section["text"])
    chunks = []
    start = 0
    while start < len(tokens):
        end = min(start + CHUNK_SIZE_TOKENS, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text = enc.decode(chunk_tokens)

        if len(chunk_tokens) >= MIN_CHUNK_TOKENS:
            chunk_id = hashlib.sha256(chunk_text.encode()).hexdigest()[:12]
            chunks.append(DocChunk(
                text=chunk_text,
                source_doc=section["source_doc"],
                section=section["section"],
                chunk_id=chunk_id,
            ))

        if end == len(tokens):
            break
        start = end - CHUNK_OVERLAP_TOKENS

    return chunks


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def generate_qa_for_chunk(chunk: DocChunk, llm_call) -> list[QAPair]:
    """Call the LLM to generate Q&A pairs for one chunk."""
    prompt = PROMPT_TEMPLATE.format(
        passage=chunk.text,
        source_doc=chunk.source_doc,
        section=chunk.section,
    )

    for attempt in range(MAX_RETRIES):
        try:
            raw = llm_call(prompt).strip()

            # Strip accidental markdown fences
            raw = re.sub(r"^```(?:json)?", "", raw).strip()
            raw = re.sub(r"```$", "", raw).strip()

            pairs_raw = json.loads(raw)
            pairs = []
            missing_passages = []
            for p in pairs_raw:
                source_passage = p.get("source_passage", "").strip()
                if not source_passage:
                    missing_passages.append(p.get("question", "<no question>"))
                    continue  # drop pairs without source_passage
                qa_id = hashlib.sha256(p["question"].encode()).hexdigest()[:12]
                pairs.append(QAPair(
                    question=p["question"],
                    answer=p["answer"],
                    difficulty=p.get("difficulty", "easy"),
                    source_passage=source_passage,
                    source_doc=chunk.source_doc,
                    section=chunk.section,
                    chunk_id=chunk.chunk_id,
                    qa_id=qa_id,
                ))

            if missing_passages:
                log.warning(
                    f"Attempt {attempt+1}: {len(missing_passages)} pair(s) had empty "
                    f"source_passage and were dropped: {missing_passages}"
                )
                # If ALL pairs were dropped due to missing passages, retry
                if not pairs:
                    log.warning(
                        f"All pairs missing source_passage on attempt {attempt+1}, retrying..."
                    )
                    time.sleep(RETRY_DELAY)
                    continue

            return pairs

        except json.JSONDecodeError as e:
            log.warning(f"JSON parse error on attempt {attempt+1}: {e}")
        except Exception as e:
            log.warning(f"API error on attempt {attempt+1}: {e}")
            time.sleep(RETRY_DELAY)

    log.error(f"Failed to generate Q&A for chunk {chunk.chunk_id} after {MAX_RETRIES} attempts")
    return []


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------

def deduplicate(pairs: list[QAPair]) -> list[QAPair]:
    """Remove near-duplicate questions using TF-IDF cosine similarity."""
    if len(pairs) < 2:
        return pairs

    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        questions = [p.question for p in pairs]
        tfidf = TfidfVectorizer().fit_transform(questions)
        sim = cosine_similarity(tfidf)

        keep = []
        removed = set()
        for i in range(len(pairs)):
            if i in removed:
                continue
            keep.append(pairs[i])
            for j in range(i + 1, len(pairs)):
                if sim[i, j] >= DEDUP_SIMILARITY_THRESHOLD:
                    removed.add(j)

        log.info(f"Deduplication: {len(pairs)} -> {len(keep)} pairs ({len(removed)} removed)")
        return keep

    except ImportError:
        log.warning("scikit-learn not available, skipping deduplication")
        return pairs


# ---------------------------------------------------------------------------
# Validation / quality filters
# ---------------------------------------------------------------------------

BAD_QUESTION_PATTERNS = [
    r"according to (the )?(passage|text|document)",
    r"^(is|are|does|do|can|will|has|have) .+\?$",  # simple yes/no
    r"the passage (says|states|mentions)",
]

def is_valid_pair(qa: QAPair) -> bool:
    q = qa.question.lower()
    a = qa.answer.lower()

    if len(qa.question.split()) < 4:
        return False
    if len(qa.answer.split()) < 3:
        return False
    if len(qa.answer.split()) > 80:
        return False
    # source_passage must be present and substantive (at least 5 words)
    if not qa.source_passage or len(qa.source_passage.split()) < 5:
        return False
    for pat in BAD_QUESTION_PATTERNS:
        if re.search(pat, q):
            return False
    if "the passage" in a or "the text" in a:
        return False

    return True


def validate_dataset(path: Path) -> dict:
    """Print stats and flag issues in an existing dataset file."""
    pairs = []
    parse_errors = 0
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    payload = json.loads(line)
                    if not isinstance(payload, dict):
                        parse_errors += 1
                        continue

                    # Keep validator compatible with legacy rows containing extra keys.
                    clean = {k: v for k, v in payload.items() if k in QA_PAIR_FIELDS}
                    if "chunk_id" not in clean:
                        source_passage = clean.get("source_passage", "")
                        clean["chunk_id"] = hashlib.md5(source_passage.encode("utf-8")).hexdigest()[:12]
                    if "qa_id" not in clean:
                        question = clean.get("question", "")
                        clean["qa_id"] = hashlib.md5(question.encode("utf-8")).hexdigest()[:12]

                    pairs.append(QAPair(**clean))
                except Exception:
                    parse_errors += 1

    total = len(pairs)
    print(f"\n=== Dataset Validation Report ===")
    print(f"Total pairs:   {total}")
    print(f"Parse errors:  {parse_errors}")
    if total == 0:
        print("No pairs found — check your API key and input source.")
        return {"total": 0, "valid": 0, "filtered_out": 0, "parse_errors": parse_errors}

    valid = [p for p in pairs if is_valid_pair(p)]
    print(f"Valid pairs:   {len(valid)} ({100*len(valid)//total}%)")
    print(f"Filtered out:  {total - len(valid)}")

    empty_passages = [p for p in pairs if not p.source_passage or len(p.source_passage.split()) < 5]
    if empty_passages:
        print(f"Empty/short source_passage: {len(empty_passages)} pair(s) <- PROBLEM")
        for p in empty_passages[:3]:
            print(f"  - {p.question[:70]}")
    else:
        print(f"Empty/short source_passage: 0 ✓")

    difficulty_counts = {}
    for p in valid:
        difficulty_counts[p.difficulty] = difficulty_counts.get(p.difficulty, 0) + 1

    print(f"\nDifficulty distribution:")
    for d, c in sorted(difficulty_counts.items()):
        pct = 100 * c // len(valid) if valid else 0
        print(f"  {d:8s}: {c:4d} ({pct}%)")

    docs = {}
    for p in valid:
        docs[p.source_doc] = docs.get(p.source_doc, 0) + 1
    print(f"\nBy source document:")
    for doc, count in sorted(docs.items(), key=lambda x: -x[1]):
        print(f"  {count:4d}  {doc}")

    return {
        "total": total,
        "valid": len(valid),
        "filtered_out": total - len(valid),
        "parse_errors": parse_errors,
    }


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run_pipeline(args):
    llm_call = make_client(args.backend)
    enc = tiktoken.get_encoding("cl100k_base")

    # 1. Load sections
    sections = []
    if args.input_dir:
        doc_dir = Path(args.input_dir)
        for ext in ["*.md", "*.txt", "*.rst"]:
            for f in doc_dir.rglob(ext):
                log.info(f"Loading {f}")
                sections.extend(load_markdown_file(f) if f.suffix == ".md" else load_text_file(f))
    elif args.input_file:
        f = Path(args.input_file)
        sections.extend(load_markdown_file(f) if f.suffix == ".md" else load_text_file(f))
    elif args.url:
        sections.extend(load_url(args.url))
    else:
        raise ValueError("Provide --input-dir, --input-file, or --url")

    log.info(f"Loaded {len(sections)} sections")

    # 2. Chunk
    all_chunks = []
    for sec in sections:
        all_chunks.extend(chunk_section(sec, enc))
    log.info(f"Created {len(all_chunks)} chunks")

    if args.max_chunks:
        all_chunks = all_chunks[:args.max_chunks]
        log.info(f"Limited to {len(all_chunks)} chunks (--max-chunks)")

    # 3. Generate Q&A (writes incrementally so you don't lose work on crash)
    all_pairs = []
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as out_f:
        for chunk in tqdm(all_chunks, desc="Generating Q&A"):
            pairs = generate_qa_for_chunk(chunk, llm_call)
            valid_pairs = [p for p in pairs if is_valid_pair(p)]
            all_pairs.extend(valid_pairs)

            for p in valid_pairs:
                out_f.write(json.dumps(asdict(p)) + "\n")
                out_f.flush()

            time.sleep(0.3)  # be polite to the API

    log.info(f"Generated {len(all_pairs)} valid Q&A pairs before dedup")

    # 4. Deduplicate
    deduped = deduplicate(all_pairs)

    deduped_path = output_path.with_suffix(".deduped.jsonl")
    output_suffix = output_path.suffix if output_path.suffix else ".jsonl"
    eval_ready_path = (
        Path(args.eval_output)
        if args.eval_output
        else output_path.with_name(f"qa_eval_ready_{output_path.stem}{output_suffix}")
    )

    with open(deduped_path, "w") as f:
        for p in deduped:
            f.write(json.dumps(asdict(p)) + "\n")

    with open(eval_ready_path, "w") as f:
        for p in deduped:
            f.write(json.dumps(asdict(p)) + "\n")

    log.info(f"Intermediate raw dataset: {len(all_pairs)} pairs -> {output_path}")
    log.info(f"Intermediate deduped dataset: {len(deduped)} pairs -> {deduped_path}")
    log.info(f"Eval-ready dataset: {len(deduped)} pairs -> {eval_ready_path}")

    # 5. Summary
    stats = validate_dataset(eval_ready_path)
    if stats["total"] == 0:
        raise RuntimeError("Validation failed: generated dataset is empty.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="ATHOS Q&A Dataset Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    source_group = parser.add_mutually_exclusive_group()
    source_group.add_argument("--input-dir",  help="Directory of .md/.txt docs to process")
    source_group.add_argument("--input-file", help="Single doc file to process")
    source_group.add_argument("--url",        help="URL to fetch and process")
    source_group.add_argument("--validate",   metavar="JSONL_PATH",
                              help="Validate and report stats on an existing dataset")

    parser.add_argument("--output",     default="qa_dataset.jsonl",
                        help="Output JSONL file (default: qa_dataset.jsonl)")
    parser.add_argument("--eval-output", default=None,
                        help="Optional explicit eval-ready output path. "
                             "Default: qa_eval_ready_<output_stem>.jsonl")
    parser.add_argument("--max-chunks", type=int, default=None,
                        help="Limit number of chunks processed (useful for testing)")
    parser.add_argument("--backend",    choices=["auto", "cborg", "anthropic", "openai", "local"], default="auto",
                        help="LLM backend to use (default: auto)")
    parser.add_argument("--model",      default=None,
                        help="Override the model name (e.g. 'lbl/cborg-coder-v3' for open-weight via CBORG)")

    args = parser.parse_args()

    # Allow model override
    if args.model:
        global CBORG_MODEL, ANTHROPIC_MODEL, OPENAI_MODEL
        if args.backend == "cborg":
            CBORG_MODEL = args.model
        elif args.backend == "anthropic":
            ANTHROPIC_MODEL = args.model
        elif args.backend == "openai":
            OPENAI_MODEL = args.model
        else:
            log.warning(
                "--model was provided with --backend auto. "
                "Set --backend explicitly if you want model override to apply."
            )

    if args.validate:
        stats = validate_dataset(Path(args.validate))
        if stats["total"] == 0:
            sys.exit(1)
    else:
        if not (args.input_dir or args.input_file or args.url):
            parser.error("Provide one of: --input-dir, --input-file, --url, or --validate")
        run_pipeline(args)


if __name__ == "__main__":
    main()
