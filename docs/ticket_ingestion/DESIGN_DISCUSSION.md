# Ticket Ingestion Pipeline Design Discussion (Historical)

This document captures early design thinking for the layered raw-ticket
ingestion approach. It is retained for background context. For the current
derived retrieval pipeline, see
[`DERIVED_CORPUS_PIPELINE.md`](./DERIVED_CORPUS_PIPELINE.md).

## Goal

Build a practical ingestion pipeline for historical ServiceNow incidents into a single Chroma collection, starting with the simplest useful implementation and adding capabilities in layers.

## Design Principle

The candidate approaches are complementary and should be staged, not treated as mutually exclusive alternatives.

- Layer 1: baseline full-incident indexing
- Layer 2: text-attachment enrichment
- Layer 3: summary + full hybrid records

Each layer should preserve previous IDs/metadata conventions so later upgrades do not invalidate prior experiments.

## Constraints and Context

- Corpus is large (`~8.6G`, `76k+` JSON records).
- Most records are small enough for single-chunk storage; tail records can be very large.
- Existing benchmark scope does not require new datasets/metrics.
- Immediate need is an enabler for existing semantic/file retrieval experiments.

## Proposed Layered Design

## Layer 1 (V0): Full Incident Record Indexing

### What gets indexed

- One normalized text document per incident JSON record.
- Include:
  - Core incident fields (`number`, short description, state/category, assignment, important timestamps, description)
  - Flattened discussions (customer comments + internal work notes)
  - Attachment metadata summary (names/types/sizes), but not attachment file contents yet

### Storage

- Single collection, e.g. `servicenow_tickets_v0`
- Metadata per document:
  - `incident_number`
  - `sys_id`
  - `state`, `category`, `subcategory`
  - `assignment_group`
  - `updated_on` / `created_on`
  - `has_attachments`
  - `doc_kind=full_incident`
  - `source_json_path`

### Chunking

- Default behavior: keep whole incident in one chunk.
- Fallback: if normalized text exceeds threshold (e.g. 40k chars), split into chunked parts with deterministic suffix (`:chunk_0`, `:chunk_1`, ...).

### Why this is the right start

- Minimal complexity and lowest implementation risk.
- Immediate retrieval value for ticket-style test cases.
- Supports your preference for single-chunk when feasible.

## Layer 2 (V0.1): Add Text Attachment Content

### What changes

- Ingest text-like attachments as separate records linked to the incident:
  - `txt`, `log`, `csv`, `sh`, `md`, optionally `rtf`
- Continue metadata-only handling for binary/complex types:
  - `png`, `jpg`, `pdf`, `docx`, `xlsx`, etc.

### Metadata additions

- `doc_kind=attachment_text`
- `attachment_name`
- `attachment_content_type`
- `attachment_local_path`
- `parent_incident_number`

### Why this is next

- Significant recall upside with small implementation delta.
- Avoids OCR and complex parsers in initial rollout.

## Layer 3 (V0.2): Hybrid Summary + Full Content

### What changes

- Add a concise summary document per incident alongside full record:
  - `doc_kind=incident_summary`
- Keep existing `full_incident` and `attachment_text` docs.

### Retrieval behavior implications

- Agents can query summary docs first for precision, then fetch full/attachments for detail.
- Same collection, differentiated by `doc_kind`.

### Why this is later

- Requires summary generation policy (extractive vs LLM-assisted), validation, and potential drift checks.
- Not needed to unlock initial experiments.

## Pseudo Example: Normalized Full Incident Text (Layer 1)

```text
INCIDENT: INC0144695
SYS_ID: 2caa1105db440810200f7d321f961905
STATE: Closed
CATEGORY: Software
SUBCATEGORY:
ASSIGNMENT_GROUP: Consulting
ASSIGNED_TO: Leak, Stephen (sleak)
PRIORITY: 3 - Moderate
CREATED: 2019-09-20 13:08:22
UPDATED: 2022-11-09 02:00:04
SHORT_DESCRIPTION: fail for module load slatec
DESCRIPTION:

CUSTOMER_COMMENTS:
[2019-09-20 13:54:23] Stephen Leak (sleak): it looks like both pgplot and slatec...
[2019-09-20 14:09:26] Guest: Thank you for your help...

INTERNAL_WORK_NOTES:
[2019-09-20 13:20:00] consultant: tracking module rebuild...

ATTACHMENTS_METADATA:
- Screen Shot 2019-08-12 at 6.08.10 PM.png (image/png, 430741 bytes)
```

## Pseudo Example: IDs in One Collection

```text
servicenow_tickets_v0
  INC0144695:full
  INC0144695:full:chunk_1   # only when fallback chunking needed
  INC0144695:att:screen-shot-2019-08-12.txt  # Layer 2+
  INC0144695:summary        # Layer 3+
```

## Implementation Notes

- Keep deterministic IDs from incident number/sys_id + doc kind + chunk index.
- Emit ingest manifest for traceability:
  - source path
  - run timestamp
  - counts by `doc_kind`
  - skipped files and reasons
- Keep parser tolerant to empty/null fields and optional arrays.

## Recommendation

Proceed with Layer 1 immediately, with chunk fallback and stable metadata conventions designed to support Layers 2 and 3 without schema churn.
