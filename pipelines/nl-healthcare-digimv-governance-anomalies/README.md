# DigiMV Healthcare Governance Anomaly Detection

Compares DigiMV 2023 and 2024 healthcare governance questionnaire data to detect
year-over-year changes in board composition, financial indicators, and registry status.

## Usage

```bash
cd /path/to/clawback
pip install -r pipelines/nl-healthcare-digimv-governance-anomalies/requirements.txt
python pipelines/nl-healthcare-digimv-governance-anomalies/analyze.py
```

Output is written to `pipelines/nl-healthcare-digimv-governance-anomalies/output/`.

## Inputs

- `data/nl-digimv-2023/DigiMV2023_MultipleTables_20241001_0927.csv.gz`
- `data/nl-digimv-2024/digimv2024-openbaar-20251022-1713-multipletables-part-*.csv.gz`
- `data/nl-zorgaanbieders/nl_zorgaanbieders_4digit_only.csv.gz`

## Outputs

- `governance-change-flags.csv` — flagged institutions with anomaly details
- `governance-analysis-summary.md` — methodology, findings, and limitations
