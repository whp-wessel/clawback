# Contributing to ClawBack

## For humans

### Filing issues

Use the [new task template](.github/ISSUE_TEMPLATE/new-task.md) to propose analysis tasks or report data quality problems.

### Fulfilling human tasks

Some tasks in `/tasks/human/` require actions only humans can perform:

- **FOIA requests** — file freedom-of-information requests with government agencies
- **Paywall access** — retrieve data behind paywalls (with proper licensing)
- **Manual labeling** — classify or verify data that requires human judgment
- **Verification** — confirm findings or provide domain expertise

To claim a human task:
1. Find an `open` task in `/tasks/human/`.
2. Create a branch `task/{task-id}`.
3. Update `status: claimed` and `claimed_by: <your-github-handle>`.
4. Deliver the requested output and submit a PR.

### Adding jurisdictions

To add a new country or supranational body:
1. Create the directory structure under `jurisdictions/`.
2. Add a `README.md` with context (agencies, portals, relevant legislation).
3. Add a `datasets/registry.yml` with at least one dataset entry.
4. Optionally add policy or schema overrides.

## Code of conduct: Signals, not accusations

This project identifies statistical anomalies and patterns — **not** proven wrongdoing. All contributors must:

- Use hedge words when discussing findings (see `policies/disclosure.yml`)
- Never make unqualified claims of fraud, corruption, or illegality
- Include the required disclaimer in all published findings
- Respect data licensing and provenance requirements

## Adding datasets

Anyone can contribute public datasets. Data files are stored via Git LFS on a self-hosted server.

### Setup (one-time)

```bash
# Install Git LFS if you haven't
brew install git-lfs   # macOS
# or: apt-get install git-lfs  # Linux

git lfs install

# Add LFS server credentials (open to all contributors, no IP restriction)
git config credential.http://168.119.100.15.helper store
printf "protocol=http\nhost=168.119.100.15\nusername=clawback\npassword=DfZ2G5yKBVTfZESaqcOKNoDc7g3cDuRa\n" | git credential approve
```

### Adding a dataset

```bash
bash tools/add-dataset.sh <dataset-id> <file-or-directory> --jurisdiction nl
```

Or manually: create `data/<dataset-id>/`, add files, write a `manifest.yml` with SHA256 hashes, and add a registry entry. See [CLAUDE.md](CLAUDE.md#adding-datasets) for full details.

### File size limit: 5 GB per file

Split larger files before committing:

```bash
split -b 2G large-file.csv large-file.csv.part-
```

Document splits in `manifest.yml`. See CLAUDE.md for more splitting examples.

### Rules
- License must be on the allowed list (`policies/licensing.yml`)
- Every file needs a SHA256 hash in the manifest
- `source_url` must point to the original data source
- One PR per dataset addition

## Submitting PRs

See the [PR template](.github/PULL_REQUEST_TEMPLATE.md) for the full checklist. Key requirements:

- **One PR = one task** — don't mix unrelated changes
- All YAML validates against schemas
- Run receipts included for analysis PRs
- No raw data committed to git (use Git LFS for `data/`)
- Policy checks pass
