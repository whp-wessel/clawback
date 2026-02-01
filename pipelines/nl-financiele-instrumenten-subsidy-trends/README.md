# nl-financiele-instrumenten-subsidy-trends

Detect unusual growth patterns and budget-vs-actual deviations in Dutch government financial instruments (2017-2024).

## Run

```bash
pip install -r requirements.txt
python analyze.py
```

Output is written to `output/`.

## Inputs

- `data/nl-financiele-instrumenten/Financiele_instrumenten_2017-2024.csv.gz`

## Outputs

- `output/subsidy-growth-anomalies.csv` — series-years with YoY growth z-score ≥ ±2.0
- `output/budget-vs-actual-outliers.csv` — series-years deviating >25% from 3-year rolling baseline
- `output/subsidy-trends-summary.md` — methodology, findings, limitations
