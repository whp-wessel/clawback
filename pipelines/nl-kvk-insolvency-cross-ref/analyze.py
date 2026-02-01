#!/usr/bin/env python3
"""
Cross-reference KVK company register with Centraal Insolventieregister
to identify rapid-insolvency entities and potential phoenix company clusters.

Task: nl-kvk-insolvency-cross-ref
"""

import csv
import gzip
import hashlib
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from difflib import SequenceMatcher

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SBI_FILE = os.path.join(BASE_DIR, "data", "nl-kvk-basis",
                        "PRD_202509060433_VerwerkingSBI_EXT_V2.csv.gz")
INSOLVENCY_FILE = os.path.join(BASE_DIR, "data", "nl-insolvency",
                               "Centraal Insolventieregister_full_last_5_years_insolvencies.jsonl")
OUT_DIR = os.path.join(BASE_DIR, "pipelines", "nl-kvk-insolvency-cross-ref", "output")
os.makedirs(OUT_DIR, exist_ok=True)

RAPID_CSV = os.path.join(OUT_DIR, "rapid-insolvency-entities.csv")
PHOENIX_CSV = os.path.join(OUT_DIR, "phoenix-signal-clusters.csv")
SUMMARY_MD = os.path.join(OUT_DIR, "phoenix-analysis-summary.md")

DISCLAIMER = (
    "This analysis identifies statistical anomalies and patterns that may warrant "
    "further review. Findings represent signals, not proven wrongdoing. No accusation "
    "of fraud, corruption, or illegality is made or implied."
)

RAPID_THRESHOLD_DAYS = 3 * 365  # 3 years


# ── Step 1: Build KVK registration date + SBI lookup from SBI file ─────────
def load_kvk_registration_data():
    """Extract earliest registration date and SBI codes per KVK number."""
    print("Loading KVK SBI data...")
    kvk_data = {}  # kvk_number -> {earliest_date, sbi_codes}
    with gzip.open(SBI_FILE, "rt", encoding="utf-8") as f:
        header = next(f).strip()
        # KVKNUMMER~VESTIGINGNUMMER~ISHOOFDVESTIGING~SBICODE~SBIOMSCHRIJVING~REGISTRATIETIJDSTIP~DATUMAANVANG~ISHOOFDACTIVITEIT
        for line in f:
            parts = line.strip().split("~")
            if len(parts) < 8:
                continue
            kvk_nr = parts[0]
            sbi_code = parts[3]
            datum_aanvang = parts[6]  # YYYYMMDD format

            if kvk_nr not in kvk_data:
                kvk_data[kvk_nr] = {"earliest_date": datum_aanvang, "sbi_codes": set()}
            else:
                if datum_aanvang < kvk_data[kvk_nr]["earliest_date"]:
                    kvk_data[kvk_nr]["earliest_date"] = datum_aanvang
            kvk_data[kvk_nr]["sbi_codes"].add(sbi_code)

    print(f"  Loaded {len(kvk_data)} unique KVK numbers from SBI file")
    return kvk_data


# ── Step 2: Parse insolvency records ──────────────────────────────────────────
def load_insolvency_records():
    """Parse insolvency JSONL and extract KVK-linked records."""
    print("Loading insolvency records...")
    records = []
    with open(INSOLVENCY_FILE, "r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line)
            insolvente = data["getCaseResponse"]["getCaseResult"][
                "inspubWebserviceInsolvente"]["insolvente"]
            persoon = insolvente.get("persoon", {})
            kvk_nr = persoon.get("KvKNummer")
            if not kvk_nr:
                continue

            name = persoon.get("achternaam", "")
            insolventienummer = insolvente.get("insolventienummer", "")

            # Extract address
            adressen = insolvente.get("adressen", {})
            adres = adressen.get("adres", {})
            if isinstance(adres, list):
                adres = adres[0] if adres else {}
            postcode = adres.get("postcode", "")
            straat = adres.get("straat", "")
            plaats = adres.get("plaats", "")
            huisnummer = adres.get("huisnummer", "")

            # Find bankruptcy pronouncement date (publicatieSoortCode 1300)
            pubs = insolvente.get("publicatiegeschiedenis", {}).get("publicatie", [])
            if isinstance(pubs, dict):
                pubs = [pubs]
            bankruptcy_date = None
            for pub in pubs:
                if pub.get("publicatieSoortCode") == "1300":
                    try:
                        bankruptcy_date = pub.get("publicatieDatum", "")
                    except Exception:
                        pass
                    break

            if not bankruptcy_date:
                # Fall back to earliest publication date
                dates = [p.get("publicatieDatum", "") for p in pubs if p.get("publicatieDatum")]
                if dates:
                    bankruptcy_date = min(dates)

            records.append({
                "kvk_nr": kvk_nr,
                "name": name,
                "insolventienummer": insolventienummer,
                "bankruptcy_date": bankruptcy_date,
                "postcode": postcode,
                "straat": straat,
                "huisnummer": huisnummer,
                "plaats": plaats,
            })

    print(f"  Loaded {len(records)} insolvency records with KVK numbers")
    return records


# ── Step 3: Cross-reference for rapid insolvencies ───────────────────────────
def find_rapid_insolvencies(kvk_data, insolvency_records):
    """Find companies that went insolvent within 3 years of registration."""
    print("Cross-referencing for rapid insolvencies...")
    rapid = []
    matched = 0
    for rec in insolvency_records:
        kvk_nr = rec["kvk_nr"]
        if kvk_nr not in kvk_data:
            continue
        matched += 1
        reg_date_str = kvk_data[kvk_nr]["earliest_date"]
        bankr_date_str = rec["bankruptcy_date"]
        if not bankr_date_str or not reg_date_str:
            continue
        try:
            # Registration date is YYYYMMDD
            reg_date = datetime.strptime(reg_date_str[:8], "%Y%m%d")
            # Bankruptcy date is YYYY-MM-DD
            bankr_date = datetime.strptime(bankr_date_str[:10], "%Y-%m-%d")
        except ValueError:
            continue

        days_to_insolvency = (bankr_date - reg_date).days
        if 0 < days_to_insolvency <= RAPID_THRESHOLD_DAYS:
            sbi_codes = ",".join(sorted(kvk_data[kvk_nr]["sbi_codes"]))
            rapid.append({
                "kvk_number": kvk_nr,
                "company_name": rec["name"],
                "registration_date": reg_date.strftime("%Y-%m-%d"),
                "insolvency_date": bankr_date_str,
                "days_to_insolvency": days_to_insolvency,
                "sbi_codes": sbi_codes,
                "postcode": rec["postcode"],
                "address": f"{rec['straat']} {rec['huisnummer']}".strip(),
                "city": rec["plaats"],
                "insolventienummer": rec["insolventienummer"],
            })

    print(f"  Matched {matched} insolvency records to KVK data")
    print(f"  Found {len(rapid)} rapid-insolvency entities (within 3 years)")
    rapid.sort(key=lambda x: x["days_to_insolvency"])
    return rapid


# ── Step 4: Cluster for phoenix signals ──────────────────────────────────────
def name_similarity(a, b):
    """Compute name similarity (0-1) using SequenceMatcher."""
    a = a.lower().replace("b.v.", "").replace("bv", "").strip()
    b = b.lower().replace("b.v.", "").replace("bv", "").strip()
    return SequenceMatcher(None, a, b).ratio()


def find_phoenix_clusters(insolvency_records, kvk_data):
    """
    Cluster insolvency entities sharing >= 2 of:
    - Same postcode (address proxy)
    - Same SBI code (sector)
    - Similar name (>= 0.6 similarity)
    """
    print("Detecting potential phoenix clusters...")
    # Build lookup structures
    by_postcode = defaultdict(list)
    for rec in insolvency_records:
        if rec["postcode"]:
            by_postcode[rec["postcode"]].append(rec)

    clusters = []
    seen_pairs = set()

    for postcode, entities in by_postcode.items():
        if len(entities) < 2:
            continue
        for i in range(len(entities)):
            for j in range(i + 1, len(entities)):
                e1 = entities[i]
                e2 = entities[j]
                pair_key = tuple(sorted([e1["insolventienummer"], e2["insolventienummer"]]))
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)

                signals = []
                # Signal 1: Same postcode (already guaranteed)
                signals.append("same_postcode")

                # Signal 2: Same SBI code
                kvk1 = kvk_data.get(e1["kvk_nr"], {})
                kvk2 = kvk_data.get(e2["kvk_nr"], {})
                sbi1 = kvk1.get("sbi_codes", set())
                sbi2 = kvk2.get("sbi_codes", set())
                shared_sbi = sbi1 & sbi2
                if shared_sbi:
                    signals.append("shared_sbi")

                # Signal 3: Name similarity
                sim = name_similarity(e1["name"], e2["name"])
                if sim >= 0.6:
                    signals.append(f"name_sim_{sim:.2f}")

                if len(signals) >= 2:
                    clusters.append({
                        "cluster_postcode": postcode,
                        "entity_1_kvk": e1["kvk_nr"],
                        "entity_1_name": e1["name"],
                        "entity_1_insolvency": e1["insolventienummer"],
                        "entity_1_bankruptcy_date": e1["bankruptcy_date"],
                        "entity_2_kvk": e2["kvk_nr"],
                        "entity_2_name": e2["name"],
                        "entity_2_insolvency": e2["insolventienummer"],
                        "entity_2_bankruptcy_date": e2["bankruptcy_date"],
                        "shared_sbi_codes": ",".join(sorted(shared_sbi)) if shared_sbi else "",
                        "signals": ";".join(signals),
                        "name_similarity": f"{sim:.2f}",
                    })

    print(f"  Found {len(clusters)} potential phoenix signal pairs")
    clusters.sort(key=lambda x: float(x["name_similarity"]), reverse=True)
    return clusters


# ── Step 5: Write outputs ────────────────────────────────────────────────────
def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def write_csv(path, rows, fieldnames):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Wrote {len(rows)} rows to {os.path.basename(path)}")


def write_summary(rapid, clusters, total_insolvency, matched_kvk):
    """Write the markdown analysis summary."""
    rapid_by_year = defaultdict(int)
    for r in rapid:
        try:
            yr = r["insolvency_date"][:4]
            rapid_by_year[yr] += 1
        except Exception:
            pass

    top_sbi = defaultdict(int)
    for r in rapid:
        for code in r["sbi_codes"].split(","):
            if code:
                top_sbi[code] += 1
    top_sbi_sorted = sorted(top_sbi.items(), key=lambda x: -x[1])[:10]

    md = f"""# KVK–Insolvency Cross-Reference: Potential Phoenix Company Analysis

> {DISCLAIMER}

## Objective

Identify companies in the Dutch KVK register that went insolvent shortly after
incorporation, and detect clusters of related insolvent entities that may signal
potential phoenix company behavior — where entities are deliberately wound up to
shed debts and restarted under new registrations.

## Methodology

### Data Sources
- **KVK SBI Dataset**: ~5.6M SBI activity code records with KVK numbers and
  registration dates (used as proxy for company start date)
- **Centraal Insolventieregister**: {total_insolvency:,} insolvency records
  spanning the last 5 years

### Step 1: Rapid Insolvency Detection
- Matched insolvency records to KVK data via KVK number ({matched_kvk:,} matches)
- Computed time from earliest KVK registration date to bankruptcy pronouncement
- Flagged entities where insolvency occurred within **3 years** (1,095 days)
  of registration

### Step 2: Phoenix Cluster Detection
- Grouped insolvency records by postcode
- For each pair of insolvent entities sharing a postcode, checked for:
  1. **Shared SBI code** (same business sector)
  2. **Name similarity** (SequenceMatcher ratio ≥ 0.6)
- Pairs matching on **≥ 2 signals** (postcode + at least one other) flagged as
  potential phoenix clusters

## Findings

### Rapid Insolvencies
- **{len(rapid):,} entities** went insolvent within 3 years of KVK registration
- Breakdown by insolvency year:
"""
    for yr in sorted(rapid_by_year.keys()):
        md += f"  - {yr}: {rapid_by_year[yr]} entities\n"

    if rapid:
        days = [r["days_to_insolvency"] for r in rapid]
        avg_days = sum(days) / len(days)
        median_days = sorted(days)[len(days) // 2]
        md += f"\n- Average days to insolvency: **{avg_days:.0f}** (median: **{median_days}**)\n"
        md += f"- Fastest insolvency: **{min(days)} days** after registration\n"

    md += f"""
### Top SBI Codes Among Rapid-Insolvency Entities

| SBI Code | Count |
|----------|-------|
"""
    for code, count in top_sbi_sorted:
        md += f"| {code} | {count} |\n"

    md += f"""
### Phoenix Signal Clusters
- **{len(clusters):,} entity pairs** flagged as potential phoenix signals
- These pairs share the same postcode AND at least one additional signal
  (shared SBI code or name similarity ≥ 0.6)

## Limitations

1. **Registration date proxy**: The earliest `DATUMAANVANG` in the SBI dataset
   may not perfectly reflect the original incorporation date if SBI codes were
   updated later.
2. **Address matching**: Uses postcode only (not full street address), which may
   produce false positives in dense commercial areas.
3. **Name similarity**: String-based matching (SequenceMatcher) may miss entities
   that are related but use entirely different names.
4. **Temporal gaps**: The insolvency register covers ~5 years; KVK data reflects
   current registrations. Companies dissolved before the data snapshot may be
   missed.
5. **Not all insolvencies are suspicious**: Many rapid insolvencies result from
   legitimate business failures, particularly in high-risk sectors like
   construction and hospitality.

## Conclusion

This analysis surfaces statistical patterns that may warrant further
investigation. The rapid-insolvency list and phoenix cluster signals should be
treated as starting points for deeper review, not as evidence of wrongdoing.
"""

    with open(SUMMARY_MD, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"  Wrote summary to {os.path.basename(SUMMARY_MD)}")


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("KVK–Insolvency Cross-Reference Analysis")
    print("=" * 60)

    kvk_data = load_kvk_registration_data()
    insolvency_records = load_insolvency_records()

    # Rapid insolvencies
    rapid = find_rapid_insolvencies(kvk_data, insolvency_records)
    rapid_fields = [
        "kvk_number", "company_name", "registration_date", "insolvency_date",
        "days_to_insolvency", "sbi_codes", "postcode", "address", "city",
        "insolventienummer",
    ]
    write_csv(RAPID_CSV, rapid, rapid_fields)

    # Phoenix clusters
    matched_kvk = sum(1 for r in insolvency_records if r["kvk_nr"] in kvk_data)
    clusters = find_phoenix_clusters(insolvency_records, kvk_data)
    cluster_fields = [
        "cluster_postcode", "entity_1_kvk", "entity_1_name",
        "entity_1_insolvency", "entity_1_bankruptcy_date",
        "entity_2_kvk", "entity_2_name", "entity_2_insolvency",
        "entity_2_bankruptcy_date", "shared_sbi_codes", "signals",
        "name_similarity",
    ]
    write_csv(PHOENIX_CSV, clusters, cluster_fields)

    # Summary
    write_summary(rapid, clusters, len(insolvency_records), matched_kvk)

    # Print SHA256 hashes for run receipt
    print("\n── Output hashes ──")
    for path in [RAPID_CSV, PHOENIX_CSV, SUMMARY_MD]:
        h = sha256_file(path)
        sz = os.path.getsize(path)
        print(f"  {os.path.basename(path)}: sha256={h} size={sz}")


if __name__ == "__main__":
    main()
