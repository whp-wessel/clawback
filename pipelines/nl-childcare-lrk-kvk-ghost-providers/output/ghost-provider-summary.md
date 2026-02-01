# Ghost Provider Analysis: LRK × KVK × BAG Cross-Reference

> This analysis identifies statistical anomalies and patterns that may warrant further review. Findings represent signals, not proven wrongdoing. No accusation of fraud, corruption, or illegality is made or implied.

## Objective

Identify potential ghost childcare providers in the Dutch Landelijk Register
Kinderopvang (LRK) by cross-referencing with KVK company data and BAG address
registry. Ghost registrations may signal potential abuse of the
kinderopvangtoeslag (childcare benefit) system.

## Data Sources

- **LRK** (Landelijk Register Kinderopvang): 87,425 records
  (32,007 currently registered)
- **KVK SBI Dataset**: 3,641,139 unique active KVK numbers
- **BAG** (Basisregistratie Adressen en Gebouwen): 474,722 unique
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
- **1,722** LRK providers have KVK numbers not found in the
  active KVK register
- Of these, **41** are still actively registered in LRK
  (status: Ingeschreven) — these are the highest-priority signals

### Invalid Addresses
- **0** LRK providers have postcodes not found in BAG
- Of these, **0** are still actively registered in LRK

### Address Stacking
- **1,168** postcodes have 3+ active LRK providers

| Providers at postcode | Number of postcodes |
|-----------------------|---------------------|
| 3 | 811 |
| 4 | 265 |
| 5 | 64 |
| 6 | 24 |
| 7 | 2 |
| 8 | 1 |
| 9 | 1 |

**Provider type distribution in stacking signals:**

| Type | Count |
|------|-------|
| KDV | 1944 |
| BSO | 1821 |
| VGO | 191 |
| GOB | 32 |

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
