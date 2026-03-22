# CUG M4 Run Review: `cug_m4`

Date: 2026-03-21 (UTC)  
Run directory: `results/cug_m4`  
Wrapper: `scripts/submit_cug_m4.sh`  
Judge: `llama_4_maverick` (`rubric_v1`)  
Aggregate manifest: `data/chroma/aggregates/manifests/athos_eval_bundle_20260318_derived_tickets_lt_20250901_v2.json`

## Scope

This review records the first expanded-set eval rerun subset that uses the M4
derived ticket retrieval corpus for paper-facing GPT-OSS retrieval
configurations.

The wrapper launched three flows over the expanded datasets:

- `cug_lang_chroma_gptoss`
- `cug_lang_chroma_gptoss_opt`
- `cug_lang_filesystem_gptoss`

Each flow ran on:

- `data/ticket_cases` (`156` cases)
- `evals/nersc_qa.v2.jsonl` (`123` questions)

Total attempted runs: `837` (`3 x 279`).

## Relation to M4

In `docs/cug_paper/PLAN.md`, milestone M4 is the derived-ticket retrieval
corpus workstream:

- replace raw-ticket retrieval surfaces with a derived representation,
- support both Chroma retrieval and filesystem retrieval,
- preserve versioned retrieval provenance.

`cug_m4` is not a new milestone definition. It is the first concrete
expanded-set evaluation run that exercises the paper-facing derived aggregate
DB in those retrieval configurations.

This run is therefore a partial M4 rerun artifact, not the M4 closeout.

## Top-Line Outcome

The run completed end to end.

- execution finished successfully for all three configured flows
- scoring and summarization completed
- final summary artifact:
  - `results/cug_m4/aggregates/summary.json`
- final judgment artifact:
  - `results/cug_m4/judgments/llama_4_maverick_rubric_v1.jsonl`

Wrapper timing summary:

- started: `2026-03-21T06:00:16Z`
- finished: `2026-03-21T10:06:41Z`
- elapsed: `14785s` (~`4.11h`)

## M4 Scope Status

This artifact should be interpreted as a completed subset of M4.

Completed in this rerun set:

- `cug_lang_chroma_gptoss`
- `cug_lang_chroma_gptoss_opt`
- `cug_lang_filesystem_gptoss`

Not covered by this artifact:

- Sonnet retrieval rows that are also affected by the corpus change
- retrieval-backed auxiliary paper evidence such as variance/harness refreshes
- judge-sensitivity rescoring over the final post-M4 retrieval-backed artifact set
- any final manuscript/table refresh needed after the full retrieval refresh set
  is frozen

## Aggregate Results

### Rollup by flow

| Flow | Runs | Skips | Mean score | Pass rate | Mean latency |
|---|---:|---:|---:|---:|---:|
| `cug_lang_chroma_gptoss` | 279 | 69 | 64.03 | 63.4% | 28.9s |
| `cug_lang_chroma_gptoss_opt` | 279 | 13 | 83.60 | 85.3% | 29.2s |
| `cug_lang_filesystem_gptoss` | 279 | 135 | 44.22 | 44.1% | 47.1s |

### Split by dataset

| Flow | Dataset | Runs | Skips | Mean score | Pass rate | Mean latency |
|---|---|---:|---:|---:|---:|---:|
| `cug_lang_chroma_gptoss` | `ticket_cases` | 156 | 44 | 62.85 | 62.8% | 28.3s |
| `cug_lang_chroma_gptoss` | `nersc_qa.v2` | 123 | 25 | 65.53 | 64.2% | 29.8s |
| `cug_lang_chroma_gptoss_opt` | `ticket_cases` | 156 | 7 | 86.35 | 87.8% | 32.6s |
| `cug_lang_chroma_gptoss_opt` | `nersc_qa.v2` | 123 | 6 | 80.11 | 82.1% | 24.9s |
| `cug_lang_filesystem_gptoss` | `ticket_cases` | 156 | 82 | 42.45 | 42.3% | 54.0s |
| `cug_lang_filesystem_gptoss` | `nersc_qa.v2` | 123 | 53 | 46.46 | 46.3% | 38.3s |

## Main Findings

### 1. The optimized Chroma row remains the strongest GPT-OSS paper-facing configuration

`cug_lang_chroma_gptoss_opt` clearly outperformed both the older Chroma GPT-OSS
baseline and the filesystem comparison row:

- best mean score (`83.60`)
- best pass rate (`85.3%`)
- lowest skip count (`13`)
- similar average latency to the non-optimized Chroma row

This supports carrying the optimized Chroma row forward as the main open-weight
retrieval result for the paper.

### 2. The non-optimized Chroma GPT-OSS row is materially weaker but still functional

`cug_lang_chroma_gptoss` completed the full expanded-set run and remains usable
as a comparison point, but it had much worse robustness than the optimized row:

- `69` skipped runs vs `13`
- ~`19.6` point lower mean score
- ~`21.9` point lower pass rate

The optimization work in M3 therefore translated into a meaningful gain on the
derived-ticket M4 retrieval surface.

### 3. The filesystem row is not stable enough to treat as a strong paper result on the expanded M4 run

The full-scale derived-ticket filesystem run underperformed badly:

- `135` skipped runs out of `279`
- mean score `44.22`
- pass rate `44.1%`
- slowest average latency of the three rows

This is much worse than the earlier mini smoke evidence documented in
`docs/filesystem_bundle_eval_issue.md`, where the bundle-backed filesystem setup
looked viable on small QA slices.

The expanded-set M4 result shows that:

- the filesystem setup is operational,
- the derived ticket representation did not fix the major reliability issues at
  expanded scale,
- the filesystem row is still a meaningful design-point comparison, but it is
  clearly weaker than the Chroma-based retrieval rows.

## Filesystem Failure Mix

For `cug_lang_filesystem_gptoss`, execution records show:

- `144` success
- `135` `execution_error`

Failure types:

- `GraphRecursionError`: `113`
- `ToolException`: `16`
- `BadRequestError`: `6`

Representative non-recursion failures:

- missing file path (`ENOENT`):
  - `results/cug_m4/athos/cug_lang_filesystem_gptoss__gptoss__57048e37/nersc_qa.v2/3462dd0f597a/0/run.json`
- attempted file read on a directory (`EISDIR`):
  - `results/cug_m4/athos/cug_lang_filesystem_gptoss__gptoss__57048e37/nersc_qa.v2/48381b50e3f0/0/run.json`
- negative remaining generation budget:
  - `results/cug_m4/athos/cug_lang_filesystem_gptoss__gptoss__57048e37/nersc_qa.v2/95eb15cd3845/0/run.json`

Observed filesystem tool use on successful runs was mostly read-oriented and
small-surface:

- `list_allowed_directories`
- `read_file`
- `search_files`
- `list_directory`

This suggests the main failure mode is not "too many different tools." The main
problems are loop control, path handling, and context-budget management.

## Documentation Assessment

Current M4 documentation quality is mixed.

What is already documented well:

- the M4 milestone definition in `docs/cug_paper/PLAN.md`
- the derived corpus mechanics in
  `docs/ticket_ingestion/DERIVED_CORPUS_PIPELINE.md`
- the bundle-backed filesystem rationale and earlier smoke results in
  `docs/filesystem_bundle_eval_issue.md`

What was missing before this review:

- a paper-workstream document tying M4 corpus buildout to an actual expanded-set
  evaluation run
- a frozen top-line result summary for `results/cug_m4`
- a clear statement that the derived-ticket corpus helped paper-facing Chroma
  evaluation lineage, but did not make the filesystem row robust at full scale

## Recommended Documentation Follow-Up

1. Keep this review as the canonical execution note for `cug_m4`.
2. Add a short pointer from `docs/cug_paper/PLAN.md` so the run is discoverable
   from the paper coordination doc.
3. Update `docs/filesystem_bundle_eval_issue.md` with the expanded-set M4
   outcome so readers do not over-generalize from the mini smoke wins.
4. If the manuscript mentions the filesystem row, describe it as:
   - an intentionally weaker but still informative retrieval-design comparison,
   - improved over earlier broad-workspace exposure,
   - still unstable on the expanded derived-ticket run.

## Recommended Next Steps

### Paper/result handling

1. Treat `cug_lang_chroma_gptoss_opt` as the canonical GPT-OSS retrieval row for
   the currently completed GPT-OSS subset of the M4 derived-ticket result set.
2. Keep `cug_lang_chroma_gptoss` as an ablation/comparison row, not the lead
   open-weight retrieval result.
3. Include `cug_lang_filesystem_gptoss` wherever the paper is explicitly
   comparing retrieval design choices, but frame it as a weaker file-based
   baseline rather than a preferred operating point.
4. Complete the remaining M4 retrieval reruns before treating the paper's
   retrieval-backed evidence set as fully migrated to the derived corpus.

### Runtime follow-up

1. Investigate the filesystem recursion failures first; they dominate the
   failure mass.
2. Add guardrails against directory reads and inferred nonexistent paths in the
   filesystem tool loop.
3. Add context-budget preflight or truncation safeguards for oversized
   filesystem traces so `max_tokens < 1` failures are prevented earlier.

### Process/documentation follow-up

1. When recording new paper-facing runs, always produce a short run-review note
   like this one alongside the result directory.
2. In the paper plan, distinguish clearly between:
   - milestone/buildout completion,
   - paper-facing evaluation completion,
   - manuscript interpretation readiness.
