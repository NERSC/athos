# CUG Paper Action Plan (Draft v0.4)

This plan is organized around versioned draft deliverables (`v0`, `v1`, etc.) and iterative milestones.

## Status Snapshot (2026-03-11)

- Eval pipeline v1 is implemented and in active use (`run_evaluations.py` + `score_runs.py` + `summarize_results.py`).
- M1 baseline study is complete and remains useful as a small-dataset validation track.
- M2 expanded study is complete for current paper results (`lang_gptoss_base`, `lang_gptoss_chroma`, `lang_sonnet_base`, `lang_sonnet_chroma`).
- M3 paper-facing Chroma-optimized expanded-set runs are complete for:
  - `lang_gptoss_chroma_opt`
  - `lang_sonnet_chroma_opt`
- Manuscript drafting is in progress in `../athos_cug_2026_paper`.
- Current manuscript draft already includes substantial content for introduction, related work, toolkit design, and experimental design; results interpretation and conclusion are still incomplete.
- M2 execution required operational patches/reruns (judge retries, provider switch + stitched runs, and Chroma retrieval failure triage), which are recorded below as takeaways for M3 hardening.

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
- Partially complete.
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
- Remaining execution work for M3 is:
  - full expanded-dataset comparison runs for SmolAgents rows (`cug_smol_chroma_gptoss`, optional `cug_smol_chroma_sonnet`),
  - optional filesystem row completion for `cug_lang_filesystem_gptoss` if stability is acceptable.
- Filesystem status update (2026-03-12):
  - the bundle-backed `cug_lang_filesystem_gptoss` mini QA smoke now completed cleanly with `run_count=5`, `skipped_count=0`, `score_mean=99.0`, `pass_rate=1.0`
  - this is sufficient to treat the bundle-backed config as the canonical filesystem paper configuration for next-stage experiments
  - the remaining open question is larger-scale behavior once tickets are added back into the bundle

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

## 5. Versioning and Change Control

Rules:
- Every dataset/config/pipeline revision gets a version tag.
- Milestone outputs record config refs, dataset versions, and git SHA.
- New experiments after a milestone roll into the next milestone version.

Policy:
- Preserve previous milestone artifacts for traceability.
- Do not silently replace milestone outputs.

## Immediate Next Steps (Updated 2026-03-11)

Execution track:
1. Run the remaining full expanded-dataset comparison sweeps for SmolAgents rows and `cug_lang_filesystem_gptoss`.
2. Keep retrieval preflight gates active for Chroma runs (collection-name verification and representative smoke queries).
3. Carry forward the completed M1 harness comparison:
   - `langchain + claude_sonnet` was strongest,
   - `smolagents + claude_sonnet` was competitive but weaker and more token-expensive,
   - both `gptoss` rows underperformed materially, with `smolagents + gptoss` weakest.
4. If filesystem retrieval underperforms, iterate only the filesystem system prompt and rerun the same config id lineage with clear versioned provenance.
5. Use `scripts/run_cug_m3_smoke.sh` for QA-only (`evals/simple_qa.jsonl`) M3 functional smoke runs with built-in scoring/summarization when adding new optional comparison rows.
6. For filesystem experiments, preserve the bundle-backed setup as the canonical config lineage and vary corpus contents via bundle assembly rather than reverting to raw workspace exposure.

Writing track:
1. Turn the six-row LangChain main-results table into manuscript narrative in `../athos_cug_2026_paper/main.tex`.
2. Add explicit discussion of execution robustness and skip-rate differences so M2 vs M3 stability improvements are visible.
3. Write conclusion, limitations, and future-work sections based on current M1/M2/M3 evidence.
4. Decide whether SmolAgents and filesystem rows are mature enough for inclusion beyond the main six-row table.
5. Clean up ACM front matter placeholders and finalize figure/table references as the manuscript approaches submission quality.
6. Capture the main file-based retrieval lesson in the manuscript discussion:
   - weaker models benefited substantially from explicit corpus shaping and navigational scaffolding (`file_retrieval_corpus` + `INDEX.md`), not just access to filesystem tools.

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

Optional rows:
- `lang_gptoss_filesystem` may be included only if execution stability is brought to an acceptable level on expanded datasets.

Reporting note:
- Keep `Eval/Skip` (or equivalent execution-success visibility) in the table so M2 vs M3 robustness differences are explicit.
- If the filesystem row is discussed, describe it as a bundle-backed file-retrieval baseline rather than generic whole-workspace filesystem access.
