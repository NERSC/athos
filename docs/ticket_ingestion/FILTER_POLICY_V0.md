# Ticket Ingestion Filter Policy v0

## Purpose

Define a pragmatic default filtering policy for ServiceNow ticket ingestion that prioritizes user-relevant support incidents while excluding obvious internal/auto-generated ops noise.

This policy is intentionally configurable and conservative enough to evolve as we validate retrieval quality.

## Defaults (v0)

## 1) Date filter

- `min_created_date = 2023-01-01`

Rationale:
- Keeps the corpus more relevant to current systems/processes.
- Reduces index size and stale operational details.

## 2) Contact-type exclusion

- Exclude:
  - `Staff Initiated`
  - `System Alert Auto Generated`

Rationale:
- These classes are strongly associated with internal/ops workflows.
- Large outlier incidents are heavily concentrated in this slice.

## 3) Close-code include filter (balanced default)

- Include:
  - `Solved (Permanently)`

Rationale:
- Prioritizes incidents with explicit permanent resolution signal.
- Excludes large classes like `Not Solved (No User Response)` that usually have weak/no fix signal.

## 4) Oversized discussion controls

- `max_comment_chars = 12000`
- `max_work_note_chars = 12000`
- `max_incident_chars = 40000` with chunk fallback

Rationale:
- Prevent single records from being dominated by machine-generated diagnostic dumps.
- Keep chunks retrievable and useful for agent context.

## 5) Attachment handling

- Include text-like attachment content (if enabled):
  - `txt`, `log`, `csv`, `sh`, `md` (optionally `rtf`)
- Keep binary/complex types as metadata-only in v0:
  - `png`, `jpg`, `jpeg`, `pdf`, `docx`, `xlsx`, `xls`, etc.

Rationale:
- Delivers retrieval value quickly without OCR/complex parsing overhead.

## Optional filters (disabled by default)

- `exclude_created_by_regex`
  - Example: `^(autoticketing|auto-ops|auto-consult|auto-consultant)$`
- `exclude_assignment_group_regex`
  - Example: `^(HPC POC|Perlmutter Admin|Cori Admin|DAS|ISG|OTG|Security)$`

Rationale:
- Useful for stricter user-support-only slices.
- Keep optional because some internal tickets may still be valuable for troubleshooting benchmarks.

## Recommended Modes

## `balanced` (default)

- Apply defaults 1-5.
- Do not apply creator/group regex excludes.

## `user_support_strict`

- Apply defaults 1,2,4,5.
- Add contact-type include list: `Email`, `User Web Interface`, `Phone`, `In Person`.
- Optionally enable creator/group regex excludes.

## `full_corpus`

- Disable contact-type/date filters.
- Keep only safety caps (`max_*_chars`) and chunk fallback.

## Config Surface (proposed)

Example CLI flags:

```text
--min-created-date 2023-01-01
--exclude-contact-type "Staff Initiated" --exclude-contact-type "System Alert Auto Generated"
--include-contact-type "Email" --include-contact-type "User Web Interface"
--include-close-code "Solved (Permanently)"
--exclude-created-by-regex "^(autoticketing|auto-ops)$"
--exclude-assignment-group-regex "^(HPC POC|Perlmutter Admin)$"
--max-comment-chars 12000
--max-work-note-chars 12000
--max-incident-chars 40000
--attachment-text-ext txt,log,csv,sh,md,rtf
```

## Manifest Requirements

Each ingestion run should persist filter settings in its manifest:

- date/contact include-exclude parameters
- regex filters
- text caps/chunk thresholds
- include/exclude attachment types
- counts: input, kept, filtered_by_reason, chunked, truncated

This is required for reproducibility and versioned comparison across corpus builds.
