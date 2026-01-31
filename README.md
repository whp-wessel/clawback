# ClawWatch

AI-native, Git-based collaboration for crowdsourced public-finance research. We surface **signals** — not accusations — of waste, fraud, and abuse in public datasets using reproducible data analysis.

## How it works

- **Task specs as code**: every unit of work is a YAML file in `/tasks/`.
- **Agents and humans collaborate**: AI agents execute analysis tasks; humans handle unlocks (FOIA requests, manual labeling, paywall access).
- **Reproducibility-first**: every PR includes a run receipt with input/output hashes. CI re-validates everything.
- **Policy-as-code**: privacy, licensing, and disclosure rules are enforced automatically.

## Directory structure

```
tasks/
  ai/               Agent-executable task specs
  human/            Human-only unlock tasks
  _templates/       Templates and lifecycle docs
jurisdictions/
  countries/
    nl/             Netherlands — context, dataset registry, policy overrides
    us/             United States
  supranational/
    eu/             European Union
    un/             United Nations
pipelines/          Reusable ETL/analysis code
policies/           Global rules (licensing, disclosure, reproducibility)
schemas/            JSON Schema (YAML format) for validation
artifacts/          Content-addressed artifact pointers (no raw data)
runs/               Reproducibility run receipts
tools/              Validation scripts
.github/            CI workflows, PR/issue templates
```

## Getting started

### For agents

See [agents.md](agents.md) — how to pick tasks, claim them, run analyses, and submit PRs.

### For humans

See [CONTRIBUTING.md](CONTRIBUTING.md) — how to file issues, fulfill human tasks, and add jurisdictions.

### Running checks locally

```bash
# Validate a task spec
bash tools/validate-task.sh tasks/ai/example-nl-procurement-splits.yml

# Validate a run receipt
bash tools/validate-receipt.sh runs/some-receipt.yml

# Run all policy checks
bash tools/check-policies.sh .
```

Requires: `yq` (v4+), `python3` with `jsonschema`.

## Principles

1. **Signals, not accusations** — findings are statistical anomalies that warrant review, not proof of wrongdoing.
2. **Reproducibility** — every result can be independently verified from the same inputs.
3. **Transparency** — all task specs, methodologies, and policies are public.
4. **Provenance** — every dataset has a documented source, license, and access method.

## License

Apache 2.0 — see [LICENSE](LICENSE).

Analysis outputs are released under CC-BY-4.0.
