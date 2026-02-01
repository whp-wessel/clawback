# KVK–Insolvency Cross-Reference: Potential Phoenix Company Analysis

> This analysis identifies statistical anomalies and patterns that may warrant further review. Findings represent signals, not proven wrongdoing. No accusation of fraud, corruption, or illegality is made or implied.

## Objective

Identify companies in the Dutch KVK register that went insolvent shortly after
incorporation, and detect clusters of related insolvent entities that may signal
potential phoenix company behavior — where entities are deliberately wound up to
shed debts and restarted under new registrations.

## Methodology

### Data Sources
- **KVK SBI Dataset**: ~5.6M SBI activity code records with KVK numbers and
  registration dates (used as proxy for company start date)
- **Centraal Insolventieregister**: 10,181 insolvency records
  spanning the last 5 years

### Step 1: Rapid Insolvency Detection
- Matched insolvency records to KVK data via KVK number (3,182 matches)
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
- **1,386 entities** went insolvent within 3 years of KVK registration
- Breakdown by insolvency year:
  - 2025: 1136 entities
  - 2026: 250 entities

- Average days to insolvency: **71** (median: **74**)
- Fastest insolvency: **3 days** after registration

### Top SBI Codes Among Rapid-Insolvency Entities

| SBI Code | Count |
|----------|-------|
| 64210 | 151 |
| 56111 | 84 |
| 78202 | 76 |
| 41000 | 66 |
| 49410 | 57 |
| 62100 | 54 |
| 70201 | 53 |
| 70102 | 49 |
| 71120 | 40 |
| 78100 | 34 |

### Phoenix Signal Clusters
- **3,528 entity pairs** flagged as potential phoenix signals
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
