# CUG Paper Action Plan (Draft v0.1)

This plan is organized around versioned draft deliverables (`v0`, `v1`, etc.) and iterative milestones.

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
- Keep legacy compatibility while migrating.

Deliverables:
- `Pipeline v0`: dual-write mode (legacy summary + canonical per-run outputs).
- `Pipeline v1`: decoupled scoring command over stored runs.
- `Pipeline v1.1`: summarization from run/judgment records with variance outputs.

Exit criteria:
- First full experimental milestone can run and summarize using the upgraded pipeline.

Status update (2026-02-22):
- Core pipeline upgrades for canonical per-run artifacts, decoupled scoring, and run-path preflight collision checks are implemented.
- Remaining known limitation: `score_runs.py` currently treats `(dataset_id, case_id)` lookup misses as missing reference, so imported runs with mismatched dataset naming can be skipped (`skipped_missing_reference`).

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

Outputs:
- `Run Artifacts v0`
- `Judgments v0`
- `Summary Tables v0`
- `Failure Analysis Notes v0`

### Milestone M2: Expanded Study v1

Goal:
- Incorporate updated configs and/or expanded datasets.

Outputs:
- `Run Artifacts v1`
- `Judgments v1`
- `Summary Tables v1` (with variance where applicable)
- `Delta Analysis v1` versus M1

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
- `Analysis Narrative v0`: takeaways, limitations, and open risks.
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

## Immediate Next Steps

1. Write `Scope Memo v0` and `Experiment Matrix v0` from current configs.
2. Run M1 baseline experiments using pipeline v1 artifacts (canonical runs + decoupled judgments).
3. Start `QA Dataset v0` and `Ticket Dataset v0` curation in parallel.
4. Define M1 checklist and target date, including explicit tracking for `skipped_missing_reference` rates on imported runs.
