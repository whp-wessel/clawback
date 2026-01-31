# Run Receipts

Each YAML file here records a single pipeline execution for reproducibility. Receipts must conform to `schemas/run-receipt.schema.yml`.

## Convention

- Filename: `{task_id}_{timestamp}.yml` (e.g., `nl-procurement-splits_2025-01-15T1200Z.yml`)
- Every PR that adds analysis results **must** include a run receipt.
- CI verifies that input/output hashes in receipts match referenced datasets and artifact pointers.
