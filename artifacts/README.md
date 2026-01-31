# Artifacts

This directory contains **pointer manifests only** — no raw data files.

Each YAML file here is a content-addressed pointer to an artifact stored externally (S3, GCS, IPFS, etc.). Pointers must conform to `schemas/artifact-pointer.schema.yml`.

## Rules

- No binary files, CSVs, or data files in this directory.
- Every pointer must include a `sha256` hash for integrity verification.
- Artifacts are produced by pipeline runs and referenced from run receipts in `/runs/`.
