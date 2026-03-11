# CUG Paper Action Plan (Draft v0.3)

This plan is organized around versioned draft deliverables (`v0`, `v1`, etc.) and iterative milestones.

## Status Snapshot (2026-03-10)

- Eval pipeline v1 is implemented and in active use (`run_evaluations.py` + `score_runs.py` + `summarize_results.py`).
- M1 baseline study is complete and remains useful as a small-dataset validation track.
- M2 expanded study is complete for current paper results (`lang_gptoss_base`, `lang_gptoss_chroma`, `lang_sonnet_base`, `lang_sonnet_chroma`).
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

## 4. Analysis and Writing

Purpose:
- Convert milestone outputs into manuscript-ready evidence and narrative.

Deliverables:
- `Analysis Narrative v0`: takeaways, limitations, and key caveats.
- `Paper Draft v0`: complete section draft aligned with milestone evidence.
- `Paper Draft v1`: revised draft with updated milestone outputs.

## 5. Versioning and Change Control

Rules:
- Every dataset/config/pipeline revision gets a version tag.
- Milestone outputs record config refs, dataset versions, and git SHA.
- New experiments after a milestone roll into the next milestone version.

Policy:
- Preserve previous milestone artifacts for traceability.
- Do not silently replace milestone outputs.

## Immediate Next Steps (Updated 2026-03-10)

1. Define M3 experiment scope with explicit separation between paper-facing analyses and internal operational validation outputs.
2. Optimize Chroma configs and patch LangChain retrieval handling so wrong/missing collection names do not hard-abort entire cases.
3. Move Chroma MCP usage from repeated `uvx` setup to a local `chroma-mcp` install inside the ATHOS runtime environment.
4. Plan/run the variability study (likely on small datasets first, potentially reusing M1 datasets for fast iteration).
5. Add a small smol-flow comparison track (potentially on M1 datasets) as a targeted M3 extension.
