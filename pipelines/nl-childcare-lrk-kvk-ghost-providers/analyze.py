#!/usr/bin/env python3
"""
Identify potential ghost childcare providers by cross-referencing LRK with
KVK company data and BAG address registry.

Task: nl-childcare-lrk-kvk-ghost-providers
"""

import csv
import gzip
import hashlib
import io
import os
import re
import sys
import zipfile
from collections import Counter, defaultdict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LRK_FILE = os.path.join(BASE_DIR, "data", "nl-lrk-childcare", "export_opendata_lrk_2.csv.gz")
SBI_FILE = os.path.join(BASE_DIR, "data", "nl-kvk-basis",
                        "PRD_202509060433_VerwerkingSBI_EXT_V2.csv.gz")
BAG_ZIP = os.path.join(BASE_DIR, "data", "nl-bag-addresses", "lvbag-extract-nl.zip")
OUT_DIR = os.path.join(BASE_DIR, "pipelines", "nl-childcare-lrk-kvk-ghost-providers", "output")
os.makedirs(OUT_DIR, exist_ok=True)

INACTIVE_CSV = os.path.join(OUT_DIR, "lrk-inactive-kvk.csv")
INVALID_ADDR_CSV = os.path.join(OUT_DIR, "lrk-invalid-address.csv")
STACKING_CSV = os.path.join(OUT_DIR, "lrk-address-stacking.csv")
SUMMARY_MD = os.path.join(OUT_DIR, "ghost-provider-summary.md")

DISCLAIMER = (
    "This analysis identifies statistical anomalies and patterns that may warrant "
    "further review. Findings represent signals, not proven wrongdoing. No accusation "
    "of fraud, corruption, or illegality is made or implied."
)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def load_lrk():
    """Load LRK records."""
    print("Loading LRK data...")
    records = []
    with gzip.open(LRK_FILE, "rt", encoding="latin-1") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            records.append({
                "lrk_id": row["lrk_id"],
                "type_oko": row["type_oko"],
                "status": row["status"],
                "inschrijfdatum": row["inschrijfdatum"],
                "uitschrijfdatum": row.get("uitschrijfdatum", ""),
                "postcode": row["opvanglocatie_postcode"].strip(),
                "woonplaats": row["opvanglocatie_woonplaats"].strip(),
                "kvk_nummer": row["kvk_nummer_houder"].strip(),
                "vestigingsnummer": row.get("vestigingsnummer_houder", "").strip(),
                "rechtsvorm": row.get("rechtsvorm_houder", "").strip(),
                "aantal_kindplaatsen": row.get("aantal_kindplaatsen", ""),
            })
    print(f"  Loaded {len(records)} LRK records")
    return records


def load_kvk_numbers():
    """Load set of active KVK numbers from SBI dataset."""
    print("Loading active KVK numbers from SBI dataset...")
    kvk_set = set()
    with gzip.open(SBI_FILE, "rt", encoding="utf-8") as f:
        next(f)  # skip header
        for line in f:
            parts = line.strip().split("~")
            if parts:
                kvk_set.add(parts[0])
    print(f"  Loaded {len(kvk_set)} unique active KVK numbers")
    return kvk_set


def load_bag_postcodes():
    """Extract all valid postcodes from BAG nummeraanduiding data."""
    print("Extracting postcodes from BAG (this may take a while)...")
    postcodes = set()
    postcode_re = re.compile(rb"<Objecten:postcode>(\w+)</Objecten:postcode>")

    with zipfile.ZipFile(BAG_ZIP) as outer:
        with outer.open("9999NUM08012026.zip") as inner_f:
            inner_bytes = io.BytesIO(inner_f.read())
            with zipfile.ZipFile(inner_bytes) as inner:
                names = sorted(inner.namelist())
                for idx, name in enumerate(names):
                    if not name.endswith(".xml"):
                        continue
                    with inner.open(name) as xml_f:
                        content = xml_f.read()
                        found = postcode_re.findall(content)
                        for pc in found:
                            postcodes.add(pc.decode("utf-8"))
                    if (idx + 1) % 100 == 0:
                        print(f"    Processed {idx + 1}/{len(names)} files, "
                              f"{len(postcodes)} unique postcodes so far")

    print(f"  Extracted {len(postcodes)} unique postcodes from BAG")
    return postcodes


def find_inactive_kvk(lrk_records, active_kvk):
    """Find LRK providers whose KVK is not in the active KVK dataset."""
    print("Checking KVK status for LRK providers...")
    inactive = []
    checked = 0
    for rec in lrk_records:
        kvk = rec["kvk_nummer"]
        if not kvk:
            continue
        checked += 1
        if kvk not in active_kvk:
            inactive.append({
                "lrk_id": rec["lrk_id"],
                "type_oko": rec["type_oko"],
                "lrk_status": rec["status"],
                "inschrijfdatum": rec["inschrijfdatum"],
                "uitschrijfdatum": rec["uitschrijfdatum"],
                "kvk_nummer": kvk,
                "vestigingsnummer": rec["vestigingsnummer"],
                "rechtsvorm": rec["rechtsvorm"],
                "postcode": rec["postcode"],
                "woonplaats": rec["woonplaats"],
                "signal": "kvk_not_in_active_register",
            })
    print(f"  Checked {checked} LRK records with KVK numbers")
    print(f"  Found {len(inactive)} with KVK not in active register")

    # Highlight the especially concerning ones: LRK still active but KVK gone
    still_active = sum(1 for r in inactive if r["lrk_status"] == "Ingeschreven")
    print(f"  Of which {still_active} are still actively registered in LRK")
    return inactive


def find_invalid_addresses(lrk_records, bag_postcodes):
    """Find LRK providers whose postcode doesn't match any BAG entry."""
    print("Validating LRK postcodes against BAG...")
    invalid = []
    checked = 0
    for rec in lrk_records:
        pc = rec["postcode"]
        if not pc:
            continue
        # Normalize: remove spaces, uppercase
        pc_norm = pc.replace(" ", "").upper()
        checked += 1
        if pc_norm not in bag_postcodes:
            invalid.append({
                "lrk_id": rec["lrk_id"],
                "type_oko": rec["type_oko"],
                "lrk_status": rec["status"],
                "inschrijfdatum": rec["inschrijfdatum"],
                "postcode": pc,
                "postcode_normalized": pc_norm,
                "woonplaats": rec["woonplaats"],
                "kvk_nummer": rec["kvk_nummer"],
                "signal": "postcode_not_in_bag",
            })
    print(f"  Checked {checked} LRK records with postcodes")
    print(f"  Found {len(invalid)} with postcodes not in BAG")
    return invalid


def find_address_stacking(lrk_records):
    """Find postcodes with 3+ LRK-registered providers."""
    print("Detecting address stacking (3+ providers per postcode)...")
    # Only count currently active (Ingeschreven) providers
    active_by_postcode = defaultdict(list)
    for rec in lrk_records:
        if rec["status"] == "Ingeschreven" and rec["postcode"]:
            pc = rec["postcode"].replace(" ", "").upper()
            active_by_postcode[pc].append(rec)

    stacking = []
    for pc, providers in sorted(active_by_postcode.items(),
                                 key=lambda x: -len(x[1])):
        if len(providers) < 3:
            continue
        # Check if they have different KVK holders (same KVK = same org, less suspicious)
        kvk_numbers = set(p["kvk_nummer"] for p in providers if p["kvk_nummer"])
        for p in providers:
            stacking.append({
                "postcode": pc,
                "provider_count_at_postcode": len(providers),
                "unique_kvk_holders": len(kvk_numbers),
                "lrk_id": p["lrk_id"],
                "type_oko": p["type_oko"],
                "kvk_nummer": p["kvk_nummer"],
                "inschrijfdatum": p["inschrijfdatum"],
                "woonplaats": p["woonplaats"],
                "aantal_kindplaatsen": p["aantal_kindplaatsen"],
            })

    postcodes_flagged = len(set(r["postcode"] for r in stacking))
    print(f"  Found {postcodes_flagged} postcodes with 3+ active providers")
    print(f"  Total provider entries in stacking list: {len(stacking)}")
    return stacking


def write_csv(path, rows, fieldnames):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Wrote {len(rows)} rows to {os.path.basename(path)}")


def write_summary(lrk_total, lrk_active, inactive_kvk, invalid_addr, stacking_rows,
                  active_kvk_count, bag_postcode_count):
    inactive_still_active = sum(1 for r in inactive_kvk if r["lrk_status"] == "Ingeschreven")
    invalid_still_active = sum(1 for r in invalid_addr if r["lrk_status"] == "Ingeschreven")
    stacking_postcodes = len(set(r["postcode"] for r in stacking_rows))

    # Distribution of stacking counts
    pc_counts = Counter()
    for r in stacking_rows:
        pc_counts[r["postcode"]] = r["provider_count_at_postcode"]
    stacking_dist = Counter(pc_counts.values())

    # Type distribution in stacking
    type_dist = Counter(r["type_oko"] for r in stacking_rows)

    md = f"""# Ghost Provider Analysis: LRK × KVK × BAG Cross-Reference

> {DISCLAIMER}

## Objective

Identify potential ghost childcare providers in the Dutch Landelijk Register
Kinderopvang (LRK) by cross-referencing with KVK company data and BAG address
registry. Ghost registrations may signal potential abuse of the
kinderopvangtoeslag (childcare benefit) system.

## Data Sources

- **LRK** (Landelijk Register Kinderopvang): {lrk_total:,} records
  ({lrk_active:,} currently registered)
- **KVK SBI Dataset**: {active_kvk_count:,} unique active KVK numbers
- **BAG** (Basisregistratie Adressen en Gebouwen): {bag_postcode_count:,} unique
  postcodes extracted from nummeraanduiding records

## Methodology

### Signal 1: Inactive KVK Registration
- Matched LRK `kvk_nummer_houder` against the KVK open dataset (SBI file)
- KVK numbers absent from the current open dataset are flagged as potentially
  dissolved or inactive, since KVK removes dissolved entities from the open data
- This is a proxy — absence may also indicate data timing differences

### Signal 2: Invalid Address (Postcode Not in BAG)
- Extracted all valid postcodes from the BAG nummeraanduiding dataset
  (1,299 XML files from the national address registry)
- Compared LRK provider postcodes against this set
- Postcodes not found in BAG may indicate non-existent addresses

### Signal 3: Address Stacking (3+ Providers per Postcode)
- Grouped currently active (Ingeschreven) LRK providers by postcode
- Flagged postcodes with 3 or more active providers
- Threshold of 3 chosen because: while childcare centers in commercial
  buildings may share a postcode, 3+ distinct registrations at a single
  postcode warrants review, especially when held by different KVK entities
- Counted unique KVK holders to distinguish multi-branch operators from
  genuinely distinct entities sharing an address

## Findings

### Inactive KVK Registrations
- **{len(inactive_kvk):,}** LRK providers have KVK numbers not found in the
  active KVK register
- Of these, **{inactive_still_active:,}** are still actively registered in LRK
  (status: Ingeschreven) — these are the highest-priority signals

### Invalid Addresses
- **{len(invalid_addr):,}** LRK providers have postcodes not found in BAG
- Of these, **{invalid_still_active:,}** are still actively registered in LRK

### Address Stacking
- **{stacking_postcodes:,}** postcodes have 3+ active LRK providers

| Providers at postcode | Number of postcodes |
|-----------------------|---------------------|
"""
    for count in sorted(stacking_dist.keys()):
        md += f"| {count} | {stacking_dist[count]} |\n"

    md += f"""
**Provider type distribution in stacking signals:**

| Type | Count |
|------|-------|
"""
    for typ, cnt in type_dist.most_common():
        md += f"| {typ} | {cnt} |\n"

    md += f"""
## Limitations

1. **KVK status proxy**: The SBI open dataset may not include all active
   entities (e.g., sole proprietors without SBI codes). Absence from the
   dataset does not definitively prove dissolution.
2. **Postcode granularity**: BAG postcodes cover ~15-20 addresses each.
   A valid postcode does not confirm a specific address exists, and an
   invalid postcode may be due to new construction not yet in the BAG extract.
3. **Guest parent care (VGO)**: Many VGO (gastouderopvang) entries have no
   fixed address in LRK (listed as "Opvang bij de vraagouder"), which is
   normal for guest parent childcare and not inherently suspicious.
4. **Stacking threshold**: The threshold of 3 providers is heuristic.
   Commercial buildings, childcare campuses, and shared facilities may
   legitimately house multiple providers at one postcode.
5. **Temporal alignment**: The LRK, KVK, and BAG datasets may have different
   extraction dates, causing false positives from timing differences.

## Conclusion

This analysis surfaces three types of signals that may warrant further review
for potential ghost registrations in the childcare benefit system. The
combination of multiple signals for the same provider (e.g., inactive KVK AND
address stacking) would strengthen the case for follow-up investigation.
"""

    with open(SUMMARY_MD, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"  Wrote summary to {os.path.basename(SUMMARY_MD)}")


def main():
    print("=" * 60)
    print("Ghost Childcare Provider Detection")
    print("=" * 60)

    lrk = load_lrk()
    active_kvk = load_kvk_numbers()
    bag_postcodes = load_bag_postcodes()

    lrk_active = sum(1 for r in lrk if r["status"] == "Ingeschreven")

    # Signal 1: Inactive KVK
    inactive = find_inactive_kvk(lrk, active_kvk)
    write_csv(INACTIVE_CSV, inactive, [
        "lrk_id", "type_oko", "lrk_status", "inschrijfdatum", "uitschrijfdatum",
        "kvk_nummer", "vestigingsnummer", "rechtsvorm", "postcode", "woonplaats",
        "signal",
    ])

    # Signal 2: Invalid address
    invalid_addr = find_invalid_addresses(lrk, bag_postcodes)
    write_csv(INVALID_ADDR_CSV, invalid_addr, [
        "lrk_id", "type_oko", "lrk_status", "inschrijfdatum", "postcode",
        "postcode_normalized", "woonplaats", "kvk_nummer", "signal",
    ])

    # Signal 3: Address stacking
    stacking = find_address_stacking(lrk)
    write_csv(STACKING_CSV, stacking, [
        "postcode", "provider_count_at_postcode", "unique_kvk_holders",
        "lrk_id", "type_oko", "kvk_nummer", "inschrijfdatum", "woonplaats",
        "aantal_kindplaatsen",
    ])

    # Summary
    write_summary(len(lrk), lrk_active, inactive, invalid_addr, stacking,
                  len(active_kvk), len(bag_postcodes))

    # Output hashes
    print("\n── Output hashes ──")
    for path in [INACTIVE_CSV, INVALID_ADDR_CSV, STACKING_CSV, SUMMARY_MD]:
        h = sha256_file(path)
        sz = os.path.getsize(path)
        print(f"  {os.path.basename(path)}: sha256={h} size={sz}")


if __name__ == "__main__":
    main()
