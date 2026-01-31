# Tools

Validation and utility scripts used locally and in CI.

| Script | Purpose |
|---|---|
| `validate-task.sh` | Validate a task YAML against the task-spec schema |
| `validate-receipt.sh` | Validate a run receipt against the run-receipt schema |
| `check-policies.sh` | Check license compliance and disclosure language |

## Dependencies

- `yq` (v4+) — YAML processing
- `python3` with `jsonschema` — schema validation (or `ajv-cli` for Node)
- `grep` — pattern matching for policy checks
