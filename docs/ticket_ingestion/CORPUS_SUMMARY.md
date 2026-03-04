# ServiceNow Ticket Corpus Summary

## Location

- Source root: `/pscratch/sd/s/sfarrell/agentic-ops/get-sn-tickets/servicenow_incidents`

## High-Level Characteristics

- Total corpus size: ~`8.6G`
- JSON records: `76,146`
- Attachment files present in many formats:
  - Common: `png`, `txt`, `jpg`, `pdf`, `log`, `jpeg`, `docx`
  - Less common: `rtf`, `csv`, `xlsx`, `xls`, `sh`, `gz`, `tar`, `tgz`, etc.

Note:
- Top-level directories (`INC001` ... `INC024`) appear to be storage buckets.
- Individual ticket records are JSON files under these buckets and represent incident numbers like `INC0144695`, `INC0249053`, etc.
- Attachment directories in this export frequently use the literal suffix `*_attachements/` (spelling as observed in corpus paths).

## Ticket Class Signals (Filtering-Relevant)

The corpus contains a mix of user-facing incidents and internal/ops-focused incidents.

### Contact Type distribution

- `User Web Interface`: `26,726`
- `Staff Initiated`: `24,696`
- `Email`: `15,570`
- `System Alert Auto Generated`: `8,777`
- (small remainder: blank/phone/in-person)

### Creator distribution (top signals)

High-volume creators include clearly automated/internal actors:

- `autoticketing`: `8,457`
- `auto-ops`: `1,300`
- plus many individual staff users (for example `bdlalli`, `jhuggins`, `twquan`, etc.)

### Assignment group distribution (top groups)

- `HPC POC`: `21,754`
- `Consulting`: `19,699`
- `Account Support`: `9,363`
- `DAS`: `6,203`
- `Allocations`: `2,806`
- `Perlmutter Admin`: `2,129`
- `ISG`: `2,125`

Interpretation:
- A large portion of records are likely internal operations workflow, not end-user support interactions.

## JSON Record Structure

Observed top-level keys are consistent:

- `metadata`
- `incident_fields`
- `discussions`
- `attachments`
- `statistics`

### `metadata` (example fields)

- `incident_number`
- `sys_id`
- `table`
- `export_timestamp`

### `incident_fields` (many fields)

Includes core fields useful for retrieval and filtering:

- `number`
- `short_description`
- `description`
- `state`
- `category`
- `subcategory`
- `assignment_group`
- `assigned_to`
- `priority`, `impact`, `urgency`
- `close_code`, `close_notes`, `resolved_at`, `resolved_by`
- `sys_created_on`, `sys_updated_on`, `opened_at`, `closed_at`, etc.

### `discussions`

- `customer_facing_comments`: array of entries with `timestamp`, `created_by`, `text`, `type`
- `internal_work_notes`: array with similar shape

### `attachments`

Array of attachment metadata objects, including:

- `file_name` (with `display_value` / `value`)
- `content_type`
- `size_bytes`
- `table_sys_id`
- `local_path` (path to attachment on disk)

Important shape detail:
- Attachment fields are often nested objects with `{display_value, value}`; ingestion should read `.value` for stable machine-parsing and retain display text when useful.

### `statistics`

- `total_comments`
- `total_work_notes`
- `total_attachments`

## Size and Density Observations

- JSON file size distribution (all records):
  - p50: ~`8.5KB`
  - p90: ~`16.9KB`
  - p99: ~`191KB`
  - max: ~`4.0MB`
- Sampled interaction density (`n=1000`):
  - avg comments: `4.47`
  - avg work notes: `1.32`
  - avg attachments: `0.16`

## Largest-Incident Findings

The largest records are often Perlmutter/HPC operations incidents, many with:

- `contact_type = System Alert Auto Generated`
- `assignment_group = HPC POC` or `Perlmutter Admin`
- `sys_created_by = autoticketing`

Important finding:
- Large JSON size is frequently driven by very large text blobs inside comments/work notes (often diagnostic dumps), not by attachments.
- Example outliers had zero attachments but multi-megabyte comment text.

Implication:
- Ingestion should include configurable truncation/capping for oversized discussion text.

Implications:
- Most incidents are compact enough to fit a single retrieval chunk.
- A minority are much larger and need chunk fallback.
- Oversized records are disproportionately associated with ops/auto-generated classes (`System Alert Auto Generated`, `autoticketing`, `HPC POC`/`Perlmutter Admin`).

## Pseudo Example: Record Shape

```json
{
  "metadata": {
    "incident_number": "INC0144695",
    "sys_id": "2caa1105db440810200f7d321f961905",
    "export_timestamp": "2026-02-15T23:33:16.683480"
  },
  "incident_fields": {
    "number": "INC0144695",
    "short_description": "fail for module load slatec",
    "description": "",
    "state": "Closed",
    "category": "Software",
    "assignment_group": "Consulting",
    "sys_created_on": "2019-09-20 13:08:22",
    "sys_updated_on": "2022-11-09 02:00:04"
  },
  "discussions": {
    "customer_facing_comments": [
      {
        "timestamp": "2019-09-20 13:54:23",
        "created_by": "Stephen Leak (sleak)",
        "text": "it looks like ...",
        "type": "customer_comment"
      }
    ],
    "internal_work_notes": [
      {
        "timestamp": "2019-09-20 13:10:00",
        "created_by": "consultant",
        "text": "tracking module rebuild",
        "type": "work_note"
      }
    ]
  },
  "attachments": [
    {
      "file_name": { "value": "example.log" },
      "content_type": { "value": "text/plain" },
      "size_bytes": { "value": "12345" },
      "local_path": "servicenow_incidents/.../example.log"
    }
  ],
  "statistics": {
    "total_comments": 1,
    "total_work_notes": 1,
    "total_attachments": 1
  }
}
```

## Pseudo Example: Attachment Directory

```text
servicenow_incidents/
  INC024/
    46/
      39.json
      00_20260212_012659_attachements/
        dell_100G_cname_req.txt
      51_20260212_012739_attachements/
        image001.png
        image001.jpg
```

## Filtering and Recency Scenarios (Observed Counts)

These counts help choose initial ingestion defaults:

- Keep only non-`Staff Initiated` and non-`System Alert Auto Generated`:
  - `42,673` (`56.04%`)
- Keep only user-facing contact types (`Email`, `User Web Interface`, `Phone`, `In Person`):
  - `42,312` (`55.57%`)
- Keep only recent incidents (`sys_created_on >= 2023-01-01`):
  - `47,184` (`61.97%`)
- Non-staff/non-auto + recent:
  - `25,093` (`32.95%`)
- User-facing contact types + recent:
  - `24,735` (`32.48%`)

## Closure-Code Signals (Observed Counts)

`incident_fields.close_code` is populated on all records (blank value in some records).

Observed distribution (`n=76,146`):

- `Solved (Permanently)`: `42,127` (`55.32%`)
- `Not Solved (No User Response)`: `21,775` (`28.60%`)
- `Resolved by Requester`: `4,041` (`5.31%`)
- `Solved (Work Around)`: `3,692` (`4.85%`)
- blank: `1,671` (`2.19%`)
- `Closed by Requester`: `1,069` (`1.40%`)
- `No Fault Found`: `815` (`1.07%`)
- `Duplicate`: `625` (`0.82%`)
- Remaining values (`Not Solved (Not Reproducible)`, `Not Solved (Too Costly)`, `Unknown (External Incident)`, and a few corpus-specific labels) are each `<0.2%`.

Filtering impact examples:

- Keep only `Solved (Permanently)`:
  - `42,127` (`55.32%`)
- Keep `Solved (Permanently|Work Around|Resolved by Requester)`:
  - `49,860` (`65.48%`)

Representative ticket examples in the corpus:

- Solved:
  - `INC0048988` (`Solved (Permanently)`) at `/Users/sfarrell/Work/agentic-ops/athos/data/servicenow_incidents/INC004/89/88.json`
  - `INC0186174` (`Solved (Work Around)`) at `/Users/sfarrell/Work/agentic-ops/athos/data/servicenow_incidents/INC018/61/74.json`
- Not solved / unsuitable for resolution retrieval:
  - `INC0043375` (`Not Solved (No User Response)`) at `/Users/sfarrell/Work/agentic-ops/athos/data/servicenow_incidents/INC004/33/75.json`
  - `INC0186132` (`Duplicate`) at `/Users/sfarrell/Work/agentic-ops/athos/data/servicenow_incidents/INC018/61/32.json`

Recommended as pipeline knobs:
- date cutoff (`min_created_date`)
- contact-type excludes/include list
- close-code include/exclude list
- creator regex exclude
- assignment-group include/exclude rules
- max comment chars / max incident chars
