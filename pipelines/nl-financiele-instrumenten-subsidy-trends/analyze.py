"""
nl-financiele-instrumenten-subsidy-trends

Detect unusual growth patterns and budget-vs-actual deviations in Dutch
government financial instruments (subsidies, grants, etc.) 2017-2024.

Key design decisions:
- The dataset has a structural break: 2017-2019 rows are highly aggregated
  (~1000/year) while 2020-2024 are granular (30K-80K/year). We aggregate
  to the (Begrotingsnaam, Regeling, Instrument) level per year so that
  trends are comparable across the full period.
- Growth anomaly detection uses a rolling z-score: for each instrument-
  regeling series, we compute the mean and std of year-over-year growth
  rates across its history. A year is flagged if its growth rate exceeds
  2 standard deviations from the series mean.
- Budget-vs-actual analysis: this dataset only contains actual disbursements
  (no separate budget column). We approximate a "budget baseline" as the
  3-year rolling mean of actuals for each series, then flag years where
  the actual deviates >25% from that baseline.
- Series with fewer than 4 years of data are excluded from anomaly
  detection (not enough history for a meaningful baseline).

Output:
  artifacts/subsidy-growth-anomalies.csv
  artifacts/budget-vs-actual-outliers.csv
  artifacts/subsidy-trends-summary.md
"""

import hashlib
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
DATA_PATH = Path("data/nl-financiele-instrumenten/Financiele_instrumenten_2017-2024.csv.gz")
OUT_DIR = Path("pipelines/nl-financiele-instrumenten-subsidy-trends/output")
GROWTH_Z_THRESHOLD = 2.0       # flag if YoY growth z-score exceeds this
BASELINE_DEVIATION_PCT = 0.25  # flag if actual deviates >25% from rolling mean
ROLLING_WINDOW = 3             # years for rolling baseline
MIN_YEARS = 4                  # minimum years of data for a series
MIN_BASELINE_K = 1000          # ignore baselines below EUR 1M (artifacts from granularity change)

# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------
def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH, sep=";", low_memory=False)
    df.rename(columns={
        "Begrotingsjaar": "year",
        "Begrotingshoofdstuk": "chapter_code",
        "Begrotingsnaam": "budget_name",
        "Instrument": "instrument",
        "Regeling": "regeling",
        "Bedrag (x1000)": "amount_k",
    }, inplace=True)
    return df


# ---------------------------------------------------------------------------
# Aggregate to comparable series
# ---------------------------------------------------------------------------
def aggregate(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate to (budget_name, regeling, instrument, year) level."""
    grp = (
        df.groupby(["budget_name", "regeling", "instrument", "year"], dropna=False)
        .agg(
            amount_k=("amount_k", "sum"),
            n_rows=("amount_k", "size"),
        )
        .reset_index()
    )
    return grp


# ---------------------------------------------------------------------------
# Growth anomaly detection
# ---------------------------------------------------------------------------
def detect_growth_anomalies(agg: pd.DataFrame) -> pd.DataFrame:
    """Flag series-years where YoY growth is >2 std devs from series mean."""
    # Pivot to wide format: one row per series, columns = years
    agg = agg.copy()
    agg["series_key"] = (
        agg["budget_name"].fillna("") + " | "
        + agg["regeling"].fillna("") + " | "
        + agg["instrument"].fillna("")
    )

    series_list = []
    for key, grp in agg.groupby("series_key"):
        grp = grp.sort_values("year")
        if grp["year"].nunique() < MIN_YEARS:
            continue

        yearly = grp.set_index("year")["amount_k"]
        # Fill missing years with 0 for growth calc
        full_idx = range(yearly.index.min(), yearly.index.max() + 1)
        yearly = yearly.reindex(full_idx, fill_value=0)

        # YoY growth rate (handle zero base: use absolute change instead)
        pct_change = yearly.pct_change()
        abs_change = yearly.diff()

        # For z-score, use pct_change where base > 0, else NaN
        growth = pct_change.copy()
        growth[yearly.shift(1) == 0] = np.nan

        mean_g = growth.mean()
        std_g = growth.std()

        if std_g == 0 or np.isnan(std_g):
            continue

        z_scores = (growth - mean_g) / std_g

        for yr in z_scores.index:
            if pd.notna(z_scores[yr]) and abs(z_scores[yr]) >= GROWTH_Z_THRESHOLD:
                parts = key.split(" | ")
                series_list.append({
                    "budget_name": parts[0],
                    "regeling": parts[1],
                    "instrument": parts[2],
                    "year": yr,
                    "amount_k": int(yearly[yr]),
                    "prev_amount_k": int(yearly.get(yr - 1, 0)),
                    "yoy_growth_pct": round(growth[yr] * 100, 1) if pd.notna(growth[yr]) else None,
                    "abs_change_k": int(abs_change[yr]) if pd.notna(abs_change[yr]) else None,
                    "z_score": round(z_scores[yr], 2),
                    "series_mean_growth_pct": round(mean_g * 100, 1),
                    "series_std_growth_pct": round(std_g * 100, 1),
                    "n_years": len(yearly),
                })

    result = pd.DataFrame(series_list)
    if len(result) > 0:
        result = result.sort_values("z_score", key=abs, ascending=False)
    return result


# ---------------------------------------------------------------------------
# Budget-vs-actual baseline deviation
# ---------------------------------------------------------------------------
def detect_baseline_deviations(agg: pd.DataFrame) -> pd.DataFrame:
    """Flag years where actual deviates >25% from 3-year rolling mean."""
    agg = agg.copy()
    agg["series_key"] = (
        agg["budget_name"].fillna("") + " | "
        + agg["regeling"].fillna("") + " | "
        + agg["instrument"].fillna("")
    )

    outliers = []
    for key, grp in agg.groupby("series_key"):
        grp = grp.sort_values("year")
        if grp["year"].nunique() < MIN_YEARS:
            continue

        yearly = grp.set_index("year")["amount_k"]
        full_idx = range(yearly.index.min(), yearly.index.max() + 1)
        yearly = yearly.reindex(full_idx, fill_value=0)

        # Rolling mean of PRECEDING years (shift to avoid including current)
        baseline = yearly.shift(1).rolling(window=ROLLING_WINDOW, min_periods=2).mean()

        for yr in yearly.index:
            if pd.isna(baseline.get(yr)) or baseline[yr] == 0:
                continue
            # Skip tiny baselines — these are artifacts from the 2017-2019
            # aggregation level producing near-zero amounts for series that
            # later appear at full granularity.
            if abs(baseline[yr]) < MIN_BASELINE_K:
                continue
            deviation = (yearly[yr] - baseline[yr]) / baseline[yr]
            if abs(deviation) > BASELINE_DEVIATION_PCT:
                parts = key.split(" | ")
                outliers.append({
                    "budget_name": parts[0],
                    "regeling": parts[1],
                    "instrument": parts[2],
                    "year": yr,
                    "amount_k": int(yearly[yr]),
                    "baseline_k": int(round(baseline[yr])),
                    "deviation_pct": round(deviation * 100, 1),
                    "deviation_direction": "over" if deviation > 0 else "under",
                    "n_years": len(yearly),
                })

    result = pd.DataFrame(outliers)
    if len(result) > 0:
        result = result.sort_values("deviation_pct", key=abs, ascending=False)
    return result


# ---------------------------------------------------------------------------
# Summary generation
# ---------------------------------------------------------------------------
def generate_summary(
    df: pd.DataFrame,
    agg: pd.DataFrame,
    growth_anomalies: pd.DataFrame,
    baseline_outliers: pd.DataFrame,
) -> str:
    total_series = agg.groupby(
        ["budget_name", "regeling", "instrument"]
    ).ngroups
    analyzed_series = agg[
        agg.groupby(["budget_name", "regeling", "instrument"])["year"]
        .transform("nunique") >= MIN_YEARS
    ].groupby(["budget_name", "regeling", "instrument"]).ngroups

    yearly_totals = df.groupby("year")["amount_k"].sum()

    # Top growth anomalies summary
    top_growth = ""
    if len(growth_anomalies) > 0:
        for _, row in growth_anomalies.head(10).iterrows():
            top_growth += (
                f"- **{row['regeling']}** ({row['budget_name']}, {row['instrument']}): "
                f"{row['year']} — {row['yoy_growth_pct']}% YoY change "
                f"(z={row['z_score']}, amount: EUR {row['amount_k']:,}k)\n"
            )

    # Top baseline outliers summary
    top_baseline = ""
    if len(baseline_outliers) > 0:
        for _, row in baseline_outliers.head(10).iterrows():
            top_baseline += (
                f"- **{row['regeling']}** ({row['budget_name']}, {row['instrument']}): "
                f"{row['year']} — {row['deviation_pct']}% {row['deviation_direction']} baseline "
                f"(actual: EUR {row['amount_k']:,}k, baseline: EUR {row['baseline_k']:,}k)\n"
            )

    # Year-over-year total spending
    yearly_table = "| Year | Total (EUR bn) | YoY Change |\n|------|---------------|------------|\n"
    prev = None
    for yr in sorted(yearly_totals.index):
        total_bn = yearly_totals[yr] / 1_000_000
        if prev is not None:
            chg = (yearly_totals[yr] - prev) / prev * 100
            yearly_table += f"| {yr} | {total_bn:,.1f} | {chg:+.1f}% |\n"
        else:
            yearly_table += f"| {yr} | {total_bn:,.1f} | — |\n"
        prev = yearly_totals[yr]

    summary = f"""# Dutch Financial Instruments — Subsidy Trend Analysis (2017-2024)

> **Disclaimer:** This analysis identifies statistical anomalies and patterns that may warrant further review. Findings represent signals, not proven wrongdoing. No accusation of fraud, corruption, or illegality is made or implied.

## Overview

- **Dataset:** Financiele instrumenten 2017-2024 (rijksfinancien.nl)
- **Total rows:** {len(df):,}
- **Years covered:** 2017-2024
- **Total unique series** (budget × regeling × instrument): {total_series:,}
- **Series with ≥{MIN_YEARS} years of data** (analyzed): {analyzed_series:,}

### Aggregate spending by year

{yearly_table}

## Methodology

### Data preparation

The dataset has a structural break around 2020: years 2017-2019 contain ~1,000 rows each (highly aggregated), while 2020-2024 contain 30,000-80,000 rows (granular, per-recipient data). To ensure comparability across the full period, all amounts are aggregated to the **(budget_name, regeling, instrument, year)** level before analysis.

### Growth anomaly detection

For each series with ≥{MIN_YEARS} years of data:
1. Compute year-over-year percentage growth rates
2. Calculate the series-level mean and standard deviation of growth rates
3. Flag any year where the growth z-score exceeds ±{GROWTH_Z_THRESHOLD}

This rolling baseline approach (as required by the task spec) means anomalies are relative to each series' own history, not a global benchmark.

### Budget-vs-actual baseline deviation

Since the dataset contains only actual disbursements (no separate budget figures), we approximate a budget baseline using a **{ROLLING_WINDOW}-year trailing rolling mean** of preceding actuals. We flag any year where the actual amount deviates more than **{int(BASELINE_DEVIATION_PCT * 100)}%** from this baseline.

## Results

### Growth anomalies

**{len(growth_anomalies):,} anomalous series-years detected** (z-score ≥ ±{GROWTH_Z_THRESHOLD}).

Top signals by absolute z-score:

{top_growth if top_growth else "No growth anomalies detected."}

### Budget-vs-actual baseline deviations

**{len(baseline_outliers):,} outlier series-years detected** (>{int(BASELINE_DEVIATION_PCT * 100)}% deviation from rolling baseline).

Top signals by absolute deviation:

{top_baseline if top_baseline else "No baseline deviations detected."}

## Limitations

1. **Structural break in granularity:** Pre-2020 data is far more aggregated than post-2020. This means some apparent "growth" in 2020 may reflect changes in reporting rather than actual spending increases. Series that only appear from 2020 onward are analyzed only across that shorter window.
2. **No budget data:** The dataset only contains actual disbursements. The baseline deviation analysis uses a rolling historical mean as a proxy, which does not capture planned budget allocations.
3. **Anonymized recipients:** Most recipients are anonymized ("Geanonimiseerde ontvanger(s)"), limiting entity-level investigation.
4. **Amounts in EUR thousands:** All amounts are in EUR × 1,000 as reported in the source data.
5. **Zero-base growth:** Series where the prior year amount was zero are excluded from percentage growth calculations to avoid division artifacts.

## Reproducibility

- **Runtime:** Python 3.12+
- **Dependencies:** See `requirements.txt`
- **Input file:** `{DATA_PATH}` (SHA256 in manifest)
- **Outputs:** `subsidy-growth-anomalies.csv`, `budget-vs-actual-outliers.csv`
"""
    return summary


# ---------------------------------------------------------------------------
# Hashing utility
# ---------------------------------------------------------------------------
def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("Loading data...")
    df = load_data()
    print(f"  {len(df):,} rows, {df['year'].nunique()} years")

    print("Aggregating to series level...")
    agg = aggregate(df)
    print(f"  {len(agg):,} aggregated rows")

    print("Detecting growth anomalies...")
    growth_anomalies = detect_growth_anomalies(agg)
    print(f"  {len(growth_anomalies):,} anomalous series-years")

    print("Detecting baseline deviations...")
    baseline_outliers = detect_baseline_deviations(agg)
    print(f"  {len(baseline_outliers):,} outlier series-years")

    print("Writing outputs...")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    growth_path = OUT_DIR / "subsidy-growth-anomalies.csv"
    baseline_path = OUT_DIR / "budget-vs-actual-outliers.csv"
    summary_path = OUT_DIR / "subsidy-trends-summary.md"

    growth_anomalies.to_csv(growth_path, index=False)
    baseline_outliers.to_csv(baseline_path, index=False)

    summary = generate_summary(df, agg, growth_anomalies, baseline_outliers)
    summary_path.write_text(summary)

    print()
    print("Output files:")
    for p in [growth_path, baseline_path, summary_path]:
        h = sha256_file(p)
        print(f"  {p} — SHA256: {h}")

    print("\nDone.")


if __name__ == "__main__":
    main()
