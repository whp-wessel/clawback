#!/usr/bin/env python3
"""
DigiMV Healthcare Governance Anomaly Detection (2023 vs 2024)

Compares DigiMV governance questionnaire data between 2023 and 2024 to
identify institutions with significant year-over-year changes in governance
indicators: board turnover, missing financial disclosures, and revenue shifts.
Cross-references flagged institutions with the zorgaanbieders registry.

Output:
  - governance-change-flags.csv: flagged institutions with anomaly details
  - governance-analysis-summary.md: methodology, findings, limitations
"""

import gzip
import hashlib
import os
import sys
from io import StringIO
from pathlib import Path

import numpy as np
import pandas as pd

# ---------- configuration ----------

DATA_DIR = Path("data")
OUTPUT_DIR = Path("pipelines/nl-healthcare-digimv-governance-anomalies/output")

DIGIMV_2023_FILE = DATA_DIR / "nl-digimv-2023/DigiMV2023_MultipleTables_20241001_0927.csv.gz"
DIGIMV_2024_FILES = [
    DATA_DIR / "nl-digimv-2024/digimv2024-openbaar-20251022-1713-multipletables-part-1.csv.gz",
    DATA_DIR / "nl-digimv-2024/digimv2024-openbaar-20251022-1713-multipletables-part-2.csv.gz",
    DATA_DIR / "nl-digimv-2024/digimv2024-openbaar-20251022-1713-multipletables-part-3.csv.gz",
]
ZORGAANBIEDERS_FILE = DATA_DIR / "nl-zorgaanbieders/nl_zorgaanbieders_4digit_only.csv.gz"

# Thresholds for flagging anomalies
REVENUE_CHANGE_THRESHOLD = 0.30       # 30% YoY change in total revenue
EQUITY_CHANGE_THRESHOLD = 0.40        # 40% YoY change in equity
BOARD_TURNOVER_THRESHOLD = 0.50       # 50%+ board members changed
RESULT_SIGN_FLIP = True               # Flag if profit -> loss or vice versa
MIN_REVENUE_FOR_FINANCIAL_FLAG = 100_000  # Only flag revenue changes above this

# ---------- helpers ----------


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_multitable_csv(gz_path: str) -> dict[str, pd.DataFrame]:
    """Parse a DigiMV multi-table CSV where multiple tables are stacked
    vertically, each with its own header starting with 'Code,...'."""
    with gzip.open(gz_path, "rt", encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")
    tables = {}
    current_header_line = None
    current_start = None
    table_idx = 0

    for i, line in enumerate(lines):
        is_header = line.startswith("Code,")
        is_end = i == len(lines) - 1

        if is_header or is_end:
            if current_header_line is not None:
                end_line = i if is_header else i + 1
                chunk = "\n".join(lines[current_start:end_line]).strip()
                if chunk:
                    try:
                        df = pd.read_csv(
                            StringIO(chunk),
                            low_memory=False,
                            on_bad_lines="skip",
                        )
                        # Name based on first non-Code column
                        cols = [c for c in df.columns if c != "Code" and not c.startswith("Unnamed")]
                        table_name = cols[0] if cols else f"table_{table_idx}"
                        tables[table_name] = df
                    except Exception:
                        pass
                table_idx += 1

            if is_header:
                current_header_line = line
                current_start = i

    return tables


def extract_main_table(tables: dict, year: str) -> pd.DataFrame:
    """Extract the main institution table (contains Questionnaire column)."""
    for name, df in tables.items():
        if "Questionnaire" in df.columns:
            main = df[df["Questionnaire"] == f"DigiMV{year}"].copy()
            return main
    return pd.DataFrame()


def extract_board_data(tables: dict) -> pd.DataFrame:
    """Extract board/function tables and count members per institution."""
    func_tables = []
    for name, df in tables.items():
        if "Code" in df.columns:
            func_cols = [c for c in df.columns if c.startswith("qFuncNaam_")]
            if func_cols:
                func_tables.append(df[["Code"] + func_cols])

    if not func_tables:
        return pd.DataFrame(columns=["Code", "board_member_count", "board_member_names"])

    combined = func_tables[0]
    for ft in func_tables[1:]:
        combined = combined.merge(ft, on="Code", how="outer")

    # Count non-null function names per institution
    name_cols = [c for c in combined.columns if c.startswith("qFuncNaam_")]
    records = []
    for _, row in combined.iterrows():
        names = [str(row[c]).strip() for c in name_cols
                 if pd.notna(row[c]) and str(row[c]).strip()]
        records.append({
            "Code": row["Code"],
            "board_member_count": len(names),
            "board_member_names": "|".join(sorted(names)),
        })
    return pd.DataFrame(records)


def extract_financial_data(tables: dict) -> pd.DataFrame:
    """Extract consolidated financial data (revenue, result, equity)."""
    fin_df = None
    for name, df in tables.items():
        if "Code" in df.columns and "qTotaalBaten_0Cons" in df.columns:
            fin_df = df
            break

    if fin_df is None:
        # Try non-consolidated revenue columns
        for name, df in tables.items():
            if "Code" in df.columns:
                rev_cols = [c for c in df.columns if "qBaten" in c or "qTotaalBaten" in c or "Baten" in c]
                if rev_cols:
                    fin_df = df
                    break

    if fin_df is None:
        return pd.DataFrame(columns=["Code"])

    result = pd.DataFrame({"Code": fin_df["Code"]})

    # Map column names to meaningful fields
    col_map = {
        "qTotaalBaten_0Cons": "total_revenue_current",
        "qTotaalBaten_1Cons": "total_revenue_previous",
        "qBatenZorg_0Cons": "care_revenue_current",
        "qBatenZorg_1Cons": "care_revenue_previous",
    }

    for col, alias in col_map.items():
        if col in fin_df.columns:
            result[alias] = pd.to_numeric(fin_df[col], errors="coerce")

    # Try result/profit columns
    for name, df in tables.items():
        if "Code" not in df.columns:
            continue
        result_cols = {
            "qResultaatNaBelasting_0Cons": "net_result_current",
            "qResultaatNaBelasting_1Cons": "net_result_previous",
            "qResultaatVoorBelasting_0Cons": "result_before_tax_current",
            "qResultaatVoorBelasting_1Cons": "result_before_tax_previous",
        }
        found = {k: v for k, v in result_cols.items() if k in df.columns}
        if found:
            for col, alias in found.items():
                temp = df[["Code", col]].copy()
                temp[alias] = pd.to_numeric(temp[col], errors="coerce")
                result = result.merge(temp[["Code", alias]], on="Code", how="left")

    # Try equity columns from result-bestemming table
    for name, df in tables.items():
        if "Code" not in df.columns:
            continue
        equity_map = {
            "qResultaatbedrag_0": "result_amount_current",
            "qResultaatbedrag_1": "result_amount_previous",
        }
        found = {k: v for k, v in equity_map.items() if k in df.columns}
        if found:
            for col, alias in found.items():
                temp = df[["Code", col]].copy()
                temp[alias] = pd.to_numeric(temp[col], errors="coerce")
                result = result.merge(temp[["Code", alias]], on="Code", how="left")

    return result


def extract_equity_data(tables: dict) -> pd.DataFrame:
    """Extract equity data from balance sheet tables."""
    for name, df in tables.items():
        if "Code" not in df.columns:
            continue
        # Look for equity columns in the consolidated balance tables
        equity_cols = {}
        for c in df.columns:
            cl = c.lower()
            if "eigenvermogen" in cl.replace(" ", "") or "eigenVermogen" in c:
                equity_cols[c] = c
            elif c in ("qEigenVermogen_0Cons", "qEigenVermogen_1Cons",
                       "qEigenVermogenTotaal_0Cons", "qEigenVermogenTotaal_1Cons",
                       "qEVTotaal_0Cons", "qEVTotaal_1Cons",
                       "qEVTotaal_0", "qEVTotaal_1"):
                equity_cols[c] = c

        if equity_cols:
            result = pd.DataFrame({"Code": df["Code"]})
            for col in equity_cols:
                result[col] = pd.to_numeric(df[col], errors="coerce")
            return result

    return pd.DataFrame(columns=["Code"])


# ---------- main analysis ----------


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("DigiMV Governance Anomaly Detection: 2023 vs 2024")
    print("=" * 60)

    # --- Load 2023 ---
    print("\n[1/6] Parsing DigiMV 2023...")
    tables_2023 = parse_multitable_csv(str(DIGIMV_2023_FILE))
    print(f"  Found {len(tables_2023)} sub-tables in 2023 data")

    main_2023 = extract_main_table(tables_2023, "2023")
    print(f"  Main table: {len(main_2023)} institutions")

    board_2023 = extract_board_data(tables_2023)
    print(f"  Board data: {len(board_2023)} records")

    fin_2023 = extract_financial_data(tables_2023)
    print(f"  Financial data: {len(fin_2023)} records")

    # --- Load 2024 (3 parts) ---
    print("\n[2/6] Parsing DigiMV 2024 (3 parts)...")
    all_main_2024 = []
    all_board_2024 = []
    all_fin_2024 = []

    for i, fpath in enumerate(DIGIMV_2024_FILES):
        print(f"  Parsing part {i+1}...")
        tables_2024 = parse_multitable_csv(str(fpath))
        print(f"    Found {len(tables_2024)} sub-tables")

        m = extract_main_table(tables_2024, "2024")
        print(f"    Main table: {len(m)} institutions")
        all_main_2024.append(m)

        b = extract_board_data(tables_2024)
        all_board_2024.append(b)

        f = extract_financial_data(tables_2024)
        all_fin_2024.append(f)

    main_2024 = pd.concat(all_main_2024, ignore_index=True).drop_duplicates(subset=["Code"])
    board_2024 = pd.concat(all_board_2024, ignore_index=True).drop_duplicates(subset=["Code"])
    fin_2024 = pd.concat(all_fin_2024, ignore_index=True).drop_duplicates(subset=["Code"])

    print(f"\n  Combined 2024: {len(main_2024)} institutions, "
          f"{len(board_2024)} board records, {len(fin_2024)} financial records")

    # --- Load zorgaanbieders ---
    print("\n[3/6] Loading zorgaanbieders registry...")
    za = pd.read_csv(str(ZORGAANBIEDERS_FILE), compression="gzip", low_memory=False)
    za_kvk_set = set(za["KVK"].dropna().astype(str).str.strip())
    print(f"  {len(za_kvk_set)} unique registered KVK numbers")

    # --- Merge 2023 institution + board + financial ---
    print("\n[4/6] Merging institution data with board and financial tables...")

    inst_2023 = main_2023[["Code", "ExternalOrganizationId", "Name", "PostalCode", "Town"]].copy()
    inst_2023 = inst_2023.rename(columns={
        "ExternalOrganizationId": "kvk_number",
        "Name": "name",
        "PostalCode": "postal_code",
        "Town": "town",
    })
    inst_2023 = inst_2023.merge(board_2023, on="Code", how="left")
    inst_2023 = inst_2023.merge(fin_2023, on="Code", how="left")

    inst_2024 = main_2024[["Code", "ExternalOrganizationId", "Name", "PostalCode", "Town"]].copy()
    inst_2024 = inst_2024.rename(columns={
        "ExternalOrganizationId": "kvk_number",
        "Name": "name",
        "PostalCode": "postal_code",
        "Town": "town",
    })
    inst_2024 = inst_2024.merge(board_2024, on="Code", how="left")
    inst_2024 = inst_2024.merge(fin_2024, on="Code", how="left")

    # Ensure kvk_number is string
    inst_2023["kvk_number"] = inst_2023["kvk_number"].astype(str).str.strip()
    inst_2024["kvk_number"] = inst_2024["kvk_number"].astype(str).str.strip()

    # Match on Code (unique per institution across years) or kvk_number
    # The Code field is a UUID unique per submission, but kvk_number links across years
    merged = inst_2023.merge(
        inst_2024,
        on="kvk_number",
        how="inner",
        suffixes=("_2023", "_2024"),
    )
    print(f"  Matched {len(merged)} institutions across 2023-2024 by KVK number")

    # Also track institutions only in one year
    only_2023_kvk = set(inst_2023["kvk_number"]) - set(inst_2024["kvk_number"]) - {"nan", ""}
    only_2024_kvk = set(inst_2024["kvk_number"]) - set(inst_2023["kvk_number"]) - {"nan", ""}
    print(f"  Only in 2023: {len(only_2023_kvk)} institutions")
    print(f"  Only in 2024: {len(only_2024_kvk)} institutions")

    # --- Detect anomalies ---
    print("\n[5/6] Detecting governance anomalies...")
    flags = []

    for _, row in merged.iterrows():
        kvk = row["kvk_number"]
        name_2023 = row.get("name_2023", "")
        name_2024 = row.get("name_2024", "")
        institution_name = name_2024 if pd.notna(name_2024) else name_2023

        anomalies = []

        # --- Board turnover ---
        names_2023 = set(row.get("board_member_names_2023", "").split("|")) - {"", "nan"}
        names_2024 = set(row.get("board_member_names_2024", "").split("|")) - {"", "nan"}
        count_2023 = row.get("board_member_count_2023", 0)
        count_2024 = row.get("board_member_count_2024", 0)

        if isinstance(count_2023, float):
            count_2023 = int(count_2023) if pd.notna(count_2023) else 0
        if isinstance(count_2024, float):
            count_2024 = int(count_2024) if pd.notna(count_2024) else 0

        if names_2023 and names_2024:
            departed = names_2023 - names_2024
            new_members = names_2024 - names_2023
            total_unique = len(names_2023 | names_2024)
            turnover_rate = (len(departed) + len(new_members)) / (2 * total_unique) if total_unique > 0 else 0

            if turnover_rate >= BOARD_TURNOVER_THRESHOLD:
                anomalies.append({
                    "flag_type": "high_board_turnover",
                    "detail": (f"Board turnover rate: {turnover_rate:.0%}. "
                               f"{len(departed)} departed, {len(new_members)} new. "
                               f"2023: {count_2023} members, 2024: {count_2024} members."),
                    "severity": "high" if turnover_rate >= 0.75 else "medium",
                })
        elif count_2023 > 0 and count_2024 == 0:
            anomalies.append({
                "flag_type": "board_data_missing_2024",
                "detail": f"Had {count_2023} board members in 2023, none reported in 2024.",
                "severity": "medium",
            })
        elif count_2023 == 0 and count_2024 > 0:
            anomalies.append({
                "flag_type": "board_data_missing_2023",
                "detail": f"No board members in 2023, {count_2024} reported in 2024.",
                "severity": "low",
            })

        # --- Revenue change ---
        rev_2023 = row.get("total_revenue_current_2023")
        rev_2024 = row.get("total_revenue_current_2024")
        if pd.notna(rev_2023) and pd.notna(rev_2024) and rev_2023 != 0:
            rev_change = (rev_2024 - rev_2023) / abs(rev_2023)
            if abs(rev_change) >= REVENUE_CHANGE_THRESHOLD and abs(rev_2023) >= MIN_REVENUE_FOR_FINANCIAL_FLAG:
                direction = "increase" if rev_change > 0 else "decrease"
                anomalies.append({
                    "flag_type": f"large_revenue_{direction}",
                    "detail": (f"Revenue changed {rev_change:+.0%}: "
                               f"{rev_2023:,.0f} EUR (2023) -> {rev_2024:,.0f} EUR (2024)."),
                    "severity": "high" if abs(rev_change) >= 0.50 else "medium",
                })

        # --- Result sign flip ---
        res_col_current = None
        for col_prefix in ["net_result_current", "result_before_tax_current", "result_amount_current"]:
            c23 = f"{col_prefix}_2023"
            c24 = f"{col_prefix}_2024"
            if c23 in row.index and c24 in row.index:
                if pd.notna(row[c23]) and pd.notna(row[c24]):
                    res_col_current = (row[c23], row[c24], col_prefix)
                    break

        if res_col_current and RESULT_SIGN_FLIP:
            val_2023, val_2024, col_name = res_col_current
            if val_2023 > 0 and val_2024 < 0:
                anomalies.append({
                    "flag_type": "profit_to_loss",
                    "detail": (f"Went from profit ({val_2023:,.0f} EUR) "
                               f"to loss ({val_2024:,.0f} EUR)."),
                    "severity": "high",
                })
            elif val_2023 < 0 and val_2024 > 0:
                anomalies.append({
                    "flag_type": "loss_to_profit",
                    "detail": (f"Went from loss ({val_2023:,.0f} EUR) "
                               f"to profit ({val_2024:,.0f} EUR)."),
                    "severity": "low",
                })

        # --- Name change ---
        if (pd.notna(name_2023) and pd.notna(name_2024)
                and str(name_2023).strip().lower() != str(name_2024).strip().lower()):
            anomalies.append({
                "flag_type": "name_change",
                "detail": f'Name changed: "{name_2023}" -> "{name_2024}".',
                "severity": "low",
            })

        # --- Zorgaanbieders check ---
        in_registry = str(kvk).strip() in za_kvk_set
        if not in_registry and kvk not in ("nan", ""):
            anomalies.append({
                "flag_type": "not_in_zorgaanbieders",
                "detail": "KVK number not found in zorgaanbieders registry.",
                "severity": "medium",
            })

        # Record flags
        for anomaly in anomalies:
            flags.append({
                "kvk_number": kvk,
                "institution_name": institution_name,
                "postal_code_2024": row.get("postal_code_2024", ""),
                "town_2024": row.get("town_2024", ""),
                "flag_type": anomaly["flag_type"],
                "severity": anomaly["severity"],
                "detail": anomaly["detail"],
                "in_zorgaanbieders": in_registry,
                "board_count_2023": count_2023,
                "board_count_2024": count_2024,
                "revenue_2023": row.get("total_revenue_current_2023"),
                "revenue_2024": row.get("total_revenue_current_2024"),
            })

    # Also flag institutions that disappeared (in 2023 but not 2024)
    for kvk in list(only_2023_kvk)[:]:
        inst_row = inst_2023[inst_2023["kvk_number"] == kvk].iloc[0]
        in_registry = kvk in za_kvk_set
        flags.append({
            "kvk_number": kvk,
            "institution_name": inst_row.get("name", ""),
            "postal_code_2024": "",
            "town_2024": "",
            "flag_type": "disappeared_from_2024",
            "severity": "medium",
            "detail": "Institution present in 2023 DigiMV but absent from 2024 filing.",
            "in_zorgaanbieders": in_registry,
            "board_count_2023": inst_row.get("board_member_count", 0),
            "board_count_2024": 0,
            "revenue_2023": inst_row.get("total_revenue_current"),
            "revenue_2024": None,
        })

    flags_df = pd.DataFrame(flags)

    # Sort by severity then flag_type
    severity_order = {"high": 0, "medium": 1, "low": 2}
    flags_df["_sev_order"] = flags_df["severity"].map(severity_order)
    flags_df = flags_df.sort_values(["_sev_order", "flag_type", "kvk_number"])
    flags_df = flags_df.drop(columns=["_sev_order"])

    print(f"\n  Total flags: {len(flags_df)}")
    print(f"  Unique institutions flagged: {flags_df['kvk_number'].nunique()}")
    print(f"\n  Flags by type:")
    print(flags_df["flag_type"].value_counts().to_string())
    print(f"\n  Flags by severity:")
    print(flags_df["severity"].value_counts().to_string())

    # --- Write outputs ---
    print("\n[6/6] Writing outputs...")

    csv_path = OUTPUT_DIR / "governance-change-flags.csv"
    flags_df.to_csv(csv_path, index=False)
    csv_hash = sha256_file(str(csv_path))
    csv_size = os.path.getsize(csv_path)
    print(f"  {csv_path}: {csv_size:,} bytes, SHA256={csv_hash}")

    # --- Summary report ---
    n_high = len(flags_df[flags_df["severity"] == "high"])
    n_medium = len(flags_df[flags_df["severity"] == "medium"])
    n_low = len(flags_df[flags_df["severity"] == "low"])
    n_unique = flags_df["kvk_number"].nunique()
    n_not_in_za = len(flags_df[flags_df["flag_type"] == "not_in_zorgaanbieders"])
    n_disappeared = len(flags_df[flags_df["flag_type"] == "disappeared_from_2024"])
    n_board_turnover = len(flags_df[flags_df["flag_type"] == "high_board_turnover"])
    n_revenue_inc = len(flags_df[flags_df["flag_type"] == "large_revenue_increase"])
    n_revenue_dec = len(flags_df[flags_df["flag_type"] == "large_revenue_decrease"])
    n_profit_loss = len(flags_df[flags_df["flag_type"] == "profit_to_loss"])

    summary = f"""# DigiMV Healthcare Governance Anomaly Analysis: 2023 vs 2024

> **Disclaimer:** This analysis identifies statistical anomalies and patterns
> that may warrant further review. Findings represent signals, not proven
> wrongdoing. No accusation of fraud, corruption, or illegality is made or
> implied.

## Objective

Compare DigiMV healthcare governance questionnaire data between 2023 and 2024
to identify institutions with significant year-over-year changes in governance
indicators, including board composition turnover, missing financial disclosures,
and large unexplained revenue shifts.

## Data Sources

| Dataset | Records | Source |
|---------|---------|--------|
| DigiMV 2023 | {len(main_2023):,} institutions | jaarverantwoordingzorg.nl |
| DigiMV 2024 | {len(main_2024):,} institutions (3 parts) | jaarverantwoordingzorg.nl |
| Zorgaanbieders registry | {len(za_kvk_set):,} unique KVK numbers | zorgaanbiedersportaal.nl |

## Methodology

### Data Parsing

The DigiMV data is exported as "multiple tables" CSV files, where different
sections of the governance questionnaire (identification, board composition,
financial statements, personnel, etc.) are stacked vertically in a single file
with separate headers. The parser splits these into individual DataFrames per
sub-table.

### Matching

Institutions are matched across years using their KVK (Chamber of Commerce)
number (`ExternalOrganizationId`). Of {len(inst_2023):,} institutions in 2023
and {len(inst_2024):,} in 2024, **{len(merged):,}** were matched.

- {len(only_2023_kvk):,} institutions present only in 2023
- {len(only_2024_kvk):,} institutions present only in 2024

### Anomaly Detection

The following checks are applied:

| Check | Threshold | Rationale |
|-------|-----------|-----------|
| Board turnover | >= 50% members changed | Sudden leadership change may indicate governance instability |
| Revenue change | >= 30% YoY (min 100K EUR) | Large unexplained revenue shifts warrant review |
| Result sign flip | Profit to loss | Financial deterioration signal |
| Name change | Any change | May indicate restructuring or ownership change |
| Registry check | Not in zorgaanbieders | Unregistered provider is a potential red flag |
| Disappearance | In 2023 but not 2024 | Institution stopped filing |

## Findings

### Summary Statistics

| Metric | Count |
|--------|-------|
| Total flags raised | {len(flags_df):,} |
| Unique institutions flagged | {n_unique:,} |
| High severity | {n_high:,} |
| Medium severity | {n_medium:,} |
| Low severity | {n_low:,} |

### Flag Breakdown

| Flag Type | Count |
|-----------|-------|
| High board turnover | {n_board_turnover:,} |
| Large revenue increase | {n_revenue_inc:,} |
| Large revenue decrease | {n_revenue_dec:,} |
| Profit to loss | {n_profit_loss:,} |
| Not in zorgaanbieders registry | {n_not_in_za:,} |
| Disappeared from 2024 filing | {n_disappeared:,} |

### Key Observations

1. **Board turnover:** {n_board_turnover} institutions showed 50%+ board member
   turnover between 2023 and 2024. High board turnover can be a signal of
   potential governance instability, though it may also reflect normal succession
   planning.

2. **Revenue anomalies:** {n_revenue_inc + n_revenue_dec} institutions showed
   30%+ year-over-year revenue changes. Large shifts may indicate reporting
   errors, scope changes, or potential financial irregularities that warrant
   further review.

3. **Missing registrations:** {n_not_in_za} flagged institutions were not found
   in the zorgaanbieders registry. This may indicate deregistered providers
   still filing governance reports, or data matching issues.

4. **Disappeared institutions:** {n_disappeared} institutions filed in 2023 but
   were absent from 2024. This could be due to mergers, closures, or failure
   to file.

## Limitations

1. **Multi-table CSV parsing:** The DigiMV export format embeds multiple tables
   in a single CSV with shared column positions. Rows with quoted text
   containing commas (e.g., board member names with titles) can cause column
   misalignment. The parser uses pandas `on_bad_lines='skip'` which may drop
   some records.

2. **KVK matching:** Matching relies on `ExternalOrganizationId` which may not
   be consistently reported across years. Some institutions may use different
   KVK numbers for the same organization.

3. **Financial data coverage:** Not all institutions report financial data in
   the DigiMV questionnaire. Smaller providers may only fill in identification
   sections, leaving financial fields blank.

4. **Board data limitations:** The board member comparison relies on name
   matching. Name variations (spelling, prefixes, married names) may cause
   false board turnover signals.

5. **Zorgaanbieders registry coverage:** The registry was scraped by 4-digit
   postal code and may not be complete. Absence from the registry does not
   necessarily mean the provider is unregistered.

## Artifacts

- `governance-change-flags.csv`: All flagged institutions with anomaly type,
  severity, and details ({len(flags_df):,} rows)
- `governance-analysis-summary.md`: This document

## Reproducibility

- Runtime: Python 3.12+
- Dependencies: pandas, numpy (see requirements.txt)
- Input hashes documented in run receipt
"""

    md_path = OUTPUT_DIR / "governance-analysis-summary.md"
    md_path.write_text(summary, encoding="utf-8")
    md_hash = sha256_file(str(md_path))
    md_size = os.path.getsize(md_path)
    print(f"  {md_path}: {md_size:,} bytes, SHA256={md_hash}")

    print("\n" + "=" * 60)
    print("DONE. Output hashes:")
    print(f"  governance-change-flags.csv:     {csv_hash}")
    print(f"  governance-analysis-summary.md:  {md_hash}")
    print(f"  CSV size: {csv_size}")
    print(f"  MD size:  {md_size}")
    print("=" * 60)


if __name__ == "__main__":
    main()
