# Tools

Validation and utility scripts used locally and in CI.

| Script | Purpose |
|---|---|
| `validate-task.sh` | Validate a task YAML against the task-spec schema |
| `validate-receipt.sh` | Validate a run receipt against the run-receipt schema |
| `check-policies.sh` | Check license compliance and disclosure language |
| `add-dataset.sh` | Add a new dataset: copies files, generates manifest, prints registry template |

## Usage

```bash
# Validate a task
bash tools/validate-task.sh tasks/ai/my-task.yml

# Validate a run receipt
bash tools/validate-receipt.sh runs/my-receipt.yml

# Run all policy checks
bash tools/check-policies.sh .

# Add a new dataset
bash tools/add-dataset.sh nl-new-dataset /path/to/data.csv.gz --jurisdiction nl
```

## Dependencies

- `yq` (v4+) — YAML processing
- `python3` with `jsonschema` — schema validation
- `shasum` — SHA256 hashing (ships with macOS/Linux)
