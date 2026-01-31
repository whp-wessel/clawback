# ClawBack — Agent Instructions

## Mission

**Audit all important public finances in the world for potential fraud, waste, and abuse.**

This is a crowdsourced research project. AI agents and humans collaborate through Git to analyze public-finance datasets — procurement, subsidies, healthcare spending, benefits programs — and surface statistical anomalies that warrant further review. We start with the Netherlands and expand jurisdiction by jurisdiction.

**Your findings are signals, not accusations.** Never state fraud as fact. Always hedge: "potential," "anomaly," "warrants further review."

---

## Quick start — three ways to contribute

### A) Pick an existing task
```
1. Read tasks/ai/ — find a YAML with status: open
2. Claim it: set claimed_by to your GitHub username
3. Load data from local_path (under data/)
4. Write analysis code in pipelines/{task-id}/
5. Produce the artifacts listed in the task spec
6. PR: task YAML + pipeline code + run receipt + artifact pointers
```

### B) Create your own task and do it
```
1. Explore the data in data/ — look at manifests, registries, schema
2. Identify something worth investigating
3. Create tasks/ai/{your-task-id}.yml with status: in-progress
4. Write the analysis in pipelines/{task-id}/
5. Produce artifacts, generate run receipt
6. PR: new task YAML + pipeline code + run receipt + artifact pointers
```

### C) Find and add missing data
```
1. Identify a jurisdiction or domain that lacks data
2. Research the internet — find open-data portals, government APIs, public registries
3. Download the dataset and add it with: bash tools/add-dataset.sh <id> <file> --jurisdiction <code>
4. If the data requires human action (FOIA, paywall, registration), create a task in tasks/human/
5. PR: new data files + manifest + registry entry (+ human task if needed)
```

All three flows are encouraged. Don't wait for someone to create a task — if you see a gap, fill it.

### Using the internet and external tools

You are encouraged to **research the internet** to find datasets, understand regulatory context, look up entity information, or verify findings. Use web search, fetch public APIs, and leverage any MCP tools available to you. If a dataset exists on a government open-data portal, download it and add it to the repo. If access requires human action (account creation, FOIA request, paywall), create a human task in `tasks/human/` describing exactly what's needed and what it unblocks.

### Scope rule

**One PR = one task.** Every PR must address exactly one task. Do not combine unrelated analyses, dataset additions, or fixes in a single PR. If you discover a new lead while working on a task, create a separate task spec and a separate PR for it. Small, focused PRs are easier to review, reproduce, and merge.

---

## Identity

**Your identity is your GitHub username.** Set `claimed_by` in task specs to your GitHub username. CI verifies that `claimed_by` matches the PR author — you can only submit work under your own name.

---

## Where things live

```
tasks/ai/              ← TASK QUEUE — open tasks, or create your own
tasks/human/           ← tasks only humans can do (FOIA, paywalls)
data/                  ← LOCAL DATASETS (Git LFS) — your input data
  nl-tenderned/        ← Dutch procurement (2023-2025)
  nl-kvk-basis/        ← KVK company register + SBI codes
  nl-kvk-jaarrekeningen/ ← KVK annual financial statements
  nl-insolvency/       ← Centraal Insolventieregister (5yr)
  nl-digimv-2023/      ← Healthcare governance data 2023
  nl-digimv-2024/      ← Healthcare governance data 2024
  nl-zorgaanbieders/   ← Healthcare provider registry
  nl-lrk-childcare/    ← National Childcare Register (LRK)
  nl-bag-addresses/    ← BAG address/building registry
  nl-cbs-childcare/    ← CBS childcare statistics
  nl-financiele-instrumenten/ ← Financial instruments 2017-2024
pipelines/             ← analysis code (one subdir per task)
schemas/               ← JSON Schema for validating YAML
policies/              ← rules you must follow (disclosure, licensing)
artifacts/             ← output pointers (no raw data)
runs/                  ← run receipts (reproducibility proof)
tools/                 ← validation and utility scripts
jurisdictions/         ← per-country context, dataset registries
```

Each `data/` subdirectory has a `manifest.yml` with SHA256 hashes and provenance. Full dataset metadata is in `jurisdictions/countries/nl/datasets/registry.yml`.

---

## Adding datasets

You can contribute new datasets. All data files live in `data/` tracked by Git LFS.

### Using the helper script
```bash
bash tools/add-dataset.sh <dataset-id> <file-or-directory> --jurisdiction nl
```
This creates `data/<dataset-id>/`, copies files, generates `manifest.yml` with SHA256 hashes, and prints a registry entry template.

### Manually
1. Create `data/{dataset-id}/`
2. Copy data files into it (Git LFS tracks `data/**/*.csv.gz`, `*.json.gz`, `*.jsonl`, `*.json`, `*.zip`, `*.csv`, `*.parquet`)
3. Create `data/{dataset-id}/manifest.yml` with:
   - `dataset_id`, `name`, `description`, `source_url`, `license`, `jurisdiction`, `access_date`
   - A `files:` list with `name`, `sha256`, `size_bytes` for every file
4. Add an entry to the jurisdiction registry (e.g., `jurisdictions/countries/nl/datasets/registry.yml`)

### Rules for datasets
- License must be on the allowed list (see `policies/licensing.yml`)
- Every file must have a SHA256 hash in the manifest
- `source_url` must point to where the data was originally obtained
- CI validates that every manifest has `dataset_id` and `license`

### What Git LFS tracks
See `.gitattributes`. Currently: `data/**/*.csv.gz`, `*.json.gz`, `*.jsonl`, `*.json`, `*.zip`, `*.csv`, `*.parquet`. To add a new format, run `git lfs track "data/**/*.{ext}"`.

---

## How to do a task (detailed)

### 1. Pick or create a task

**Picking an existing task:** Read YAMLs in `tasks/ai/` with `status: open`. Check that:
- You have the `capabilities` listed (etl, stats, nlp, viz, etc.)
- All `depends_on` tasks have `status: merged`
- The `datasets` have a `local_path` (data is available locally)

**Creating your own task:** Copy `tasks/_templates/ai-task.yml` to `tasks/ai/{task-id}.yml`. Fill in:
- `id` — lowercase, hyphens only (e.g., `nl-kvk-insolvency-cross-ref`)
- `objective` — what you're investigating (use signal language)
- `datasets` — which datasets, with `local_path` pointing to `data/` dirs
- `artifacts` — what outputs you'll produce
- `evaluation.criteria` — how to judge correctness
- `claimed_by` — your GitHub username
- `status` — set to `in-progress` (you're doing it yourself)

### 2. Understand the data

Read the `manifest.yml` in each `data/` subdirectory for file descriptions. Read the jurisdiction registry for broader context. Data files are typically gzipped — use `gzip`/`pandas`/etc.

### 3. Write your analysis

Create `pipelines/{task-id}/` with:
- Your analysis code (Python, R, SQL, whatever)
- A `requirements.txt` or equivalent dependency lock
- A `README.md` explaining how to run it

### 4. Produce artifacts

Generate the exact artifacts listed in the task spec. Compute SHA256 for every output.

Every markdown artifact must include this disclaimer (or equivalent):

> This analysis identifies statistical anomalies and patterns that may warrant further review. Findings represent signals, not proven wrongdoing. No accusation of fraud, corruption, or illegality is made or implied.

### 5. Submit your PR

Your PR must include:

**a) Task spec** in `tasks/ai/{task-id}.yml` — set `status: in-review`, `claimed_by: {your-github-username}`

**b) Pipeline code** in `pipelines/{task-id}/`

**c) Run receipt** in `runs/{task-id}_{timestamp}.yml`:
```yaml
task_id: nl-procurement-splits
timestamp: "2025-01-22T14:00:00Z"
commit_sha: "abc123..."                  # full 40-char SHA
environment:
  runtime: "python:3.12.1"
  dependencies_lock: "pipelines/nl-procurement-splits/requirements.txt"
inputs:
  - path: data/nl-tenderned/Dataset_Tenderned-2024-01-01-2024-12-31.json.gz
    sha256: "9da496e825725c9a346bd68f44dddcdd0a1bc16bd2a68d0c4341e84d3066efc1"
outputs:
  - artifact_id: split-signal-candidates
    sha256: "..."
```

**d) Artifact pointers** in `artifacts/{task-id}.yml` — one entry per output with SHA256, format, and storage location.

### Worked example

See these three files together for a complete finished task:
- `tasks/ai/example-completed-nl-childcare-duplicates.yml` — the task spec
- `runs/nl-childcare-duplicates_2025-01-22T1400Z.yml` — the run receipt
- `artifacts/nl-childcare-duplicates.yml` — the artifact pointers

### 6. CI validates your PR

Your PR is blocked until:
- All YAML passes `yamllint`
- Task spec passes `schemas/task-spec.schema.yml`
- Run receipt passes `schemas/run-receipt.schema.yml`
- `claimed_by` matches your GitHub username (PR author)
- Dataset manifests have `dataset_id` and `license`
- `tools/check-policies.sh` passes (disclosure language, licensing)
- No raw data files in `artifacts/` or `runs/`

---

## Rules

### Disclosure — "signals not accusations"
See `policies/disclosure.yml`. Never use these words without a hedge: fraud, corruption, embezzlement, money laundering, criminal, guilty, illegal. Hedges: potential, possible, anomaly, signal, red flag, warrants further review.

### Licensing
Input datasets must have approved licenses (see `policies/licensing.yml`). Your outputs are released CC-BY-4.0.

### Reproducibility
See `policies/reproducibility.yml`. Pin your runtime version. Lock dependencies. Hash everything. Another agent must be able to re-run your code and get identical output hashes.

---

## Human tasks

Some work requires humans (FOIA requests, paywall access, manual labeling). These are in `tasks/human/`. If your task has a `depends_on` pointing to a human task, wait until that task reaches `status: merged`.

---

## Validation commands

```bash
bash tools/validate-task.sh tasks/ai/{task}.yml
bash tools/validate-receipt.sh runs/{receipt}.yml
bash tools/check-policies.sh .
bash tools/add-dataset.sh <id> <file> --jurisdiction nl
```

Requires: `yq` (v4+), `python3` with `jsonschema`.
