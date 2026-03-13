# Collaborator Eval Setup Guide

For the external standalone-agent baseline workflow, see `docs/cug_paper/CLAUDE_CODE_EVAL_GUIDE.md`.

This guide is for running the M3 variance experiment in a clean repo-local setup.

## Assignment

Primary task:
- run the M3 variance study for `cug_lang_chroma_gptoss_opt`
- datasets: `evals/test_cases` + `evals/simple_qa.jsonl`
- target run policy: `run_count=10`

Use a short smoke run first, then launch the full repeated run.

## Expected repo layout

Clone the repo in `pscratch` and keep the working folders local to that checkout:

```text
athos/
  config/
  data/
  docs/
  evals/
  results/
  workspace/
```

## What you will receive

You will receive a single tarball containing:
- `workspace/`
- `data/chroma/aggregates/manifests/athos_eval_bundle_20260306_local.json`

The bundled `workspace/` is already prepared for the retrieval-backed evals.

## Install the bundle

From the repo root:

```bash
mkdir -p data results
tar -xzf /path/to/athos_m3_variance_bundle.tar.gz
```

After unpacking, you should have:

```text
workspace/
data/chroma/aggregates/manifests/athos_eval_bundle_20260306_local.json
```

## Configure `.env`

Do not set the workspace path manually in each shell. Put it in `.env`.

If `.env` does not exist yet:

```bash
cp .env.template .env
```

Then edit `.env` so it includes:

```bash
ATHOS_WORKSPACE=./workspace
AGGREGATE_MANIFEST=./data/chroma/aggregates/manifests/athos_eval_bundle_20260306_local.json
```

Notes:
- `ATHOS_WORKSPACE=./workspace` keeps the workspace local to the repo.
- `AGGREGATE_MANIFEST` is used for provenance when running the paper evals.
- CBORG settings should already be working in your environment if you can run the basic `athos` CLI.

## Environment

On NERSC:

```bash
ml conda
conda activate athos
```

If your shell does not automatically load `.env`, run:

```bash
set -a
source .env
set +a
```

That exports the variables from `.env` into the current shell.

## Quick validation

Check that the expected workspace content exists:

```bash
ls workspace
ls workspace/chroma
```

Smoke-check the Chroma DB:

```bash
set -a
source .env
set +a

ATHOS_CHROMA_INTEGRATION=1 \
ATHOS_CHROMA_EXPECTED_COLLECTION=docs \
pytest tests/integration/tools/chroma/test_workspace_chroma_smoke.py
```

Optional stronger check:

```bash
set -a
source .env
set +a

python - <<'PY'
import os
from pathlib import Path
import chromadb

workspace = Path(os.environ["ATHOS_WORKSPACE"])
client = chromadb.PersistentClient(path=str(workspace / "chroma"))
names = sorted(c.name for c in client.list_collections())
print(names)
missing = {"docs", "consulting_docs", "tickets"} - set(names)
if missing:
    raise SystemExit(f"Missing collections: {sorted(missing)}")
PY
```

## Smoke run

Run one short validation pass before launching the repeated run:

```bash
RUN_COUNT=1 FLOWS="cug_lang_chroma_gptoss_opt" scripts/run_cug_m3_var.sh
```

This is just to confirm:
- the workspace is wired correctly
- retrieval works
- canonical `run.json` output is being written
- scoring and summary complete successfully

## Full M3 variance run

After the smoke run succeeds:

```bash
RUN_COUNT=10 FLOWS="cug_lang_chroma_gptoss_opt" scripts/run_cug_m3_var.sh
```

If you need to append runs later without overwriting previous ones:

```bash
EXPERIMENT_ID=<existing_experiment_id> \
RUN_START=5 \
RUN_COUNT=5 \
FLOWS="cug_lang_chroma_gptoss_opt" \
scripts/run_cug_m3_var.sh
```

## Output to share back

The script prints the run directory it used at the end. When the variance run completes successfully, share back that experiment directory under `results/`.

Typical example:

```bash
results/cug_m3_var_<timestamp>
```

That experiment directory should contain:
- canonical `run.json` trees
- judgments output
- summary output

## Common failure modes

1. `aggregate manifest not found`
- confirm that `data/chroma/aggregates/manifests/athos_eval_bundle_20260306_local.json` exists
- confirm `.env` points at the repo-local path

2. Chroma collection failures
- confirm `workspace/chroma` exists
- confirm the workspace tarball unpacked correctly

3. CLI works but evals fail
- usually this is a path/config issue rather than a CBORG issue
