# Threshold Clustering Analysis

This analysis identifies statistically unusual patterns in Dutch public procurement
contract values relative to EU mandatory tender thresholds. The analysis detects
potential threshold avoidance by examining clustering just below thresholds:
- Services threshold: €221,000
- Works threshold: €5,538,000

## Methodology

### Data
- Source: TenderNed public procurement notices (2023-2025)
- Dataset: 15866 contracts with valid values

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
|    | bucket   |   count |   percentage |
|---:|:---------|--------:|-------------:|
|  0 | 0-10%    |    5696 |    35.9007   |
|  1 | 10-20%   |     214 |     1.3488   |
|  2 | 20-30%   |     256 |     1.61351  |
|  3 | 30-40%   |     252 |     1.5883   |
|  4 | 40-50%   |     250 |     1.5757   |
|  5 | 50-60%   |     225 |     1.41813  |
|  6 | 60-70%   |     189 |     1.19123  |
|  7 | 70-80%   |     249 |     1.56939  |
|  8 | 80-90%   |     212 |     1.33619  |
|  9 | 90-95%   |     154 |     0.970629 |
| 10 | 95-99%   |     105 |     0.661793 |
| 11 | 99-100%  |      43 |     0.27102  |
| 12 | >100%    |    8021 |    50.5546   |

**HHI:** 3863.19
Lower HHI indicates more uniform distribution; higher HHI indicates concentration.

**Threshold Anomalies:**


**McCrary Test:**
- Near-threshold observations: 0
- Far-left observations: 8169
- Far-right observations: 0
- Chi-square statistic: nan
- P-value: nan
- Z-score: nan

### Works Threshold (€5,538,000)

**Distribution:**
|    | bucket   |   count |   percentage |
|---:|:---------|--------:|-------------:|
|  0 | 0-10%    |   10650 |   67.1247    |
|  1 | 10-20%   |    1593 |   10.0403    |
|  2 | 20-30%   |     760 |    4.79012   |
|  3 | 30-40%   |     427 |    2.69129   |
|  4 | 40-50%   |     342 |    2.15555   |
|  5 | 50-60%   |     288 |    1.8152    |
|  6 | 60-70%   |     209 |    1.31728   |
|  7 | 70-80%   |     168 |    1.05887   |
|  8 | 80-90%   |     127 |    0.800454  |
|  9 | 90-95%   |      82 |    0.516828  |
| 10 | 95-99%   |      27 |    0.170175  |
| 11 | 99-100%  |      15 |    0.0945418 |
| 12 | >100%    |    1178 |    7.42468   |

**HHI:** 4703.59

**Threshold Anomalies:**


**McCrary Test:**
- Near-threshold observations: 0
- Far-left observations: 1220
- Far-right observations: 0
- Chi-square statistic: nan
- P-value: nan
- Z-score: nan

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
