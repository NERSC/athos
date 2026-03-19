# Derived Ticket Corpus Plan

## Goal

Build a new retrieval corpus derived from historical ServiceNow tickets which is:

- more retrieval-friendly than raw ticket transcripts,
- safer to expose to downstream commercial models,
- produced entirely by on-prem transformation using open-weights models,
- reproducible and auditable.

The derived corpus should replace raw ticket text as the retrieval surface used by agentic flows. Raw tickets remain an internal source artifact only.

## Context

The current retrieval corpus is built from sanitized raw ticket JSON. This is an improvement over using unsanitized tickets, but the source format is still not ideal for retrieval:

- the ticket body is dominated by conversational history,
- useful technical signal is mixed with greetings, signatures, routing chatter, and repeated updates,
- some residual personal names may remain in prose,
- attachment content is not yet transformed into a retrieval-friendly form.

For the longer-term design, the better boundary is:

`raw ticket -> on-prem transformation -> derived safe corpus -> retrieval -> downstream model use`

## Source Ticket Shape

Important constraint: our ServiceNow ticket data does **not** contain a usable freeform `description` field for most tickets in the way many incident systems do.

In practice, the high-value source fields are:

- `short_description` as a concise title,
- customer-facing comments,
- internal work notes,
- deterministic incident metadata,
- attachment metadata,
- in some cases, text-like attachment contents.

This means the transformation pipeline should treat the ticket as:

1. deterministic metadata,
2. short title,
3. threaded message history,
4. attachment metadata and optional attachment text.

## Non-Goals

This pipeline should **not** try to:

- perfectly remove all personal names from free-form prose,
- preserve the original ticket transcript verbatim as the retrieval unit,
- produce a highly granular incident ontology with many ambiguous fields,
- extract OCR from image-based attachments in v1,
- perform final paper-quality classification beyond the retrieval transformation itself.

## Proposed Output Contract

Keep deterministic metadata separate from LLM-derived fields.

### Deterministic Metadata

These should come directly from the existing pipeline, not from the LLM:

- `incident_number`
- `sys_created_on`
- `state`
- `close_code`
- `category`
- `subcategory`
- `assignment_group` if needed
- `source_json_path`
- corpus/version provenance
- prompt/model version provenance

### LLM-Derived Fields

Use a compact, high-signal schema:

```json
{
  "issue_summary": "string",
  "technical_context": "string",
  "resolution_summary": "string",
  "retrieval_keywords": ["string"],
  "evidence_snippets": ["string"]
}
```

Field intent:

- `issue_summary`
  - what the user was trying to do and what failed
- `technical_context`
  - environment details only when they help retrieval
  - examples: software, module, filesystem, machine, service, workflow
- `resolution_summary`
  - root cause, workaround, resolution, or explicit uncertainty if unresolved
- `retrieval_keywords`
  - short normalized terms useful for search and recall
- `evidence_snippets`
  - short technical strings worth retrieving on
  - commands, error fragments, module names, service names, file or system identifiers

### Required vs Optional

Recommended:

- required:
  - `issue_summary`
  - `resolution_summary`
  - `retrieval_keywords`
- optional but encouraged:
  - `technical_context`
  - `evidence_snippets`

This keeps the output contract small enough that the model does not need to invent precision.

## Derived Retrieval Document

In v1, generate one retrieval document per incident from the derived record.

Example rendering:

```text
ISSUE_SUMMARY:
...

TECHNICAL_CONTEXT:
...

RESOLUTION_SUMMARY:
...

RETRIEVAL_KEYWORDS:
- ...
- ...

EVIDENCE_SNIPPETS:
- ...
- ...
```

This text should be derived deterministically from the JSON record, not generated independently.

## Input Formatting for the Model

Do **not** pass raw JSON directly to the model.

Instead, render a deterministic input view with sections such as:

```text
INCIDENT_METADATA:
- incident_number: ...
- created_on: ...
- state: ...
- close_code: ...
- category: ...
- subcategory: ...

SHORT_DESCRIPTION:
...

CUSTOMER_COMMENTS:
- [timestamp] ...
- [timestamp] ...

INTERNAL_WORK_NOTES:
- [timestamp] ...
- [timestamp] ...

ATTACHMENT_METADATA:
- filename (type, size)
- filename (type, size)

ATTACHMENT_TEXT_SNIPPETS:
- attachment: ...
  content: ...
```

This keeps the LLM interface stable even if the raw JSON shape evolves.

## Attachment Strategy

We likely do need to process some text-based attachment data.

This should follow the same layered approach already discussed in the existing Chroma ingestion docs:

- attachment metadata is always available,
- text-like attachments are a distinct enrichment layer,
- binary/image/OCR-heavy attachments should be out of scope for v1.

### Recommended Attachment Handling

For v1:

- include attachment metadata for all attachments,
- include attachment text only for text-like formats,
- skip OCR and complex binary extraction.

Candidate text-like types:

- `txt`
- `log`
- `out`
- `err`
- `csv`
- `tsv`
- `json`
- `yaml`
- `yml`
- `xml`
- `md`
- `rst`
- `sh`
- `bash`
- `c`
- `cc`
- `cpp`
- `h`
- `hpp`
- `py`
- `sql`

### How Attachment Text Should Be Used

Do not dump full attachment bodies into the prompt by default.

Instead:

- use deterministic extraction for text attachments,
- cap and prioritize high-signal content,
- include only selected snippets or truncated content blocks in the rendered input.

Priority should go to:

- error messages,
- commands,
- configuration excerpts,
- stack traces,
- module or environment lines,
- quota or filesystem diagnostics,
- scheduler or system status excerpts.

## Model Role

Use the local open-weights model for:

- synthesis,
- normalization,
- compression,
- selection of salient technical details.

Do **not** ask it to infer unsupported facts.

If root cause or resolution is unclear, the model should say so briefly rather than hallucinating certainty.

## Prompt Design

The prompt should explicitly instruct the model to:

- produce only the requested JSON object,
- preserve technical signal,
- omit greetings and signatures,
- omit usernames, emails, phone numbers, display names, and watchlists,
- avoid participant names in the output,
- include root cause, workaround, and outcome when clearly supported,
- state uncertainty when the ticket is unresolved or ambiguous,
- keep wording compact and retrieval-oriented.

### Should We Include an Example?

Yes.

Recommendation:

- include exactly one short concrete example in the prompt,
- make it representative but not overly detailed,
- show both the input section style and the desired JSON output.

Why:

- it anchors output style,
- reduces schema drift,
- helps the model keep `retrieval_keywords` and `evidence_snippets` concise,
- clarifies how to avoid PII while preserving technical content.

One example is likely enough for v1.

## Validation and Audit

We should **not** assume the model output is safe by default.

### Deterministic Validation

Every derived record should be validated for:

- valid JSON,
- required fields present,
- string/list type correctness,
- length bounds,
- keyword count bounds,
- snippet count bounds.

### Residual PII Audit

Use post-generation auditing as a leak finder, not as a perfect oracle.

Current intent:

- run residual audits over the derived corpus,
- use findings to patch prompt, formatting, or deterministic post-processing,
- iterate until the derived output is acceptable.

Presidio can be one of the audit tools, but it should be used carefully:

- useful for exploratory residual detection,
- not suitable as a raw pass/fail gate on generic `PERSON` findings in technical text,
- better for identifying recurring leak classes and guiding iteration.

High-confidence deterministic checks should remain the primary release gate:

- emails,
- username-in-context patterns,
- phone-number-like patterns if feasible,
- explicit structured identity fields,
- watchlist/display-name remnants in deterministic metadata.

## Provenance and Reproducibility

The derived corpus should carry explicit provenance:

- source manifest path,
- source corpus fingerprint,
- transformation run timestamp,
- model name,
- model settings,
- prompt version,
- schema version,
- validation/audit summary.

This is important for both scientific reproducibility and paper defensibility.

## Recommended Implementation Shape

Keep this as a deterministic batch transformation pipeline, not an agent flow.

Suggested components:

1. deterministic ticket renderer
   - JSON -> prompt input text
2. LLM transform step
   - rendered ticket -> structured derived JSON
3. deterministic validator
   - schema and bounds checks
4. residual PII audit step
   - reports and sample findings
5. deterministic rendering step
   - derived JSON -> retrieval document text
6. ingestion step
   - index the derived retrieval document corpus

## LangChain / OpenAI API Notes

Using LangChain is reasonable here if it helps with:

- model invocation,
- structured output parsing,
- retry control,
- batching and logging,
- reuse of existing repo/environment support.

But the pipeline itself should remain simple:

- no multi-step agent orchestration,
- no tool-calling inside the transform loop unless clearly needed,
- deterministic configuration and manifests.

## Open Questions To Resolve Before Implementation

1. Exact schema limits
   - max chars for `issue_summary`, `technical_context`, `resolution_summary`
   - max keyword count
   - max evidence snippet count

2. Input truncation strategy
   - how much history to include
   - whether to emphasize latest resolution-bearing notes
   - how to cap attachment text

3. Prompt wording
   - final instructions
   - exact example content

4. Retry policy
   - how many retries on invalid JSON or failed validation
   - whether to use a stricter repair prompt vs full rerun

5. Storage format
   - one JSON per ticket vs JSONL
   - whether to keep rendered retrieval text as a separate stored artifact

6. Attachment text scope
   - exactly which extensions/content types are allowed in v1

## Proposed Pilot

Before full-corpus transformation:

1. select a small mixed subset, e.g. 100 to 300 tickets,
2. build derived records,
3. audit residual PII,
4. compare retrieval quality against the current sanitized raw corpus,
5. revise prompt/validation before scaling.

## Current Recommendation

For the immediate paper cycle:

- use the current deterministic sanitization pipeline already implemented,
- treat this derived-corpus workstream as the next hardening step.

For the next implementation cycle:

- finalize the compact schema,
- draft the transformation prompt with one example,
- define validation thresholds,
- build a small pilot transformer and audit loop.
