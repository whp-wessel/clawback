# Policies

Machine-readable rules enforced by CI on every PR.

| Policy | File | What it governs |
|---|---|---|
| Licensing | `licensing.yml` | Allowed input dataset licenses; output license (CC-BY-4.0) |
| Disclosure | `disclosure.yml` | Language rules: "signals not accusations" framing |
| Reproducibility | `reproducibility.yml` | Run receipt requirements, hash formats, environment pinning |

## Enforcement

- `tools/check-policies.sh` runs these checks locally.
- `.github/workflows/validate-pr.yml` runs them in CI and blocks merge on failure.
- Jurisdiction-level overrides can be placed in `jurisdictions/<path>/policies/` and will be merged with global policies during validation.
