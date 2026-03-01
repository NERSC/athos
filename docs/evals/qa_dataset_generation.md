# ATHOS Q&A Dataset Generation Pipeline

Generates factual Q&A pairs from NERSC documentation for the ATHOS benchmark evaluation suite.

## Setup

Install dependencies:

```bash
pip install openai anthropic tiktoken beautifulsoup4 requests scikit-learn numpy tqdm
```

Set one API key (the script supports `--backend auto|cborg|anthropic|openai`):

```bash
# Option 1: CBORG (NERSC/LBNL)
export CBORG_API_KEY=your_cborg_key

# Option 2: Anthropic
export ANTHROPIC_API_KEY=your_anthropic_key

# Option 3: OpenAI
export OPENAI_API_KEY=your_openai_key
```

## Quick Start

```bash
# Auto-select backend from available keys (CBORG > Anthropic > OpenAI)
python3 scripts/generate_qa_dataset.py --backend auto --url https://docs.nersc.gov/systems/perlmutter/architecture/ --output qa_simple.jsonl

# Force OpenAI backend
python3 scripts/generate_qa_dataset.py --backend openai --url https://docs.nersc.gov/systems/perlmutter/architecture/ --output qa_simple.jsonl

# From a directory of markdown docs
python3 scripts/generate_qa_dataset.py --input-dir ./nersc_docs --output qa_simple.jsonl

# From a single file
python3 scripts/generate_qa_dataset.py --input-file perlmutter_guide.md --output qa_simple.jsonl

# From a live NERSC docs page
python3 scripts/generate_qa_dataset.py --url https://docs.nersc.gov/systems/perlmutter/architecture/ --output qa_simple.jsonl

# Test with just 5 chunks first
python3 scripts/generate_qa_dataset.py --input-dir ./nersc_docs --max-chunks 5 --output qa_test.jsonl

# Validate / get stats on an existing dataset
python3 scripts/generate_qa_dataset.py --validate qa_simple.deduped.jsonl
```

## Output Format

Each line in the `.jsonl` output is a JSON object:

```json
{
  "question": "What is the scratch quota per user on Perlmutter?",
  "answer": "Each user has a 20 TB scratch quota on Perlmutter.",
  "difficulty": "easy",
  "source_passage": "Each user is allocated 20 TB of scratch space...",
  "source_doc": "storage.md",
  "section": "Scratch Filesystem",
  "chunk_id": "a3f9c12d8b01",
  "qa_id": "7e2b4f91c083"
}
```

Two files are written:
- `qa_simple.jsonl` — raw output (one pair per line, written incrementally)
- `qa_simple.deduped.jsonl` — after near-duplicate removal (use this one)

## Recommended NERSC Doc Sources

### Public (priority first)
- `https://docs.nersc.gov/systems/perlmutter/` — architecture, storage, queues
- `https://docs.nersc.gov/jobs/` — job submission, policies
- `https://docs.nersc.gov/filesystems/` — quotas, purge policies, community FS
- `https://docs.nersc.gov/software/` — modules, Python, containers
- `https://docs.nersc.gov/accounts/` — allocations, user policies

### Internal (consulting docs)
- Export to markdown before processing
- Remove any PII or sensitive ticket content before generating

## Tips

- **Test first**: always run with `--max-chunks 5` before a full run to check output quality
- **Iterative**: the pipeline writes incrementally so you can kill and resume
- **Cost estimate**: ~600 tokens in + ~400 tokens out per chunk; at $3/MTok in and $15/MTok out, 200 chunks ≈ $0.50
- **Quality check**: after generation, review 10-15 examples manually, especially for "hard" difficulty pairs
- **Difficulty balance**: aim for ~50% easy, 30% medium, 20% hard across the full dataset

## Pipeline Steps

```
Docs → Section splitting → Token chunking (600 tok, 100 overlap)
     → Claude generation (3-6 Q&A per chunk)
     → Quality filtering (length, bad patterns)
     → TF-IDF deduplication (cosine > 0.92 removed)
     → JSONL output
```
