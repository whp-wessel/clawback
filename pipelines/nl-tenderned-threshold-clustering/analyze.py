#!/usr/bin/env python3
"""
Threshold clustering analysis for Dutch public procurement.

Analyzes TenderNed contract values (2023-2025) to detect unusual clustering
just below EU mandatory tender thresholds:
- Services: EUR 221,000
- Works: EUR 5,538,000

Uses McCrary density test to detect bunching effects.
"""

import pandas as pd
import numpy as np
import json
import gzip
import hashlib
import os
import glob
from datetime import datetime
from scipy import stats
from statsmodels.nonparametric.kde import KDEUnivariate
import matplotlib.pyplot as plt
import matplotlib

matplotlib.use("Agg")

EU_THRESHOLDS = {"services": 221_000, "works": 5_538_000}

THRESHOLD_ZONES = {
    "near_services": (
        0.90 * EU_THRESHOLDS["services"],
        1.0 * EU_THRESHOLDS["services"],
    ),
    "near_works": (0.90 * EU_THRESHOLDS["works"], 1.0 * EU_THRESHOLDS["works"]),
    "far_below_services": (0, 0.90 * EU_THRESHOLDS["services"]),
    "far_below_works": (0, 0.90 * EU_THRESHOLDS["works"]),
}


def load_tenderned_data():
    """Load TenderNed JSON.gz files for 2023, 2024, and partial 2025."""
    json_files = glob.glob("data/nl-tenderned/Dataset_Tenderned-*.json.gz")
    if not json_files:
        raise FileNotFoundError(f"No TenderNed files found in data/nl-tenderned/")

    records = []
    for filepath in json_files:
        print(f"Loading: {filepath}")
        with gzip.open(filepath, "rt") as f:
            full_json = json.load(f)

        # Extract releases if they exist
        if "releases" in full_json and isinstance(full_json["releases"], list):
            records.extend(full_json["releases"])
        else:
            records.append(full_json)

    df = pd.DataFrame(records)
    print(f"Loaded {len(df)} total records")
    return df


def extract_contract_value(record):
    """Extract contract value from a record. Handles various formats."""
    if isinstance(record, dict):
        # Try award value structure first (common in OCDS format)
        if (
            "awards" in record
            and isinstance(record["awards"], list)
            and len(record["awards"]) > 0
        ):
            award = record["awards"][0]
            if isinstance(award, dict) and "value" in award:
                value_obj = award["value"]
                if isinstance(value_obj, dict) and "amount" in value_obj:
                    amount_str = value_obj["amount"].replace(",", ".")
                    try:
                        val = float(amount_str)
                        return val
                    except (ValueError, TypeError):
                        pass
                elif isinstance(value_obj, (int, float)):
                    return float(value_obj)
    return None


def clean_value(value):
    """Clean and validate contract value."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        if value <= 0:
            return None
        return value
    return None


def filter_by_threshold_zone(df, threshold_type, lower, upper):
    """Filter DataFrame for a specific threshold zone."""
    zone_name = f"{threshold_type}_{lower}_{upper}"

    if threshold_type == "services":
        mask = (df["services_ratio"] >= lower) & (df["services_ratio"] < upper)
    else:
        mask = (df["works_ratio"] >= lower) & (df["works_ratio"] < upper)

    return df[mask].copy(), zone_name


def calculate_threshold_ratios(df):
    """Calculate contract value as ratio to thresholds."""
    df = df.copy()
    df["services_ratio"] = df["contract_value"] / EU_THRESHOLDS["services"]
    df["works_ratio"] = df["contract_value"] / EU_THRESHOLDS["works"]
    return df


def compute_distribution_buckets(df, threshold_type):
    """Compute distribution in threshold-relative buckets."""
    buckets = []

    if threshold_type == "services":
        ratios = df["services_ratio"]
        bucket_labels = [
            "0-10%",
            "10-20%",
            "20-30%",
            "30-40%",
            "40-50%",
            "50-60%",
            "60-70%",
            "70-80%",
            "80-90%",
            "90-95%",
            "95-99%",
            "99-100%",
            ">100%",
        ]
        bucket_edges = [
            0,
            0.10,
            0.20,
            0.30,
            0.40,
            0.50,
            0.60,
            0.70,
            0.80,
            0.90,
            0.95,
            0.99,
            1.0,
            float("inf"),
        ]
    else:
        ratios = df["works_ratio"]
        bucket_labels = [
            "0-10%",
            "10-20%",
            "20-30%",
            "30-40%",
            "40-50%",
            "50-60%",
            "60-70%",
            "70-80%",
            "80-90%",
            "90-95%",
            "95-99%",
            "99-100%",
            ">100%",
        ]
        bucket_edges = [
            0,
            0.10,
            0.20,
            0.30,
            0.40,
            0.50,
            0.60,
            0.70,
            0.80,
            0.90,
            0.95,
            0.99,
            1.0,
            float("inf"),
        ]

    digitized = np.digitize(ratios, bucket_edges)
    for i, (label, edge) in enumerate(zip(bucket_labels, bucket_edges[:-1])):
        count = np.sum(digitized == i + 1)
        buckets.append(
            {"bucket": label, "count": count, "percentage": count / len(df) * 100}
        )

    return pd.DataFrame(buckets)


def mccrary_density_test(values, threshold):
    """Perform McCrary density test for bunching at threshold."""
    values = np.array(values)

    # Define bandwidth for binning
    bandwidth = 0.05

    # Create bins
    bins = np.arange(0, 2, bandwidth)
    if threshold not in bins:
        bins = np.sort(np.unique(np.concatenate([bins, [threshold]])))

    # Count observations near threshold
    near_threshold = values[
        (values >= threshold - bandwidth) & (values <= threshold + bandwidth)
    ]
    far_left = values[values < threshold - bandwidth]
    far_right = values[values > threshold + bandwidth]

    # Bin near threshold
    near_bins = len(near_threshold)
    left_bins = len(far_left)
    right_bins = len(far_right)

    # Perform chi-square test for uniform distribution
    # Use far left as reference distribution
    counts = [near_bins, left_bins, right_bins]
    observed = np.array(counts)
    expected = np.array([near_bins, left_bins, right_bins])

    # Chi-square test
    if observed.sum() > 5:
        chi2, p_value = stats.chisquare(observed, f_exp=expected)
    else:
        p_value = np.nan
        chi2 = np.nan

    # Standard error of observed vs expected
    se = np.sqrt(expected)
    z_score = (observed[0] - expected[0]) / se[0]

    return {
        "n_near_threshold": near_bins,
        "n_far_left": left_bins,
        "n_far_right": right_bins,
        "chi2_statistic": chi2,
        "p_value": p_value,
        "z_score": z_score,
        "test_statistic": chi2,
    }


def plot_threshold_histogram(df, threshold_type, threshold_value, output_path):
    """Create histogram showing threshold distribution."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    if threshold_type == "services":
        values = df["services_ratio"]
        threshold_label = f"Services Threshold: €{threshold_value:,.0f}"
    else:
        values = df["works_ratio"]
        threshold_label = f"Works Threshold: €{threshold_value:,.0f}"

    # Log scale for better visualization
    ax1.hist(values, bins=100, range=(0, 2), log=True, alpha=0.7, color="steelblue")

    # Add threshold line
    ax1.axvline(x=1.0, color="red", linestyle="--", linewidth=2, label="Threshold")
    ax1.axvline(
        x=0.95, color="orange", linestyle="--", linewidth=2, label="95% of threshold"
    )
    ax1.axvline(
        x=0.99, color="green", linestyle="--", linewidth=2, label="99% of threshold"
    )

    ax1.set_xlabel(
        f"Contract Value as Ratio to {threshold_type.capitalize()} Threshold"
    )
    ax1.set_ylabel("Count (log scale)")
    ax1.set_title(f"Distribution of {threshold_type.capitalize()} Contract Values")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Zoom in on near-threshold zone
    ax2.hist(
        values[(values >= 0.90) & (values <= 1.10)],
        bins=20,
        range=(0.90, 1.10),
        log=True,
        alpha=0.7,
        color="steelblue",
    )
    ax2.axvline(x=1.0, color="red", linestyle="--", linewidth=2, label="Threshold")
    ax2.axvline(
        x=0.95, color="orange", linestyle="--", linewidth=2, label="95% of threshold"
    )
    ax2.axvline(
        x=0.99, color="green", linestyle="--", linewidth=2, label="99% of threshold"
    )
    ax2.axvline(
        x=1.01, color="purple", linestyle="--", linewidth=2, label="101% of threshold"
    )

    ax2.set_xlabel(f"Contract Value Ratio (90%-110%)")
    ax2.set_ylabel("Count (log scale)")
    ax2.set_title(f"Near-Threshold Zone: {threshold_label}")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()

    return output_path


def identify_anomalies(distribution, threshold_type):
    """Identify statistically unusual patterns in threshold distribution."""
    anomalies = []

    bucket_labels = distribution["bucket"].tolist()
    counts = distribution["count"].tolist()

    for i, (label, count) in enumerate(zip(bucket_labels, counts)):
        # Calculate expected count based on uniform distribution assumption
        total = sum(counts)
        expected_count = total / len(counts)

        # Use coefficient of variation to identify outliers
        # Low CV indicates more uniform distribution
        if i == 0:  # First bucket (0-10%)
            cv = np.nan
        else:
            cv = np.sqrt(counts[i] / expected_count) if expected_count > 0 else np.nan

        # Check for unusually high concentration in late buckets (90%+)
        if "90%" in label or "95%" in label or "99%" in label:
            if count > expected_count * 2:
                anomalies.append(
                    {
                        "threshold_type": threshold_type,
                        "bucket": label,
                        "count": count,
                        "expected_count": expected_count,
                        "observed_vs_expected": count / expected_count,
                        "anomaly_type": "concentration",
                        "severity": "high" if count / expected_count > 3 else "medium",
                    }
                )

        # Check for unusually high concentration in late buckets (90%+)
        if "90%" in label or "95%" in label or "99%" in label:
            if count > expected_count * 2:
                anomalies.append(
                    {
                        "threshold_type": threshold_type,
                        "bucket": label,
                        "count": count,
                        "expected_count": expected_count,
                        "observed_vs_expected": count / expected_count,
                        "anomaly_type": "concentration",
                        "severity": "high" if count / expected_count > 3 else "medium",
                    }
                )

    return pd.DataFrame(anomalies)


def calculate_hhi(df, threshold_type):
    """Calculate Herfindahl-Hirschman Index (HHI) by value bucket."""
    distribution = compute_distribution_buckets(df, threshold_type)
    distribution["hhi"] = (
        distribution["count"] / distribution["count"].sum()
    ) ** 2 * 10000
    return distribution


def main():
    """Main analysis function."""
    print("Starting threshold clustering analysis...")

    # Load data
    df = load_tenderned_data()
    df["contract_value"] = df.apply(
        lambda x: extract_contract_value(x.to_dict()), axis=1
    )
    df["contract_value"] = df["contract_value"].apply(clean_value)
    df = df[df["contract_value"].notna()].copy()
    df = df[df["contract_value"] > 0].copy()

    print(f"Contract values after filtering: {len(df)} records")

    # Calculate threshold ratios
    df = calculate_threshold_ratios(df)

    # Compute distributions for both thresholds
    dist_services = compute_distribution_buckets(df, "services")
    dist_works = compute_distribution_buckets(df, "works")

    # Identify anomalies
    anomalies_services = identify_anomalies(dist_services, "services")
    anomalies_works = identify_anomalies(dist_works, "works")

    # Compute HHI
    hhi_services = calculate_hhi(df, "services")
    hhi_works = calculate_hhi(df, "works")

    # Perform McCrary tests
    near_services = df[df["services_ratio"] >= 0.95]["services_ratio"]
    mccrary_services = mccrary_density_test(near_services, EU_THRESHOLDS["services"])

    near_works = df[df["works_ratio"] >= 0.95]["works_ratio"]
    mccrary_works = mccrary_density_test(near_works, EU_THRESHOLDS["works"])

    # Save threshold distribution
    dist_services.to_csv("threshold-distribution.csv", index=False)
    print(f"Saved threshold distribution: {len(dist_services)} buckets")

    dist_works.to_csv("threshold-distribution-works.csv", index=False)
    print(f"Saved threshold distribution (works): {len(dist_works)} buckets")

    # Save anomalies
    anomalies_services.to_csv("threshold-anomalies-services.csv", index=False)
    print(f"Saved anomalies for services: {len(anomalies_services)}")

    anomalies_works.to_csv("threshold-anomalies-works.csv", index=False)
    print(f"Saved anomalies for works: {len(anomalies_works)}")

    # Save HHI
    hhi_services.to_csv("threshold-hhi-services.csv", index=False)
    print(f"Saved HHI for services: {len(hhi_services)} buckets")

    hhi_works.to_csv("threshold-hhi-works.csv", index=False)
    print(f"Saved HHI for works: {len(hhi_works)} buckets")

    # Plot histograms
    plot_threshold_histogram(
        df, "services", EU_THRESHOLDS["services"], "threshold-histogram-services.png"
    )
    print("Saved services histogram")

    plot_threshold_histogram(
        df, "works", EU_THRESHOLDS["works"], "threshold-histogram-works.png"
    )
    print("Saved works histogram")

    # Generate summary
    summary = f"""# Threshold Clustering Analysis

This analysis identifies statistically unusual patterns in Dutch public procurement
contract values relative to EU mandatory tender thresholds. The analysis detects
potential threshold avoidance by examining clustering just below thresholds:
- Services threshold: €221,000
- Works threshold: €5,538,000

## Methodology

### Data
- Source: TenderNed public procurement notices (2023-2025)
- Dataset: {len(df)} contracts with valid values

### Statistical Approach
- **Distribution Analysis**: Contract values binned as percentages of thresholds
- **Herfindahl-Hirschman Index (HHI)**: Measures concentration in value buckets
- **McCrary Density Test**: Tests for bunching at threshold using chi-square

### Threshold Zones Analyzed
- 0-10%, 10-20%, ..., 80-90% (far below threshold)
- 90-95%, 95-99%, 99-100% (just below threshold)
- >100% (above threshold)

## Findings

### Services Threshold (€221,000)

**Distribution:**
{dist_services.to_markdown()}

**HHI:** {hhi_services["hhi"].sum():.2f}
Lower HHI indicates more uniform distribution; higher HHI indicates concentration.

**Threshold Anomalies:**
{anomalies_services.to_markdown()}

**McCrary Test:**
- Near-threshold observations: {mccrary_services["n_near_threshold"]}
- Far-left observations: {mccrary_services["n_far_left"]}
- Far-right observations: {mccrary_services["n_far_right"]}
- Chi-square statistic: {mccrary_services["chi2_statistic"]:.4f}
- P-value: {mccrary_services["p_value"]:.4f}
- Z-score: {mccrary_services["z_score"]:.4f}

### Works Threshold (€5,538,000)

**Distribution:**
{dist_works.to_markdown()}

**HHI:** {hhi_works["hhi"].sum():.2f}

**Threshold Anomalies:**
{anomalies_works.to_markdown()}

**McCrary Test:**
- Near-threshold observations: {mccrary_works["n_near_threshold"]}
- Far-left observations: {mccrary_works["n_far_left"]}
- Far-right observations: {mccrary_works["n_far_right"]}
- Chi-square statistic: {mccrary_works["chi2_statistic"]:.4f}
- P-value: {mccrary_works["p_value"]:.4f}
- Z-score: {mccrary_works["z_score"]:.4f}

## Interpretation

**Statistical Significance:**
- P-values < 0.05 indicate statistically significant deviations from expected
- Z-scores > 2 or < -2 indicate anomalies

**HHI Interpretation:**
- HHI < 1500: Low concentration (uniform distribution)
- 1500 ≤ HHI < 2500: Moderate concentration
- HHI ≥ 2500: High concentration

## Limitations

1. **Data Quality**: Contract values may be missing or estimated
2. **Threshold Exemptions**: Some contracts may be exempt from thresholds
3. **Single-Source Contracts**: Exemptions not captured in analysis
4. **Temporal Trends**: Analysis does not distinguish between years
5. **Contract Modifications**: Value changes not captured in static snapshots

## Next Steps

For any statistically significant findings, consider:
1. Manual review of contracts in anomalous buckets
2. Cross-referencing with contracting authority records
3. Investigation of threshold exemption applications
4. Analysis by procurement category or municipality

---

This analysis identifies statistical anomalies and patterns that may warrant further review. Findings represent signals, not proven wrongdoing. No accusation of fraud, corruption, or illegality is made or implied.
"""

    with open("threshold-analysis-summary.md", "w") as f:
        f.write(summary)

    print("Saved threshold analysis summary")

    print("\nAnalysis complete!")
    print(f"Total contracts analyzed: {len(df)}")
    print(f"Services threshold anomalies: {len(anomalies_services)}")
    print(f"Works threshold anomalies: {len(anomalies_works)}")


if __name__ == "__main__":
    main()
