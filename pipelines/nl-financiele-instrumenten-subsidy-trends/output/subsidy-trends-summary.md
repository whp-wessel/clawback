# Dutch Financial Instruments — Subsidy Trend Analysis (2017-2024)

> **Disclaimer:** This analysis identifies statistical anomalies and patterns that may warrant further review. Findings represent signals, not proven wrongdoing. No accusation of fraud, corruption, or illegality is made or implied.

## Overview

- **Dataset:** Financiele instrumenten 2017-2024 (rijksfinancien.nl)
- **Total rows:** 292,754
- **Years covered:** 2017-2024
- **Total unique series** (budget × regeling × instrument): 4,476
- **Series with ≥4 years of data** (analyzed): 395

### Aggregate spending by year

| Year | Total (EUR bn) | YoY Change |
|------|---------------|------------|
| 2017 | 129.1 | — |
| 2018 | 140.8 | +9.0% |
| 2019 | 148.3 | +5.3% |
| 2020 | 175.8 | +18.6% |
| 2021 | 175.8 | -0.0% |
| 2022 | 158.9 | -9.6% |
| 2023 | 407.1 | +156.2% |
| 2024 | 202.7 | -50.2% |


## Methodology

### Data preparation

The dataset has a structural break around 2020: years 2017-2019 contain ~1,000 rows each (highly aggregated), while 2020-2024 contain 30,000-80,000 rows (granular, per-recipient data). To ensure comparability across the full period, all amounts are aggregated to the **(budget_name, regeling, instrument, year)** level before analysis.

### Growth anomaly detection

For each series with ≥4 years of data:
1. Compute year-over-year percentage growth rates
2. Calculate the series-level mean and standard deviation of growth rates
3. Flag any year where the growth z-score exceeds ±2.0

This rolling baseline approach (as required by the task spec) means anomalies are relative to each series' own history, not a global benchmark.

### Budget-vs-actual baseline deviation

Since the dataset contains only actual disbursements (no separate budget figures), we approximate a budget baseline using a **3-year trailing rolling mean** of preceding actuals. We flag any year where the actual amount deviates more than **25%** from this baseline.

## Results

### Growth anomalies

**33 anomalous series-years detected** (z-score ≥ ±2.0).

Top signals by absolute z-score:

- **Dotatie/onttrekking Algemene Mediareserve** (Onderwijs, Cultuur en Wetenschap, Bekostiging): 2018 — 6388.3% YoY change (z=2.26, amount: EUR -30,041k)
- **Commissariaat voor de Media** (Onderwijs, Cultuur en Wetenschap, Bijdrage aan ZBOs en RWTs): 2023 — 166.7% YoY change (z=2.21, amount: EUR 14,218k)
- **Filmfonds van de omroep en Telefilm (COBO)** (Onderwijs, Cultuur en Wetenschap, Bekostiging): 2023 — 337.6% YoY change (z=2.21, amount: EUR 11,044k)
- **Nederlands-Vlaamse Accreditatieorganisatie (NVAO)** (Onderwijs, Cultuur en Wetenschap, Bijdrage aan ZBOs en RWTs): 2023 — 179.9% YoY change (z=2.16, amount: EUR 11,918k)
- **Educatie** (Onderwijs, Cultuur en Wetenschap, Bijdrage aan medeoverheden): 2023 — 142.0% YoY change (z=2.15, amount: EUR 170,894k)
- **Nederlands Instituut voor Beeld en Geluid (NIBG)** (Onderwijs, Cultuur en Wetenschap, Bekostiging): 2023 — 151.0% YoY change (z=2.15, amount: EUR 64,182k)
- **EMBL** (Onderwijs, Cultuur en Wetenschap, Bijdrage aan (inter-)nationale organisaties): 2023 — 131.3% YoY change (z=2.15, amount: EUR 13,076k)
- **Overige subsidies** (Onderwijs, Cultuur en Wetenschap, Subsidies (regelingen)): 2019 — 491.9% YoY change (z=2.15, amount: EUR 126,257k)
- **SBB** (Onderwijs, Cultuur en Wetenschap, Bijdrage aan ZBOs en RWTs): 2023 — 146.1% YoY change (z=2.14, amount: EUR 164,126k)
- **Stichting Omroep Muziek** (Onderwijs, Cultuur en Wetenschap, Bekostiging): 2023 — 121.8% YoY change (z=2.14, amount: EUR 39,954k)


### Budget-vs-actual baseline deviations

**799 outlier series-years detected** (>25% deviation from rolling baseline).

Top signals by absolute deviation:

- **Bekostiging voortgezet onderwijs lumpsum** (Onderwijs, Cultuur en Wetenschap, Bekostiging): 2021 — 25234.6% over baseline (actual: EUR 8,812,213k, baseline: EUR 34,783k)
- **Wet Personenvervoer 2000** (Infrastructuur en Waterstaat, Subsidies (regelingen)): 2023 — 21918.8% over baseline (actual: EUR 265,326k, baseline: EUR 1,205k)
- **Incidenteel** (Infrastructuur en Waterstaat, Subsidies (regelingen)): 2020 — 5155.3% over baseline (actual: EUR 631,824k, baseline: EUR 12,022k)
- **Basisbeurs prestatiebeurs (NR)** (Onderwijs, Cultuur en Wetenschap, Leningen): 2024 — -3518.0% under baseline (actual: EUR 1,209,060k, baseline: EUR -35,373k)
- **Loopbaanorientatie** (Onderwijs, Cultuur en Wetenschap, Subsidies (regelingen)): 2023 — 3054.7% over baseline (actual: EUR 69,192k, baseline: EUR 2,193k)
- **Gemeenten** (Binnenlandse Zaken en Koninkrijksrelaties, Bijdrage aan medeoverheden): 2023 — 2760.9% over baseline (actual: EUR 57,246k, baseline: EUR 2,001k)
- **Energiebesparing Koopsector** (Binnenlandse Zaken en Koninkrijksrelaties, Subsidies (regelingen)): 2021 — 2432.3% over baseline (actual: EUR 90,134k, baseline: EUR 3,559k)
- **Diverse subsidies** (Binnenlandse Zaken en Koninkrijksrelaties, Subsidies (regelingen)): 2020 — 2005.4% over baseline (actual: EUR 79,984k, baseline: EUR 3,799k)
- **Programmatische Samenwerkingsverbanden** (Economische Zaken en Klimaat, Subsidies (regelingen)): 2022 — 1822.7% over baseline (actual: EUR 108,491k, baseline: EUR 5,643k)
- **Programmatische Samenwerkingsverbanden** (Economische Zaken en Klimaat, Subsidies (regelingen)): 2023 — 1805.9% over baseline (actual: EUR 755,930k, baseline: EUR 39,662k)


## Limitations

1. **Structural break in granularity:** Pre-2020 data is far more aggregated than post-2020. This means some apparent "growth" in 2020 may reflect changes in reporting rather than actual spending increases. Series that only appear from 2020 onward are analyzed only across that shorter window.
2. **No budget data:** The dataset only contains actual disbursements. The baseline deviation analysis uses a rolling historical mean as a proxy, which does not capture planned budget allocations.
3. **Anonymized recipients:** Most recipients are anonymized ("Geanonimiseerde ontvanger(s)"), limiting entity-level investigation.
4. **Amounts in EUR thousands:** All amounts are in EUR × 1,000 as reported in the source data.
5. **Zero-base growth:** Series where the prior year amount was zero are excluded from percentage growth calculations to avoid division artifacts.

## Reproducibility

- **Runtime:** Python 3.12+
- **Dependencies:** See `requirements.txt`
- **Input file:** `data/nl-financiele-instrumenten/Financiele_instrumenten_2017-2024.csv.gz` (SHA256 in manifest)
- **Outputs:** `subsidy-growth-anomalies.csv`, `budget-vs-actual-outliers.csv`
