# Data

Local dataset storage tracked via Git LFS. Each subdirectory contains one logical dataset with a `manifest.yml` documenting provenance, license, and SHA256 hashes for every file.

## Rules

- All files are tracked by Git LFS (configured in `.gitattributes`).
- Every subdirectory **must** have a `manifest.yml`.
- Agents reference datasets via `local_path` in jurisdiction registry files.
- Source URLs in manifests enable independent re-download and hash verification.

## Datasets

| Directory | Description |
|---|---|
| `nl-tenderned/` | Dutch public procurement notices (2023-2025) |
| `nl-kvk-basis/` | KVK company register + SBI codes |
| `nl-kvk-jaarrekeningen/` | KVK annual financial statements |
| `nl-insolvency/` | Centraal Insolventieregister (5yr insolvencies) |
| `nl-digimv-2023/` | DigiMV healthcare governance data 2023 |
| `nl-digimv-2024/` | DigiMV healthcare governance data 2024 |
| `nl-zorgaanbieders/` | Healthcare provider registry |
| `nl-lrk-childcare/` | Landelijk Register Kinderopvang |
| `nl-bag-addresses/` | BAG national address registry extract |
| `nl-cbs-childcare/` | CBS formal childcare statistics |
| `nl-financiele-instrumenten/` | Financial instruments 2017-2024 |
