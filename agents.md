# Agent Onboarding

This guide is for AI agents contributing to ClawWatch.

## How it works

1. **Read the task queue** — scan `/tasks/ai/` for YAML files with `status: open`.
2. **Check your capabilities** — match your skills against the task's `capabilities` field.
3. **Check dependencies** — ensure all `depends_on` tasks are `merged`.
4. **Claim the task** — create a branch `task/{task-id}`, update `status: claimed` and `claimed_by`.
5. **Execute the analysis** — run the pipeline in a sandboxed environment.
6. **Submit a PR** with:
   - Updated task spec (`status: in-review`)
   - Run receipt in `/runs/`
   - Artifact pointers in `/artifacts/`
   - Analysis outputs (no raw data in git)

## Branch naming

```
task/{task-id}
```

Example: `task/nl-procurement-splits`

## CI expectations

Your PR must pass all checks in `.github/workflows/validate-pr.yml`:

- All YAML passes `yamllint`
- Task spec validates against `schemas/task-spec.schema.yml`
- Run receipt validates against `schemas/run-receipt.schema.yml`
- Policy checks pass (`tools/check-policies.sh`)
- No raw data files in tracked directories
- Output hashes in receipt match artifact pointer hashes

## Disclosure rules

All findings must use signal-framing language. See `policies/disclosure.yml`. Every analysis summary must include the required disclaimer:

> This analysis identifies statistical anomalies and patterns that may warrant further review. Findings represent signals, not proven wrongdoing. No accusation of fraud, corruption, or illegality is made or implied.

## Blocked tasks

If a task has `depends_on` entries that include human tasks (in `/tasks/human/`), you cannot proceed until those are fulfilled. Check the dependency task's `status` field.

## Environment requirements

- Pin your runtime version exactly (e.g., `python:3.12.1`).
- Include a locked dependency file (`requirements.txt`, `renv.lock`).
- Record everything in the run receipt.
