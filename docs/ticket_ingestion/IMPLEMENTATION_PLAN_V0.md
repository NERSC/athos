# Ticket Ingestion Implementation Plan v0

## Objective

Implement a layered ServiceNow ticket ingestion pipeline for Chroma that:

- starts with a minimal, reliable baseline
- supports configurable filtering (recency, contact type, etc.)
- preserves reproducibility/versioning for future rebuilds

Primary scope for v0: Layer 1 baseline + filtering + manifest + basic validation.

## Scope

In scope:

- Ingest incident JSON records into one Chroma collection
- Normalize incident text for retrieval
- Apply configurable filters from `FILTER_POLICY_V0.md`
- Enforce text caps and chunk fallback
- Emit run manifest with reproducibility metadata

Out of scope (v0):

- OCR and complex binary attachment extraction
- LLM-generated summary documents
- full ATHOS-wide DB versioning refactor (document pattern now; implement broadly later)

## Deliverables

1. `scripts/build_tickets_chroma.py`
2. `src/athos/utils/ticket_ingest.py`
3. `docs/ticket_ingestion/` docs updates (as needed)
4. Test coverage:
   - unit tests for parser/normalizer/filter/chunker
   - one integration smoke for local Chroma write/read
5. Manifest schema and sample output

## Data Model (v0)

Single collection, default name:

- `servicenow_tickets_v0`

Document kinds:

- `full_incident` (primary v0 record type)

Required metadata per document:

- `incident_number`
- `sys_id`
- `state`
- `category`
- `subcategory`
- `assignment_group`
- `sys_created_on`
- `sys_updated_on`
- `contact_type`
- `created_by`
- `has_attachments`
- `doc_kind`
- `source_json_path`
- `chunk_index`
- `chunk_count`

## CLI Contract (proposed)

```text
python scripts/build_tickets_chroma.py \
  /path/to/servicenow_incidents \
  --persist-dir /path/to/chroma \
  --collection-name servicenow_tickets_v0 \
  --min-created-date 2023-01-01 \
  --exclude-contact-type "Staff Initiated" \
  --exclude-contact-type "System Alert Auto Generated" \
  --max-comment-chars 12000 \
  --max-work-note-chars 12000 \
  --max-incident-chars 40000 \
  --manifest-out /path/to/manifests/tickets_v0_YYYYMMDD.json \
  --mode balanced
```

Optional flags:

- `--include-contact-type ...` (override mode)
- `--exclude-created-by-regex ...`
- `--exclude-assignment-group-regex ...`
- `--dry-run` (compute counts only; do not write Chroma)
- `--limit N` (debug mode)

## Phased Plan

## Phase 1: Baseline Parser + Normalizer

Tasks:

- Implement JSON loader and schema-safe extraction (`metadata`, `incident_fields`, `discussions`, `attachments`, `statistics`)
- Build normalized text block:
  - header/core incident fields
  - flattened customer comments
  - flattened work notes
  - attachment metadata summary
- Deterministic ID scheme:
  - `<incident_number>:full` or `<sys_id>:full`
  - chunk suffix when needed

Exit criteria:

- Can parse a random sample without crashes
- Produces stable normalized text and metadata

## Phase 2: Filtering + Text Caps + Chunking

Tasks:

- Implement filter pipeline (date, contact type, optional regex filters)
- Implement `max_comment_chars`, `max_work_note_chars`, `max_incident_chars`
- Implement chunk fallback for oversized incidents

Exit criteria:

- Filter decisions explainable and counted by reason
- Oversized machine-log incidents no longer create extreme single documents

## Phase 3: Chroma Writer + Manifest

Tasks:

- Add persistent Chroma client writer
- Batch add documents with deterministic IDs
- Add run manifest output with:
  - source path, run timestamp
  - full CLI/config args
  - counts (input/kept/filtered/chunked/truncated/errors)
  - collection/persist-dir identifiers
  - git SHA (if available)

Exit criteria:

- Collection build is reproducible
- Manifest fully describes run conditions

## Phase 4: Tests + Validation

Tasks:

- Unit tests:
  - core field extraction
  - discussion flattening
  - filters
  - chunking behavior
  - deterministic IDs
- Integration smoke:
  - small fixture corpus -> Chroma
  - query returns expected incident IDs for known keywords
  - query returns expected incident IDs for semantic/paraphrase prompts (not exact keyword match)

Exit criteria:

- Tests pass in CI/local for unit scope
- Manual smoke query sanity check passes
- Integration smoke validates both keyword and semantic retrieval behavior on fixture corpus

## Acceptance Criteria (v0)

1. End-to-end build command completes on full corpus slice without fatal errors.
2. Manifest includes all required reproducibility fields.
3. Default `balanced` mode applies agreed filter policy.
4. Largest outlier incidents are bounded via truncation/chunking.
5. Collection is queryable by incident keywords and metadata filters.

## Operational Recommendations

1. Start with `--dry-run` to inspect keep/filter counts before full ingest.
2. Build first on a sampled subset (`--limit`) to validate runtime and output quality.
3. Promote only versioned collections/manifests to “current”.
4. Process JSON records in a streaming fashion (no full in-memory load of corpus) and write progress logs/checkpoints for resumability.
5. Treat attachment paths as potentially irregular and verify existence before attempting reads.

## Runtime Caveats

1. Chroma persistence compatibility:
   - Persisted DBs may not be portable across differing Chroma runtime versions/environments.
   - Prefer versioned `persist-dir`/collection outputs per ingestion run rather than in-place mutation of unknown-origin DBs.

2. Large-record handling:
   - A small minority of incidents contain very large discussion text blobs; truncation/chunk limits are mandatory to avoid pathological embeddings and memory spikes.

3. Corpus traversal assumptions:
   - Top-level `INC001..INC024` folders are buckets, not incident identifiers.
   - Incident identity should come from record fields (`metadata.incident_number`, `metadata.sys_id`) rather than path prefixes.

## Versioning Pattern (for this pipeline)

Recommended naming:

- collection: `servicenow_tickets_v0_20260223`
- manifest: `manifests/servicenow_tickets_v0_20260223.json`
- optional alias: `servicenow_tickets_current -> servicenow_tickets_v0_20260223`

This pattern should later generalize to docs embeddings and other ATHOS vector corpora.

## Next Layer Hooks (post-v0)

- Layer 2: `attachment_text` docs for text-like attachments
- Layer 3: `incident_summary` docs alongside full records

Both can be added without breaking v0 if IDs/metadata are kept stable.
