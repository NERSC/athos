# CUG Paper Action Plan (Draft v0.4)

This plan is organized around versioned draft deliverables (`v0`, `v1`, etc.) and iterative milestones.

## Status Snapshot (2026-03-15)

- Eval pipeline v1 is implemented and in active use (`run_evaluations.py` + `score_runs.py` + `summarize_results.py`).
- M1 baseline study is complete and remains useful as a small-dataset validation track.
- M2 expanded study is complete for current paper results (`lang_gptoss_base`, `lang_gptoss_chroma`, `lang_sonnet_base`, `lang_sonnet_chroma`).
- M3 paper-facing Chroma-optimized expanded-set runs are complete for:
  - `lang_gptoss_chroma_opt`
  - `lang_sonnet_chroma_opt`
- Filesystem comparison runs are complete for current paper scope, including stitched reruns used to repair provider-quota-contaminated tails.
- SmolAgents comparison is intentionally restricted to the mini-dataset harness slice and is already represented in the manuscript.
- Manuscript drafting is in progress in `../athos_cug_2026_paper`.
- Current manuscript draft already includes substantial content for introduction, related work, toolkit design, and experimental design; results interpretation and conclusion are still incomplete.
- M2 execution required operational patches/reruns (judge retries, provider switch + stitched runs, and Chroma retrieval failure triage), which are recorded below as takeaways for M3 hardening.
- Paper-facing judge swap is complete:
  - canonical runs are rescored with `mistral_large_3`,
  - paper tables/figures and main narrative have been updated to the Mistral-scored artifacts,
  - wrapper defaults are now paper-ready for reproducible rerenders without large command overrides.

## 0. Scope and Configuration Working Points

Purpose:
- Decide the first study scope and the initial configuration working points for experiments.
- Lock initial experiment axes so later analysis is consistent and repeatable.

Deliverables:
- `Scope Memo v0`: included/excluded study axes for first milestone.
- `Study Questions v0`: prioritized questions the experiments must answer.
- `Axes and Working Points v0`: study axes and candidate operating points.
- `Experiment Set v0`: selected experiments for first milestone.
- `Metric Set v0`: scoring, pass threshold, latency/tokens, variance treatment.

Exit criteria:
- Team agreement on first-pass scope, study questions, axes/working points, and selected v0 experiment set.

### Study Questions v0 (Initial)

1. How much can we use open-weight models for HPC ops problems, and when are frontier proprietary models needed?
2. Are coding agents "all you need"? How effective are they, and what additional token/cost overhead do they introduce?
3. Which documentation and information-retrieval mechanisms are most effective, and what are the accuracy vs cost tradeoffs?
4. How effective are the best agent systems for HPC ops problems (state-of-the-art performance on ATHOS benchmarks)?
5. What are the important failure modes in current agentic systems, and what follow-up work do they suggest?
6. How effective are LLMs out-of-box on these benchmarks without tools (model knowledge only)?
7. What is the run-to-run variance of these systems on HPC ops benchmarks?

### Experiment Planning Method (v0)

Step 1: Define study axes and candidate working points.
- Enumerate the dimensions we want to study (model class, agent type, tooling/retrieval mode, etc.).
- For each axis, list candidate working points.
- This is the candidate space, not the immediate run plan.

Step 2: Select the actual `Experiment Set v0`.
- Choose a sparse, signal-rich subset of points that best answer `Study Questions v0`.
- Do not require dense grid sampling in v0.
- Include important non-grid points where needed (example: coding-agent baseline as a single config such as Claude Code Sonnet with file tools).

Selection rule for v0:
- Prioritize experiments expected to produce high information gain for unresolved study questions.
- Defer low-signal combinatorial expansion to later milestones (`M2+`).

## 1. Evaluation Pipeline Upgrade (Enabler Workstream)

Purpose:
- Upgrade evaluation infrastructure to support studies across time, configs, and repeated runs.
- Finish core analysis plumbing early so later experiment expansion is low-friction.

Scope:
- Implement run-first architecture per `docs/eval_pipeline_v2.md`.
- Support incremental run indexing (`--run-count`, `--run-start`).
- Separate execution from judging/scoring.
- Maintain compatibility for importing/scoring external runs.

Deliverables:
- `Pipeline v0`: dual-write mode (legacy summary + canonical per-run outputs).
- `Pipeline v1`: decoupled scoring command over stored runs.
- `Pipeline v1.1`: summarization from run/judgment records with variance outputs.

Exit criteria:
- First full experimental milestone can run and summarize using the upgraded pipeline.

Status update (2026-02-27):
- `Pipeline v0/v1/v1.1` are implemented in repository (`run_evaluations.py`, `score_runs.py`, `import_runs.py`, `summarize_results.py`) with integration coverage.
- Canonical run-path preflight collision checks and decoupled scoring/summarization are in place for repeated runs over time.
- Remaining known limitation: `score_runs.py` currently treats `(dataset_id, case_id)` lookup misses as missing reference, so imported runs with mismatched dataset naming can be skipped (`skipped_missing_reference`).
- Focus has shifted from pipeline buildout to M1 execution hardening and experiment completion.

Status update (2026-03-09):
- Pipeline enabler work is complete for M1/M2 execution needs.
- Remaining work is process/documentation hardening (milestone manifests, closeout checklists, and updated experiment pointers).
- Paper-facing scoring follow-up: rescore archived runs with at least one non-overlapping judge model so evaluation and judgment are not both anchored on GPT-OSS when GPT-OSS is also a system under test.

Status update (2026-03-15):
- Alternate-judge follow-up is complete for current paper scope:
  - `mistral_large_3` rescoring completed for canonical main, filesystem, harness, variance, and external mini result dirs,
  - retry pass cleared transient `skipped_judge_error` cases; remaining skips are execution-status related.

## 1.1 Ticket Ingestion Pipeline (Enabler Workstream)

Purpose:
- Build a Chroma ingestion pipeline for historical ServiceNow ticket JSON + attachments available on filesystem.
- Reuse existing retrieval experiments, datasets, and metrics; no new evaluation dataset track is required.

Scope:
- Extend existing docs ingestion patterns to support ticket corpus ingestion and indexing.
- Support metadata needed for filtering/traceability (ticket id, timestamps, category/service fields, attachment provenance).
- Keep this as an enabler for existing tool-type experiments (semantic retrieval vs file-based retrieval).
- For CUG M1 runs, use `--mode balanced` (exclude `Staff Initiated` and `System Alert Auto Generated`); do not use `full_corpus`.

Deliverables:
- `Ticket Ingestion Pipeline v0`: reproducible ingest from ticket filesystem into Chroma collection(s).
- `Ticket Corpus Manifest v0`: source paths, ingest config, and corpus/version fingerprint used for runs.

Exit criteria:
- Ticket corpus can be indexed and queried by configured semantic retrieval agents in M1 experiments.

Status update (2026-02-27):
- Ticket ingestion pipeline v0 is implemented (`scripts/build_tickets_chroma.py`, `src/athos/utils/ticket_ingest.py`) with filtering modes, truncation/chunk controls, and manifest + corpus fingerprint output.
- Operational wrappers for balanced-mode ingestion and aggregate DB builds are available (`scripts/run_ticket_balanced_full.sh`, `scripts/build_chroma_aggregate.py`, `scripts/run_build_chroma_aggregate.sh`).
- Unit and integration coverage exists for ingestion and aggregate builds, including semantic smoke checks.
- Remaining work is M1 operational execution: produce/freeze versioned corpus manifests and ensure those manifests are attached to run artifacts.

Status update (2026-03-09):
- Aggregate metadata capture in run artifacts is functioning.
- Remaining M1 closeout risk: confirm retrieval collections expected by Chroma-enabled flows are present and consistently named in the selected aggregate DB before freezing retrieval comparisons.

## 2. Dataset Curation (Parallel Workstream)

Purpose:
- Build benchmark-suitable datasets aligned to realistic NERSC support/operations tasks.

### 2.1 Q&A Dataset Expansion

Plan:
- Expand simple Q&A using AI-assisted generation from NERSC sources:
  - docs
  - Iris
  - system outage API

Requirements:
- Questions remain answerable against identifiable source truth.
- Dataset versions are stable and benchmarkable.

Deliverables:
- `QA Dataset v0`: expanded question set with tags/metadata.
- `QA Dataset v1`: quality-reviewed revision after pilot runs.

Status update (2026-03-09):
- Versioned QA files now include `evals/simple_qa.v2.jsonl` and `evals/nersc_qa.v2.jsonl`.
- M2 should explicitly adopt expanded QA coverage centered on `evals/nersc_qa.v2.jsonl`.

### 2.2 User Ticket Dataset Expansion (Single-Turn Scope)

Plan:
- Use AI-assisted synthesis from cached ServiceNow tickets.
- Ensure problem descriptions are detailed enough to solve in a benchmark setting.
- Keep current scope to single-turn ticket scenarios.
- Current benchmark `test_cases` remain the evaluation set for ticket-style scenarios in M1; historical ticket corpus is used as an additional retrieval source, not a separate evaluation dataset.

Requirements:
- Case input is sufficiently specified to avoid ambiguous grading.
- Each case has expected solution/rubric suitable for automated scoring.

Deliverables:
- `Ticket Dataset v0`: synthetic benchmark-ready single-turn set.
- `Ticket Dataset v1`: post-error-analysis revision.

Status update (2026-03-09):
- Single-turn ticket-case datasets are now being exercised in smoke/eval workflows and should be promoted to explicit M2 dataset pointers.
- M2 should use ticket-case datasets as primary ticket-style evaluation input.

### 2.3 Additional Benchmark Categories (Candidate Track)

Candidates:
- SRE tasks (Siqi)
- System utilization metrics tasks (Kadidia)

Deliverables:
- `Category Proposal v0`: definitions, feasibility, and integration notes.
- Optional `Category Pilot v0`: small benchmark slice if ready.

### 2.4 End-to-End / Live-System Tests (Separate Track)

Notes:
- Likely needs different structures/schemas than automated eval datasets.
- Examples: ticket creation workflows, multi-turn scenarios with a human tester.
- Treat as complementary evidence track, not a blocker for automated milestone execution.

Deliverables:
- `E2E Test Plan v0`: scope, prerequisites, and success criteria.

## 3. Experiment Milestones (Versioned)

Principle:
- Milestones establish first working versions; later expansion is expected.

### Milestone M1: Baseline Study v0

Goal:
- Run initial matrix on first curated dataset versions with upgraded pipeline.

Execution gates:
- Build a versioned retrieval aggregate DB for M1 and archive its manifest (docs + consulting docs + balanced tickets).
- Run `evals/run_evaluations.py` with `--aggregate-manifest <path>` so each `run.json` records retrieval corpus provenance in `request.input_artifacts`.
- Record aggregate manifest path/version, dataset pointers, config refs, and git SHA in the M1 run manifest/checklist.

Outputs:
- `Run Artifacts v0`
- `Judgments v0`
- `Summary Tables v0`
- `Failure Analysis Notes v0`

Status (2026-03-10):
- Complete.
- M1 remains a useful small-dataset validation baseline and may be reused for focused follow-on analyses.

### Milestone M2: Expanded Study v1

Goal:
- Incorporate updated configs and/or expanded datasets.

Outputs:
- `Run Artifacts v1`
- `Judgments v1`
- `Summary Tables v1`
- `Execution Takeaways v1` (internal operational notes, not a paper analysis section)

Initial experiment definition (v0, 2026-03-09):
- M2-E1..E4: Repeat M1 flow matrix on expanded datasets:
  - use ticket-case dataset pointer(s),
  - use expanded QA set (`evals/nersc_qa.v2.jsonl`).
- M2-E5 (variance): run top two M1 configurations with `--run-count 3` (or higher as budget allows) on expanded datasets.
- M2-E6 (external baseline carry-forward): import and score external coding-agent runs with dataset IDs aligned to local references.
- Retrieval gate for any Chroma-enabled M2 run: require a preflight smoke check that verifies expected collection names exist in the selected aggregate DB.

Status (2026-03-10):
- Complete for current paper result set:
  - `lang_gptoss_base`
  - `lang_gptoss_chroma`
  - `lang_sonnet_base`
  - `lang_sonnet_chroma`
- Canonical analysis artifact is materialized at `results/cug_m2_canonical` (copy-based snapshot) with:
  - selected run trees under `athos/<config_id>/.../run.json` for the four paper configs,
  - centralized judgment files under `results/cug_m2_canonical/judgments/`,
  - provenance manifests under `results/cug_m2_canonical/manifests/`:
    - `canonical_manifest.json`
    - `all_runs.manifest.txt`
    - `judgments_manifest.json`

M2 execution takeaways (to inform M3):
- Scoring failures required patching by enabling judge retries.
- `lang_sonnet_chroma` hit CBorg quota mid-run; remaining runs used AmSC I2 API and were materialized into stitched outputs via `scripts/materialize_stitched_sonnet_runs.py`.
- A large number of Chroma flow evals failed on collection retrieval; LangChain flow behavior currently aborts if a wrong collection name is retrieved.
- Evals were slowed because chroma-mcp `uvx` environments were created repeatedly; move to a local `chroma-mcp` install in the ATHOS environment for M3.

### Milestone M3: Pre-Write Freeze v1.x

Goal:
- Freeze experiment set used for manuscript results sections.

Outputs:
- `Result Freeze Manifest`
- `Figure/Table Pack v1.x`

Execution scope update (2026-03-11):
- Variance study scope is explicitly small-dataset (M1 datasets) for faster repeated runs:
  - datasets: `evals/test_cases` + `evals/simple_qa.jsonl`
  - flows: `cug_lang_chroma_gptoss_opt`, `cug_lang_chroma_sonnet_opt`
  - run policy target: `run_count=10` (adjust downward only for quota/runtime constraints).
- Full expanded-dataset (`evals/nersc_qa.v2.jsonl` + ticket cases) runs are still required for current paper-facing configs:
  - `cug_lang_chroma_gptoss_opt`
  - `cug_lang_chroma_sonnet_opt`
  - `cug_smol_chroma_gptoss`
  - `cug_lang_filesystem_gptoss`
- SmolAgents comparison-row alignment for M3:
  - treat the built-in SmolAgents coding prompt/behavior as part of the harness,
  - align the ATHOS-authored retrieval instructions with the LangChain optimized Chroma prompt,
  - keep the SmolAgents retrieval tool surface restricted to the same read-only five-tool subset used by paper-facing LangChain Chroma runs.
  - if `gptoss` underperforms materially in the SmolAgents harness, add a `claude_sonnet` SmolAgents comparison row as a model-fit calibration point rather than treating the GPT-OSS result as harness-conclusive by itself.
- Paper-eval guardrail: filesystem MCP usage for `cug_lang_filesystem_gptoss` is restricted via MCP tool filtering (`allowed_tools` + `blocked_tools`) to read-only operations.
- Filesystem paper-config note (2026-03-12):
  - the canonical filesystem row now uses a frozen bundle rooted at `${ATHOS_WORKSPACE}/file_retrieval_corpus`, not raw whole-workspace filesystem exposure
  - the bundle is intended to provide a fairer and more reproducible file-based retrieval baseline by narrowing the corpus to task-relevant sources and adding a generated `INDEX.md`
- Paper-eval guardrail (Chroma): for current M3 paper runs, do not expose `chroma_peek_collection` in active retrieval toolsets.
  - Finding from M3 smoke: in MCP/LangChain path, `chroma_peek_collection` intermittently failed with serialization errors (`numpy.ndarray` in tool result).
  - Mitigation applied in current configs: retrieval runs use `list/query/get/info/count` subset and exclude `peek`.

Status update (2026-03-12):
- Complete for the scoped paper experiment set.
- Full expanded-dataset paper-facing Chroma-optimized LangChain runs are complete:
  - `cug_m3_full_gptoss_opt_20260311_013848`
  - `cug_m3_full_sonnet_opt_20260311_081645`
- Small-dataset variance run for `cug_lang_chroma_gptoss_opt` completed via collaborator handoff:
  - artifact root: `madan_results/cug_m3_var_20260312_093435`
  - complete run tree: `120` run artifacts across `evals/test_cases` + `evals/simple_qa.jsonl`
  - observed execution/output failures retained in analysis: `3`
    - `simple_qa/nersc_ai_support_group/2`: provider-side `BadRequestError` (`max_tokens` became negative)
    - `test_cases/pytorch-launch-error/0`: retrieval tool queried nonexistent collection `perlmutter_ddp_guides`
    - `test_cases/pytorch-launch-error/1`: empty model response (`invalid_output`)
- Small-dataset variance run for `cug_lang_chroma_sonnet_opt` completed via collaborator handoff:
  - artifact root: `madan_results/cug_m3_var_20260312_130318`
  - complete run tree: `120` run artifacts across `evals/test_cases` + `evals/simple_qa.jsonl`
  - execution/output failures: `0`
- SmolAgents scope decision:
  - comparison is intentionally limited to the mini-dataset harness slice rather than expanded-dataset sweeps
  - those results are already reflected in the paper as auxiliary comparison evidence, not as part of the main six-row LangChain table
- Filesystem status update (2026-03-12):
  - the bundle-backed `cug_lang_filesystem_gptoss` mini QA smoke now completed cleanly with `run_count=5`, `skipped_count=0`, `score_mean=99.0`, `pass_rate=1.0`
  - this is sufficient to treat the bundle-backed config as the canonical filesystem paper configuration for next-stage experiments
  - the remaining open question is larger-scale behavior once tickets are added back into the bundle
- Filesystem status update (2026-03-13):
  - ticket-inclusive mini QA smoke for the same canonical config completed with `run_count=5`, `skipped_count=1`, `score_mean=80.0`, `pass_rate=0.8`
  - the skipped case was `nersc_ai_support_group` (`ToolException`, `EISDIR`)
  - interpretation for paper purposes: corpus shaping plus `INDEX.md` guidance makes file-based retrieval viable, but broader heterogeneous corpora still reintroduce some navigation/tool-use brittleness for GPT-OSS
- Filesystem status update (2026-03-14, Sonnet stitched canonical result):
  - canonical stitched artifact root: `results/cug_m3_fs_sonnet_stitched_20260314`
  - clean paper-facing judgments dir: `results/cug_m3_fs_sonnet_stitched_20260314/judgments_final`
  - flow/config lineage: `cug_lang_filesystem_sonnet__claude_sonnet__91ee9a56`
  - source runs merged into the stitched artifact:
    - ticket baseline: `results/cug_m3_fs_sonnet_tickets_20260313_145140`
    - ticket quota-retry subset: `results/cug_m3_fs_sonnet_tickets_20260313_145140_retry_badrequest`
    - QA baseline: `results/cug_m3_smoke_20260313_145034`
    - QA budget-retry subset: `results/cug_m3_smoke_20260313_145034_retry_budget`
  - stitched aggregate summary from `aggregates_final/summary.json`:
    - `nersc_qa.v2`: `run_count=123`, `skipped_count=1`, `score_mean=78.76`, `pass_rate=0.7236`
    - `ticket_cases`: `run_count=156`, `skipped_count=14`, `score_mean=72.31`, `pass_rate=0.6538`
  - retry outcome:
    - all `16` quota-hit QA cases were successfully repaired via bounded rerun
    - `8` of the `9` quota-hit ticket cases were repaired; `INC0248658_portal_hpss_degraded_access` still failed on rerun with `GraphRecursionError`
  - paper interpretation:
    - use this stitched experiment as the canonical Sonnet filesystem paper source instead of the raw collaborator QA run
    - the remaining skips now mostly reflect actual execution failures, not quota-tail contamination
- Execution status note (2026-03-14):
  - scoped experiment execution for the paper is complete
  - remaining work in this branch is manuscript synchronization and plan/documentation cleanup, not additional ATHOS experiment runs
  - focused coding-agent mini comparison work is complete and reflected in the manuscript harness-comparison section

Variance-run bookkeeping note (2026-03-12):
- Current scoring/summarization behavior intentionally penalizes execution/output failures with `score = 0` rather than dropping them from aggregate metrics.
- Those same records still carry `judgment_status = skipped_execution_status`, so current `summary.json` files can report internally inconsistent `scored_count` / `skipped_count` combinations even when the visible pass/score/fail table values remain aligned with the intended interpretation.
- For the paper deadline, keep behavior unchanged and interpret current `skipped_count` in variance summaries/tables as execution-failure count.
- Post-deadline cleanup is tracked in GitHub issue `#87`.

Variance failure-analysis note (2026-03-12):
- In the collaborator-run Sonnet variance artifact (`madan_results/cug_m3_var_20260312_130318`), `test_cases/salloc-account-error` failed consistently across all `10` attempts.
- All runs executed successfully and were scored, so this is not an execution-stability issue.
- Repeated failure pattern:
  - the model retrieved evidence (`chroma_list_collections` + `chroma_query_documents`) and then diagnosed the issue as missing Perlmutter `salloc` flags such as `--qos interactive` and `--constraint`
  - the benchmark reference solution instead attributes the error to lack of authorization for the `desi` allocation account and recommends checking `iris` / `groups` and contacting the PI if needed
- Candidate paper takeaway:
  - retrieval can reinforce the wrong explanation when multiple sources share the same surface error string
  - this case is a useful example of retrieval-driven misdiagnosis rather than pure model hallucination or infrastructure failure

## 4. Analysis and Writing

Purpose:
- Convert milestone outputs into manuscript-ready evidence and narrative.

Deliverables:
- `Analysis Narrative v0`: takeaways, limitations, and key caveats.
- `Paper Draft v0`: complete section draft aligned with milestone evidence.
- `Paper Draft v1`: revised draft with updated milestone outputs.
- `Judge Sensitivity Note v0`: rescore the paper-facing result set with an alternate judge and briefly assess whether headline conclusions remain stable across judge choice.

Status update (2026-03-11):
- Manuscript drafting is active in `../athos_cug_2026_paper`.
- `Paper Draft v0` is in progress with substantial draft text already written for:
  - Introduction
  - Related Work
  - ATHOS Toolkit Design
  - Experimental Design
- Results section structure and table integration are in place, including `tables/cug_results_per_config.tex`, but narrative interpretation is still incomplete.
- Conclusion remains placeholder-level and needs to be written.
- Near-term writing work should focus on:
  - main results interpretation from the six-row LangChain table,
  - discussion of robustness/failure modes and retrieval tradeoffs,
  - conclusion/limitations/future work,
  - cleanup of ACM metadata/front matter placeholders.

Status update (2026-03-12):
- Repeated-run variance figure using collaborator-provided GPT-OSS and Sonnet artifacts is now integrated into `../athos_cug_2026_paper/main.tex` as a dedicated subsection with side-by-side subfigures.
- Current variance writeup anchors three points that should be preserved in later edits:
  - GPT-OSS shows broader dispersion and a small number of execution/output failures that are retained in the variance story
  - Sonnet is operationally cleaner in this repeated-run slice but still exhibits a stable retrieval-driven semantic failure on `salloc-account-error`
  - reliability differences are case-specific and should not be collapsed to overall mean score alone
- Judge follow-up:
  - try at least one alternate judge configuration/model for the paper-facing result set
  - main motivation is to avoid having GPT-OSS evaluate GPT-OSS if the alternate judge produces reasonable results
  - a broader judge-sensitivity study would add value, but remains optional rather than a paper blocker

Status update (2026-03-13):
- Judge-model sensitivity should be treated as an explicit paper-quality check, not only an eval harness detail.
- Preferred next step is to rescore existing canonical runs with one or more judge models that are different from the evaluated model family, then compare score/pass deltas and any ranking changes.
- If stable, this becomes evidence that the current conclusions are judge-robust; if not, it becomes a useful mini study and a limitation note.

Status update (2026-03-15):
- Judge swap execution and write-up alignment are complete for the current submission path:
  - main paper outputs now use Mistral-judged artifacts,
  - manuscript claims were updated to match regenerated table/figure values,
  - a deeper multi-judge study remains optional follow-up work.

### Manuscript Status Snapshot

Status update (2026-03-11):
- Manuscript repo: `../athos_cug_2026_paper`
- Main draft file: `main.tex`
- Drafted sections with substantial prose:
  - Introduction
  - Related Work
  - ATHOS Toolkit Design
  - Experimental Design
- Results assets already wired into manuscript:
  - per-config results table via `tables/cug_results_per_config.tex`
  - architecture/execution figures
- Sections still needing major writing:
  - Results narrative/interpretation
  - Conclusion
  - limitations/future-work refinement
- Publication polish still pending:
  - ACM front matter placeholders
  - final figure/table captions and references
  - acknowledgments/bibliography cleanup as needed

### Paper Limitations To Capture

- Dataset scope:
  - current benchmark coverage is selective rather than comprehensive,
  - the paper emphasizes Q&A and single-turn ticket-style cases and does not yet establish performance on broader multi-turn, live-operations, or human-in-the-loop workflows.
- Judge-model coverage:
  - paper-facing outputs now use a non-overlapping Mistral judge for scoring instead of GPT-OSS judging GPT-OSS,
  - limitation shifts from overlap risk to breadth of sensitivity: only one alternate judge has been run across full paper scope so far.
- Retrieval corpus bias:
  - retrieval results depend in part on corpus construction choices, including what documentation/tickets were included, how they were filtered, and how they were chunked/indexed,
  - observed gains or failures should therefore be interpreted as model-plus-retrieval-stack behavior, not as model capability in isolation.
- Prompt-engineering scope:
  - this paper does not include extensive prompt optimization,
  - only limited trial-and-error prompt iteration was used for selected configurations (notably LangChain optimized retrieval configs and filesystem configs),
  - no judge-model prompt tuning was performed beyond the current rubric prompt/version choices.
- Production-readiness boundary:
  - current results should not be interpreted as sufficient validation for production deployment in HPC operations settings,
  - substantial additional validation is still required before claiming readiness for production systems.

## 5. Versioning and Change Control

Rules:
- Every dataset/config/pipeline revision gets a version tag.
- Milestone outputs record config refs, dataset versions, and git SHA.
- New experiments after a milestone roll into the next milestone version.

Policy:
- Preserve previous milestone artifacts for traceability.
- Do not silently replace milestone outputs.

## Immediate Next Steps (Updated 2026-03-15)

Execution track:
1. Freeze the scoped paper experiment set as complete and keep any further runs explicitly out of scope unless they are needed to repair a documented artifact.
2. Carry forward the completed M1 harness comparison:
   - `langchain + claude_sonnet` was strongest,
   - `smolagents + claude_sonnet` was competitive but weaker and more token-expensive,
   - both `gptoss` rows underperformed materially, with `smolagents + gptoss` weakest.
3. Preserve the bundle-backed filesystem setup as the canonical paper lineage and use the stitched Sonnet artifact as the paper-facing filesystem source.
4. For quota-sensitive Sonnet filesystem runs, prefer bounded reruns over full reruns when the artifact pattern shows a likely provider-exhaustion tail.
5. Keep alternate-judge rescoring frozen for submission unless a documented artifact repair is needed.
6. For external coding-agent baselines, use `scripts/score_cug_external.sh` as the canonical scorer wrapper (default paper config: `config/paper/cug_m1.yaml` for mini-harness comparisons).
7. Treat the focused external coding-agent mini comparison as complete for paper scope; keep any further coding-agent runs explicitly out of scope unless needed to repair artifacts.

Writing track:
1. Keep the current Mistral-aligned tables/figures/narrative frozen unless a documented artifact repair is needed.
2. Build and sanity-check the final PDF against current paper artifacts (tables/figures/narrative all Mistral-aligned).
3. Do a final manuscript pass for ACM metadata/front matter polish, captions, and references.
4. If space allows, add one representative benchmark example (prompt + reference solution; optional appendix with model/judge excerpt).
5. Preserve the short judge-sensitivity note as a robustness check:
   - motivation: reduce judge overlap risk and test headline stability,
   - method: rescore fixed stored outputs under alternate judge(s),
   - current status: one alternate full-scope judge (`mistral_large_3`) completed.
6. Keep filesystem and SmolAgents rows framed as secondary/diagnostic comparisons relative to the main six-row LangChain table.

Post-deadline follow-up candidate (not required for current submission deadline):
- Human adjudication mini-study:
  - sample a small set of cases with the largest judge-to-judge disagreements,
  - collect blinded human scores/comments,
  - compare human alignment versus automated judges and report as a follow-up hardening study.
- Third-judge sensitivity extension:
  - staged `llama-4-maverick` rescore plan is documented in `docs/cug_paper/JUDGE_SENSITIVITY_MAVERICK_PLAN.md`,
  - Phase 1-3 status (mini harness + external mini + expanded optimized rows) is now complete,
  - no judge-format reruns were needed in those phases (`skipped_judge_error=0` observed),
  - next decision is whether to finish full Maverick artifact swap (remaining 1914 runs) or keep Maverick as a targeted sensitivity addendum.

## M3 Execution Log (2026-03-11)

- Sonnet QA smoke (simple_qa only):
  - experiment: `cug_m3_smoke_20260311_013258`
  - runs path: `results/cug_m3_smoke_20260311_013258`
  - flow: `cug_lang_chroma_sonnet_opt`
- SmolAgents GPTOSS QA smoke (simple_qa only):
  - experiment: `cug_m3_smoke_20260311_204913`
  - runs path: `results/cug_m3_smoke_20260311_204913`
  - flow: `cug_smol_chroma_gptoss`
  - summary:
    - `simple_qa`: `run_count=5`, `skipped_count=0`, `pass_rate=0.4`, `score_mean=49.0`
  - takeaway:
    - run stability was acceptable, but answer quality was poor and token use was high; do not treat this row alone as harness-conclusive.
- SmolAgents Sonnet QA smoke (simple_qa only):
  - experiment: `cug_m3_smoke_20260311_205923`
  - runs path: `results/cug_m3_smoke_20260311_205923`
  - flow: `cug_smol_chroma_sonnet`
  - summary:
    - `simple_qa`: `run_count=5`, `skipped_count=0`, `pass_rate=1.0`, `score_mean=95.0`
  - takeaway:
    - strong Sonnet smoke supports interpreting the weak GPTOSS SmolAgents row as a model-fit issue rather than a blanket SmolAgents failure.
- Four-way M1 harness comparison (LangChain vs SmolAgents; GPTOSS vs Sonnet):
  - experiment: `cug_m3_var_20260311_231139`
  - runs path: `results/cug_m3_var_20260311_231139`
  - datasets: `evals/test_cases` + `evals/simple_qa.jsonl`
  - flows:
    - `cug_lang_chroma_gptoss_opt`
    - `cug_lang_chroma_sonnet_opt`
    - `cug_smol_chroma_gptoss`
    - `cug_smol_chroma_sonnet`
  - overall ranking across 12 M1 cases per config:
    - `cug_lang_chroma_sonnet_opt`: overall `score_mean=89.33`, `pass_rate=0.917`
    - `cug_smol_chroma_sonnet`: overall `score_mean=80.67`, `pass_rate=0.750`
    - `cug_lang_chroma_gptoss_opt`: overall `score_mean=63.17`, `pass_rate=0.583`
    - `cug_smol_chroma_gptoss`: overall `score_mean=43.50`, `pass_rate=0.333`
  - dataset-level notes:
    - `simple_qa`: `lang_sonnet` `96.0/1.0`, `smol_sonnet` `94.0/0.8`, `lang_gptoss` `80.0/0.8`, `smol_gptoss` `66.0/0.6`
    - `test_cases`: `lang_sonnet` `84.57/0.857`, `smol_sonnet` `71.14/0.714`, `lang_gptoss` `51.14/0.429`, `smol_gptoss` `27.43/0.143`
  - interpretation:
    - model choice dominated harness choice on M1 datasets;
    - LangChain outperformed SmolAgents at both model tiers;
    - the gap was much smaller with Sonnet than with GPTOSS;
    - SmolAgents rows were materially more token-expensive, especially on `test_cases`;
    - repeated hard cases across harnesses included `salloc-account-error` and `pytorch-launch-error-2`.
- GPTOSS full expanded-set run:
  - experiment: `cug_m3_full_gptoss_opt_20260311_013848`
  - runs path: `results/cug_m3_full_gptoss_opt_20260311_013848`
  - flow: `cug_lang_chroma_gptoss_opt`
  - datasets: `evals/nersc_qa.v2.jsonl` + `ticket_cases`
  - summary:
    - `nersc_qa.v2`: `run_count=123`, `skipped_count=7` (`5.7%`), `pass_rate=0.7317`, `score_mean=78.47`
    - `ticket_cases`: `run_count=156`, `skipped_count=7` (`4.5%`), `pass_rate=0.7308`, `score_mean=76.43`
  - notable failure classes seen in run logs: `GraphRecursionError`, invalid tool-argument schema for `chroma_get_documents`, invalid/nonexistent collection names.
  - artifact pointers:
    - `results/cug_m3_full_gptoss_opt_20260311_013848/aggregates/summary.json`
    - `results/cug_m3_full_gptoss_opt_20260311_013848/judgments/gptoss_rubric_v1.skips.jsonl`
- External Codex mini baseline (imported run scoring path):
  - experiment: `cug_codex_external_mini_20260313_232712`
  - runs path: `results/cug_codex_external_mini_20260313_232712`
  - scorer wrapper: `scripts/score_cug_external.sh`
  - scoring config: `config/paper/cug_m1.yaml`
  - execution command:
    - `EXPERIMENT_ID=cug_codex_external_mini_20260313_232712 scripts/score_cug_external.sh`
  - output artifacts:
    - `results/cug_codex_external_mini_20260313_232712/judgments/gptoss_rubric_v1.jsonl`
    - `results/cug_codex_external_mini_20260313_232712/aggregates/summary.json`
  - implementation note:
    - wrapper summarizes from `--judgment-file` (single judge output) to avoid mixed-judge collisions when `judgments/` contains older judge files.
- External Claude Code mini baseline (imported run scoring path):
  - experiment: `cug_claude_external_mini_20260314`
  - runs path: `results/cug_claude_external_mini_20260314`
  - scorer wrapper: `scripts/score_cug_external.sh`
  - scoring config: `config/paper/cug_m1.yaml`
  - execution command:
    - `EXTERNAL_RUNS_INPUT=results/external_runs/claude_code_fs_bundle_v1_mini_20260314.success_only.jsonl EXPERIMENT_ID=cug_claude_external_mini_20260314 scripts/score_cug_external.sh`
  - summary highlights:
    - `simple_qa`: `run_count=5`, `pass_rate=0.8`, `score_mean=85.0`, `tokens_total_mean=79299.0`, `latency_ms_mean=13614.2`
    - `test_cases`: `run_count=7`, `pass_rate=0.7143`, `score_mean=79.0`, `tokens_total_mean=193367.14`, `latency_ms_mean=51739.43`
  - implementation notes:
    - some successful Claude CLI responses can return empty top-level `result` while still returning `structured_output.answer`;
    - `score_cug_external.sh` now normalizes missing `response.output_text` from `provenance.raw_stdout` before import;
    - cache-aware token accounting is now applied in `evals/summarize_results.py` so external rows are comparable with provider-reported cached-token usage.
- Sonnet full expanded-set run:
  - experiment: `cug_m3_full_sonnet_opt_20260311_081645`
  - runs path: `results/cug_m3_full_sonnet_opt_20260311_081645`
  - flow: `cug_lang_chroma_sonnet_opt`
  - datasets: `evals/nersc_qa.v2.jsonl` + `ticket_cases`
  - summary:
    - `nersc_qa.v2`: `run_count=123`, `skipped_count=0` (`0.0%`), `pass_rate=0.7967`, `score_mean=84.34`
    - `ticket_cases`: `run_count=156`, `skipped_count=1` (`0.6%`), `pass_rate=0.8333`, `score_mean=84.11`
  - skip detail:
    - single skipped case: `INC0241968_spin_filesystem_postgres_mismatch` (`execution_error`, provider `400`).
  - artifact pointers:
    - `results/cug_m3_full_sonnet_opt_20260311_081645/aggregates/summary.json`
    - `results/cug_m3_full_sonnet_opt_20260311_081645/judgments/gptoss_rubric_v1.skips.jsonl`

## Main Table Scope Decision (2026-03-11)

Primary manuscript results table should include six LangChain configurations:
- M2 baseline/no-tool rows:
  - `lang_gptoss_base`
  - `lang_sonnet_base`
- M2 Chroma rows:
  - `lang_gptoss_chroma`
  - `lang_sonnet_chroma`
- M3 Chroma-optimized rows:
  - `lang_gptoss_chroma_opt` (from `cug_m3_full_gptoss_opt_20260311_013848`)
  - `lang_sonnet_chroma_opt` (from `cug_m3_full_sonnet_opt_20260311_081645`)

Secondary comparison rows:
- `lang_gptoss_filesystem` from `results/cug_m3_20260313_080148`
- `lang_sonnet_filesystem` from `results/cug_m3_fs_sonnet_stitched_20260314`

Reporting note:
- Keep `Eval/Skip` (or equivalent execution-success visibility) in the table so M2 vs M3 robustness differences are explicit.
- If the filesystem row is discussed, describe it as a bundle-backed file-retrieval baseline rather than generic whole-workspace filesystem access.
