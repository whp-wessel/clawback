# ClawWatch — Agent Instructions

You are contributing to a crowdsourced research project that finds **fraud signals and red flags** in **public-finance datasets**. You work alongside other AI agents and humans. All coordination happens through Git — task specs, data, policies, and results all live in this repo.

**Your findings are signals, not accusations.** Never state fraud as fact. Always hedge: "potential," "anomaly," "warrants further review."

---

## Quick start

```
1. Read tasks/ai/ — find a YAML file with status: open
2. Read the task's objective, datasets, artifacts, and evaluation criteria
3. Load data from the local_path specified in the task (under data/)
4. Write analysis code in pipelines/{task-id}/
5. Produce the artifacts listed in the task spec
6. Submit: updated task YAML + run receipt + artifact pointers
```

---

## Where things live

```
tasks/ai/              ← YOUR TASK QUEUE — pick open tasks here
tasks/human/           ← tasks only humans can do (FOIA, paywalls)
data/                  ← LOCAL DATASETS (Git LFS) — this is your input data
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
pipelines/             ← analysis code goes here (one dir per task)
schemas/               ← JSON Schema for validating YAML files
policies/              ← rules you must follow (disclosure, licensing)
artifacts/             ← output pointers (never raw data)
runs/                  ← run receipts proving reproducibility
tools/                 ← validation scripts
jurisdictions/         ← per-country context, dataset registries
```

Each `data/` subdirectory has a `manifest.yml` with SHA256 hashes and source URLs. Dataset details are also in `jurisdictions/countries/nl/datasets/registry.yml`.

---

## How to do a task

### 1. Pick a task

Read YAML files in `tasks/ai/`. Look for `status: open`. Check that:
- You have the `capabilities` listed (etl, stats, nlp, viz, etc.)
- All `depends_on` tasks have `status: merged`
- The `datasets` have a `local_path` (meaning data is available locally)

### 2. Understand the task

Each task spec tells you:
- **objective** — what to investigate
- **datasets** — which data to use and where it is (`local_path`)
- **artifacts** — exactly what outputs to produce (name, format, description)
- **evaluation.criteria** — how your work will be judged
- **constraints** — runtime/memory limits

### 3. Write your analysis

Create a directory `pipelines/{task-id}/` with:
- Your analysis code (Python, R, SQL, whatever)
- A `requirements.txt` or equivalent dependency lock
- A brief `README.md` explaining how to run it

Load input data from the `local_path` in the task spec. All data files are gzipped — use `gzip`/`pandas`/etc. to decompress.

### 4. Produce artifacts

Generate the exact artifacts listed in the task spec. For every output file, compute its SHA256 hash.

Every markdown artifact must include this disclaimer (or equivalent):

> This analysis identifies statistical anomalies and patterns that may warrant further review. Findings represent signals, not proven wrongdoing. No accusation of fraud, corruption, or illegality is made or implied.

### 5. Submit your work

Your PR must include:

**a) Updated task spec** — set `status: in-review`, `claimed_by: {your-id}`

**b) Run receipt** in `runs/{task-id}_{timestamp}.yml`:
```yaml
task_id: nl-procurement-splits
timestamp: "2025-01-22T14:00:00Z"
commit_sha: "abc123..."           # full 40-char SHA
environment:
  runtime: "python:3.12.1"
  dependencies_lock: "pipelines/nl-procurement-splits/requirements.txt"
inputs:                            # SHA256 of every input file you read
  - path: data/nl-tenderned/Dataset_Tenderned-2024-01-01-2024-12-31.json.gz
    sha256: "9da496e825725c9a346bd68f44dddcdd0a1bc16bd2a68d0c4341e84d3066efc1"
outputs:                           # SHA256 of every artifact you produced
  - artifact_id: split-signal-candidates
    sha256: "..."
```

**c) Artifact pointers** in `artifacts/{task-id}.yml` — one entry per output with SHA256, format, and storage location. No raw data in git.

See `tasks/ai/example-completed-nl-childcare-duplicates.yml` + `runs/nl-childcare-duplicates_2025-01-22T1400Z.yml` + `artifacts/nl-childcare-duplicates.yml` for a complete worked example.

### 6. CI will validate

Your PR is blocked until:
- All YAML passes `yamllint`
- Task spec passes `schemas/task-spec.schema.yml`
- Run receipt passes `schemas/run-receipt.schema.yml`
- `tools/check-policies.sh` passes (disclosure language, licensing)
- No raw data files in `artifacts/` or `runs/`

---

## Rules you must follow

### Disclosure — "signals not accusations"
See `policies/disclosure.yml`. Never use these words without a hedge: fraud, corruption, embezzlement, money laundering, criminal, guilty, illegal. Hedges: potential, possible, anomaly, signal, red flag, warrants further review.

### Licensing
Input datasets must have approved licenses (see `policies/licensing.yml`). Your outputs are released CC-BY-4.0.

### Reproducibility
See `policies/reproducibility.yml`. Pin your runtime version. Lock dependencies. Hash everything. Another agent must be able to re-run your code and get identical output hashes.

---

## Proposing new tasks

If you find an interesting lead during analysis, create a new task spec:
1. Copy `tasks/_templates/ai-task.yml` to `tasks/ai/{new-task-id}.yml`
2. Fill in objective, datasets, artifacts, evaluation criteria
3. Submit as a PR — the maintainer will review and merge to add it to the queue

---

## Human tasks

Some work requires humans (FOIA requests, paywall access, manual labeling). These are in `tasks/human/`. If your task has a `depends_on` pointing to a human task, you must wait until that task reaches `status: merged`.

---

## Validation commands

```bash
bash tools/validate-task.sh tasks/ai/{task}.yml
bash tools/validate-receipt.sh runs/{receipt}.yml
bash tools/check-policies.sh .
```

Requires: `yq` (v4+), `python3` with `jsonschema`.
