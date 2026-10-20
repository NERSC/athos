# Derived Ticket Corpus Pipeline

This documents the current derived-ticket retrieval pipeline.

## Outputs

The derived pipeline now produces two complementary retrieval surfaces:

1. Batch artifact: one JSON object per ticket in a single JSONL file
2. File-search artifact: one Markdown file per ticket in a sharded directory tree

The JSONL file is the canonical batch artifact for:

- reproducible corpus generation
- downstream Chroma ingestion
- audits and reruns

The materialized Markdown directory is the recommended surface for filesystem
tooling and bundle-backed file retrieval.

## Why not use one giant JSONL for filesystem retrieval?

The filesystem surface used in ATHOS is read-oriented but coarse-grained:

- file search
- file read
- directory listing

It does not provide line-range seeking into a large file. That makes a single
multi-thousand-record JSONL awkward for agentic file search:

- a file search can find a hit, but
- a file read may then need to read the entire large file, and
- the agent has no natural per-record unit to inspect

For that reason, the derived pipeline can now also materialize one Markdown file
per ticket. This preserves the canonical JSONL while giving the filesystem agent
a narrow, searchable, readable artifact shape.

## Build the Derived Corpus

Example pilot or full run:

```bash
python scripts/build_derived_ticket_corpus.py \
  --selected-corpus-manifest data/manifests/servicenow_tickets_balanced_v0_20260306_retrieval_lt_20250901_filter.json \
  --output-jsonl data/derived_ticket_corpus/derived_ticket_retrieval_lt_20250901_v2.jsonl \
  --materialize-dir data/derived_ticket_corpus/derived_ticket_retrieval_lt_20250901_v2_files \
  --model cborg_coder \
  --allow-transform-errors -v
```

Primary outputs:

- `derived_ticket_retrieval_lt_20250901_v2.jsonl`
- `derived_ticket_retrieval_lt_20250901_v2.jsonl.manifest.json`
- `derived_ticket_retrieval_lt_20250901_v2.jsonl.failures.jsonl`
- `derived_ticket_retrieval_lt_20250901_v2_files/INDEX.md`
- `derived_ticket_retrieval_lt_20250901_v2_files/manifest.json`
- one Markdown file per incident under `derived_ticket_retrieval_lt_20250901_v2_files/`

## Build Chroma from the Derived Corpus

The Chroma builder now accepts either raw selected-ticket manifests or derived
JSONL directly.

Example:

```bash
python scripts/build_tickets_chroma.py \
  --derived-jsonl data/derived_ticket_corpus/derived_ticket_retrieval_lt_20250901_v2.jsonl \
  --persist-dir data/chroma/derived_ticket_retrieval_lt_20250901_v2 \
  --collection-name tickets_derived_retrieval_lt_20250901_v2
```

The derived Chroma surface renders deterministic retrieval text from the
structured fields at ingest time. The JSONL remains structured-only and does
not need to store a duplicated rendered text field.

## Use in the Filesystem Bundle

For bundle-backed filesystem retrieval, point `--fs-tickets-dir` at the
materialized Markdown directory rather than raw ticket JSON:

```bash
python scripts/build_workspace.py \
  --workspace-dir workspace \
  --fs-docs-dir data/docs/docs \
  --fs-consulting-docs-dir data/consulting_docs/docs \
  --fs-tickets-dir data/derived_ticket_corpus/derived_ticket_retrieval_lt_20250901_v2_files \
  --fs-include-tickets \
  --build-fs-index
```

This keeps the filesystem agent’s ticket surface:

- compact
- one-record-per-file
- readable without JSON parsing
- narrow enough for generic file-search and file-read workflows

## Current Status

- Canonical paper-facing retrieval cutoff is `lt_2025-09-01` and the corrected
  derived retrieval corpus matches the original retrieval split exactly
  (`7187` tickets).
- Chroma ingestion from derived JSONL is implemented and validated.
- Materialized per-ticket Markdown output is implemented for filesystem use.
- Deterministic text-attachment extraction has been exercised on targeted tickets
  with `.txt` and `.log` attachments, and also appeared in the broader corpus
  build.
- The derived corpus is now available both as a ticket-only Chroma DB and inside
  an aggregate DB with `docs`, `consulting_docs`, and derived `tickets`.
