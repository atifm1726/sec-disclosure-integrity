# Data Contract: SEC Financial Statement Data Sets

**Author:** Atif Memon
**Profiled from:** 2026q1
**Status:** Phase 3

---

## 1. Source

| Item | Value |
|---|---|
| Publisher | US SEC, DERA |
| URL pattern | https://www.sec.gov/files/dera/data/financial-statement-data-sets/{yyyy}q{q}.zip |
| Cadence | Quarterly, roughly two month lag after quarter end |
| Format | ZIP containing 4 tab-delimited .txt files plus readme.htm |
| Encoding | UTF-8 |
| Delimiter | Tab |
| Line ending | Newline |
| Header | Row 1, column names in lowercase |
| Access | Requires a User-Agent header with name and email |
| Zip size | Approx 60 to 120 MB |

## 2. Files and grain

| File | One row is | Size (2026q1) |
|---|---|---|
| sub.txt | One EDGAR submission, one filing by one company | 1.9 MB |
| tag.txt | One accounting tag definition, standard or custom | 19.7 MB |
| num.txt | One numeric value from a primary financial statement | 559.4 MB |
| pre.txt | One line as presented on a statement page | 90.6 MB |

num grain, stated fully: one numeric value, for one filing, one accounting tag
and taxonomy version, one period end date, one duration in quarters, one unit
of measure, one segment breakdown, and one co-registrant.

## 3. Keys

| File | Documented key | Measured finding |
|---|---|---|
| sub | adsh | Holds |
| tag | tag + version | Holds |
| num | adsh, tag, version, coreg, ddate, qtrs, uom | Fails, see section 4 |
| pre | adsh, report, line | Not yet tested |

## 4. Key decision: the segments column

The SEC readme documents a 7 column key for NUM. The delivered files contain a
10th column named segments, added in the December 2024 reprocessing, sitting at
position 7 between uom and coreg. It is not in the published key definition.

Measured on 2026q1:

| Test | Result |
|---|---|
| Total rows | 3,690,955 |
| Distinct on documented 7 columns | 1,706,512 |
| Duplicates under 7 column key | 1,984,443 (53.8%) |
| Distinct on 8 columns including segments | 3,690,938 |
| Duplicates under 8 column key | 17 (0.0005%) |
| Rows with a non-empty segments value | 2,185,031 (59.2%) |

Most common segments values:

    EquityComponents=CommonStock;                 90,320
    EquityComponents=AdditionalPaidInCapital;     75,386
    EquityComponents=RetainedEarnings;            64,400
    ConsolidatedEntities=ParentCompany;           46,545
    ConsolidationItems=OperatingSegments;         13,206
    ClassOfStock=CommonClassA;                    12,617

Decision: the NUM natural key is 8 columns, including segments.

Reasoning: segments values are component breakdowns of a figure, for example
total equity versus its common stock and retained earnings parts. These share
all seven documented key columns and differ only by segments. Excluding segments
from the key would treat 1.98M genuinely distinct facts as duplicates.

Downstream consequence: Silver keeps every row. The Gold fundamentals mart
filters to segments = '' so cross-company comparisons use consolidated totals
only and do not double count a company total against its own breakdowns.

Open question: ConsolidatedEntities=ParentCompany overlaps conceptually with the
coreg column. Both describe which legal entity a figure belongs to. Revisit when
building dim_filer in Phase 10.

## 5. Volume expectations

| File | Rows (2026q1) | Tolerance band | Action outside band |
|---|---|---|---|
| sub | 6,169 | TBD after 2nd quarter | Alert, do not fail |
| tag | 91,794 | TBD | Alert |
| num | 3,690,955 | TBD | Alert |
| pre | 733,134 | TBD | Alert |

Bands to be set in the Phase 3 exercise after profiling 2024q2.

Note: pre has fewer rows than num. Expected, because num carries values for many
periods while pre describes the statement layout once.

## 6. Column reference

### sub, columns in scope

| Column | Cast to | Nullable | Missing (2026q1) | Notes |
|---|---|---|---|---|
| adsh | string | No | 0% | PK, format nnnnnnnnnn-nn-nnnnnn |
| cik | string | No | 0% | Company id, keep as string to preserve leading zeros |
| name | string | No | 0% | As of filing date, can change over time |
| sic | string | Yes | 3.0% | Industry, needs an Unknown bucket |
| form | string | No | 0% | /A suffix means amendment |
| period | date | No | 0% | Balance sheet date |
| fy | int | Yes | 4.5% | Correlated with fp |
| fp | string | Yes | 4.5% | FY, Q1-Q4, H1, H2, M9, T1-T3, M8, CY |
| filed | date | No | 0% | Drives restatement precedence |
| accepted | timestamp | No | 0% | Tiebreaker when filed dates match |
| prevrpt | boolean | No | 0% | 1 = later amended, validation signal for Phase 8 |
| detail | boolean | No | 0% | Footnote detail tagged |
| afs | string | Yes | 2.2% | Filer size, needs an Unknown bucket |
| nciks | int | No | 0% | Count of registrants on the filing |
| aciks | string | Yes | 98.0% | Additional CIKs, null when nciks = 1, keep |

Dropped in Silver, kept in Bronze: the address block (bas1, bas2, baph, cityba,
zipba, stprba, countryba and the mailing equivalents), plus ein, instance, wksi,
former, changed. Reason: no charter question uses them.

### num, all columns in scope

| Column | Cast to | Nullable | Notes |
|---|---|---|---|
| adsh | string | No | Key 1, FK to sub |
| tag | string | No | Key 2 |
| version | string | No | Key 3, equals adsh when the tag is custom |
| ddate | date | No | Key 4, rounded to nearest month end |
| qtrs | int | No | Key 5, duration in quarters |
| uom | string | No | Key 6 |
| segments | string | Yes | Key 7, empty means consolidated |
| coreg | string | Yes | Key 8, null means consolidated entity |
| value | decimal(28,4) | Yes | 139,725 rows empty (3.8%) |
| footnote | string | Yes | Free text, may contain quote characters |

### tag, columns in scope

| Column | Cast to | Notes |
|---|---|---|
| tag, version | string | Composite key |
| custom | boolean | 1 = filer invented, charter question 6 |
| abstract | boolean | 1 = heading, carries no numeric value |
| datatype | string | Null when abstract = 1 |
| iord | string | I = instant, D = duration, cross check against qtrs |
| crdr | string | C or D, natural balance |
| tlabel | string | Display label for dashboards |

## 7. Value ranges observed

qtrs distribution:

| Value | Count | Meaning |
|---|---|---|
| 0 | 1,778,875 | Point in time, balance sheet |
| 4 | 1,546,875 | Full year |
| 1 | 208,109 | One quarter |
| 2 | 78,414 | Six months |
| 3 | 77,950 | Nine months |
| 5 to 128 | approx 600 total | Multi-year cumulative, see below |

Values above 4 were inspected. They are concentrated in equity and buyback tags
such as TreasuryStockSharesAcquired, PaymentsForRepurchaseOfCommonStock and
ShareBasedCompensation, with normal year-end ddate values. These are cumulative
since-inception figures, for example total shares repurchased since a buyback
programme began. They are legitimate, not errors.

ddate range: min 19880531, max 20321031.

The maximum is six years in the future and cannot be legitimate for a filing
received in 2026 Q1. Filer typo. Note also that a quarterly file contains ddate
values spanning decades, because a single filing reports current and prior
periods. The file name indicates when filings were received, not what periods
they cover.

## 8. Null expectations

Expected sparse, keep anyway:

| Column | Missing | Why |
|---|---|---|
| aciks | 98.0% | Only populated when nciks > 1 |
| bas2, mas2 | 54.9%, 54.8% | Second address line, most companies have none |
| former, changed | 43.9% each | Only when a company renamed, always populated together |
| coreg | High | Null means consolidated entity, meaningful not missing |
| segments | 40.8% | Empty means consolidated total |

Spec violations found, these should be zero:

| Column | Missing | Spec says |
|---|---|---|
| countryba | 6.5% | May not be null |
| fye | 0.2% | May not be null |
| cityba | 0.1% | May not be null |

Correlated pairs, a free consistency check: former/changed, fy/fp, nciks/aciks.
If one is populated and its partner is not, the row is suspect.

## 9. Referential integrity

Documented relationships:

| From | Columns | To |
|---|---|---|
| num | adsh | sub.adsh |
| num | tag, version | tag.tag, tag.version |
| pre | adsh | sub.adsh |
| pre | tag, version | tag.tag, tag.version |
| pre | adsh, tag, version | num same columns |

Measured orphan counts: TBD, Part H not yet run.

## 10. Known hazards

| Hazard | Impact | Handled in |
|---|---|---|
| Quote characters in text fields | Default CSV quote handling swallows line breaks and undercounts rows | Phase 5, set quote option to empty |
| coreg is null and part of the key | Nulls do not compare equal, MERGE silently drops rows | Phase 7, substitute a sentinel value |
| segments absent from published key | Deduplicating on 7 columns discards 54% of facts | Section 4 |
| segments column inserted at position 7 | Position-based reads silently shift | Phase 5, read by column name only |
| 2009q1.zip contains headers only, no rows | An empty load is by design, not a failure | Phase 9 backfill |
| ddate spans decades and reaches into the future | A date dimension built on the file name will be wrong | Phase 10 |
| pre fans out against num | The same tag appears on more than one statement, joins multiply rows | Phase 10 |
| tag contains all standard taxonomy tags | Many tag rows never appear in num, this is not an error | Phase 6 |
| Multi-registrant filings, 2% of rows | One adsh maps to several companies | Phase 10, attribute to primary cik |

## 11. Validation rules

Each rule is traceable to a measurement above. Reason codes flow into the Phase 6
quarantine table and the Phase 11 quality dashboard.

| # | Rule | Reason code | Expected volume |
|---|---|---|---|
| 1 | adsh matches ^[0-9]{10}-[0-9]{2}-[0-9]{6}$ | BAD_ADSH_FORMAT | 0 |
| 2 | ddate matches ^[0-9]{8}$ | BAD_DDATE_FORMAT | 0 |
| 3 | ddate is not later than the load date | DDATE_FUTURE | Under 50 |
| 4 | ddate is not earlier than 19900101 | DDATE_TOO_OLD | Under 50 |
| 5 | value, when non-empty, casts to double without producing null | VALUE_NOT_NUMERIC | 0 |
| 6 | The 8 column NUM key is unique within a quarterly load | DUPLICATE_KEY | Under 50 |
| 7 | Every num.adsh exists in sub.adsh | ORPHAN_SUBMISSION | 0 |
| 8 | Every num tag and version pair exists in tag | ORPHAN_TAG | Under 100 |
| 9 | cityba, fye and countryba are populated | MISSING_REQUIRED_FIELD | Under 500 |
| 10 | qtrs is between 0 and 4 | QTRS_NONSTANDARD | Approx 600, flag only, do not reject |
| 11 | Row counts fall within the section 5 tolerance band | VOLUME_ANOMALY | Alert, do not fail |
| 12 | Correlated pairs are both populated or both empty | CORRELATED_PAIR_MISMATCH | 0 |

Rule 10 flags rather than rejects. The values are legitimate multi-year
cumulative figures, but they are not comparable to quarterly or annual figures
and must be excluded from period-based aggregations.

## 12. Open questions

1. Tolerance bands for row counts, needs a second quarter, Phase 3 exercise.
2. Does 2024q2 contain the segments column? Confirms the schema evolution event.
3. Orphan counts in both directions, Part H.
4. Is the pre key of adsh, report and line actually unique?
5. Relationship between ConsolidatedEntities in segments and the coreg column.
6. How to attribute revisions on multi-registrant filings, 2% of rows.
7. Should segments be parsed into structured Dimension and Member columns in
   Silver? Decision deferred to Phase 10, but parse in Silver while the code is
   fresh to keep the option open.