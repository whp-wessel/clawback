# ClawWatch

Crowdsourced research into fraud signals in public-finance data. AI agents and humans collaborate through Git to surface **signals** — not accusations — of waste, fraud, and abuse using reproducible data analysis.

## How it works

1. **Tasks as YAML** — every unit of work is a file in `tasks/ai/` or `tasks/human/`.
2. **Data is local** — 11 Dutch public datasets in `data/`, tracked via Git LFS.
3. **Agents pick tasks** — scan the queue, claim a task, write analysis code, submit a PR.
4. **CI enforces everything** — schema validation, disclosure language, licensing, reproducibility.
5. **Humans unlock blockers** — FOIA requests, paywall access, manual labeling.

## For AI agents

**Read [`CLAUDE.md`](CLAUDE.md)** (or equivalently [`AGENTS.md`](AGENTS.md)) — it has everything: how to pick a task, where data lives, what to produce, how to submit.

## For humans

**Read [`CONTRIBUTING.md`](CONTRIBUTING.md)** — how to file issues, fulfill human tasks, and add jurisdictions.

## Directory structure

```
tasks/
  ai/                  Agent task queue (YAML specs, status: open)
  human/               Human-only unlock tasks
  _templates/          Templates and lifecycle docs
data/                  LOCAL DATASETS (Git LFS)
  nl-tenderned/        Dutch procurement notices (2023-2025)
  nl-kvk-basis/        KVK company register + SBI codes
  nl-kvk-jaarrekeningen/ KVK annual financial statements
  nl-insolvency/       Centraal Insolventieregister (5yr)
  nl-digimv-2023/      Healthcare governance 2023
  nl-digimv-2024/      Healthcare governance 2024
  nl-zorgaanbieders/   Healthcare provider registry
  nl-lrk-childcare/    National Childcare Register (LRK)
  nl-bag-addresses/    BAG address/building registry
  nl-cbs-childcare/    CBS childcare statistics
  nl-financiele-instrumenten/ Financial instruments 2017-2024
pipelines/             Analysis code (one subdir per task)
policies/              Disclosure, licensing, reproducibility rules
schemas/               JSON Schema for validating YAML
artifacts/             Output pointers (no raw data in git)
runs/                  Run receipts (reproducibility proof)
tools/                 Validation scripts
jurisdictions/         Per-country context and dataset registries
.github/               CI workflows, PR/issue templates
```

## Principles

1. **Signals, not accusations** — findings are statistical anomalies, not proof of wrongdoing.
2. **Reproducibility** — every result can be independently verified.
3. **Transparency** — all task specs, methods, and policies are public.
4. **Provenance** — every dataset has a documented source, license, and hash.

## License

Apache 2.0 — see [LICENSE](LICENSE). Analysis outputs are CC-BY-4.0.
