# Project Charter: SEC Disclosure Integrity Platform

**Author:** Atif Memon
**Status:** Draft, Phase 0

## 1. The problem

Public companies file financial statements with the SEC every quarter. Those
filings are not final. Companies file amendments, and they restate prior-period
figures inside later filings.

The SEC publishes this data deliberately unprocessed: uncorrected, "as filed"
submissions containing multiple reporting periods including amendments of prior
submissions, which may contain redundancies, inconsistencies, and discrepancies.

A figure pulled six months ago may no longer be the figure the company reports
today, and the raw source keeps no record of what changed, when, or by how much.
There is no built-in revision history.

The raw format is a second barrier: quarterly ZIP archives of tab-separated text,
four interrelated files per quarter with no enforced keys between them, filer-
invented tags mixed with standard taxonomy tags, and a schema that has changed
over the dataset's lifetime.

## 2. Who needs this

| Stakeholder | Decision they make | What they need |
|---|---|---|
| Credit risk analyst | Whether to extend or reprice credit | Whether a filer's figures are stable or frequently revised |
| Audit team | Where to focus review effort | Which filers and industries restate most often |
| Data platform team | Whether downstream reports can be trusted | Row counts, validation pass rates, freshness |
| Index or data vendor | Which value to publish | Current value plus full revision history |

Primary user is the credit risk analyst. Where requirements conflict, they win.

## 3. Questions the platform must answer

1. How many financial facts were revised after their original filing, by quarter?
2. Which filers revise most frequently, over the last eight quarters?
3. What is the magnitude of revisions, as percent change from the original value?
4. Which industries (by SIC code) have the highest revision rates?
5. What is the median lag between period end date and filing date, by filer size?
6. What share of a filer's tags are custom rather than standard taxonomy tags?
7. For a company, tag, and period: current value plus every prior reported value?
8. For Revenues, Assets, and NetIncomeLoss: latest reported value by company/period?
9. How many records failed validation in the latest load, by rejection reason?
10. When was each Gold table last refreshed, and is it stale?

Questions 1 to 4 are the product. Questions 9 and 10 prove the pipeline works.

## 4. Success metrics

**Business metrics**
- Revision rate: revised facts as a percentage of total facts, by quarter
- Median absolute revision magnitude, as a percentage of the original value
- Median filing lag in days, from period end to filing date
- Custom tag ratio per filer

**Platform metrics**
- Validation pass rate above 98 percent of Bronze rows reaching Silver
- Zero orphaned facts in Silver
- Idempotent: two consecutive runs on the same input give identical row counts
- Gold refresh within a target runtime, baselined in Phase 12
- Every Gold table has table and column comments in Unity Catalog

## 5. Grain decisions

**Silver fact grain:** one row per (accession number, tag, tag version, period,
quarters, segments, coregistrant). Matches the source NUM natural key, so Silver
preserves the source faithfully with cleaning applied but no collapsing.

**Gold versioned fact:** one row per (filer, tag, period, quarters, version) with
validity dates. This is SCD Type 2. It exists to answer question 7.

**Gold current fact:** one row per (filer, tag, period, quarters) holding the
latest value. Derived from the versioned fact so question 8 and the dashboard
stay simple and fast.

Rationale for both: analysts asking "what is revenue" want one row. Analysts
asking "has revenue changed" need all of them. Serving both from one table
forces every consumer to write windowing logic, which is a design smell.

## 6. Scope

**In scope**
- Financial Statement Data Sets, quarterly ZIP releases
- All four files: SUB, TAG, NUM, PRE
- Initial build: 8 most recent quarters. Full history backfilled in Phase 9.
- Batch processing on a scheduled job

**Out of scope, with reasons**
- Financial Statement *and Notes* Data Sets. Larger, adds no new concept.
- EDGAR full-text and submissions APIs. Different pattern, no added value.
- Streaming. Source publishes quarterly. Streaming would be decoration.
- Accounting interpretation. We report that a figure changed, not whether the
  restatement was appropriate. Metrics chosen are structural, not judgment based.
- Machine learning. No prediction needed for any committed question.

## 7. Known data hazards

| Hazard | Why it matters | Handled in |
|---|---|---|
| Same fact in multiple filings with different values | This is the product | Phase 8, SCD Type 2 |
| Facts referencing a submission missing from SUB | Orphans corrupt joins | Phase 6 |
| Custom tags absent from the TAG file | Breaks the tag dimension | Phase 6, quarantine |
| NUM gained a segments column in Dec 2024 reprocessing | Schema changes mid-history | Phase 5 |
| Amended filings arrive quarters after the period | Late-arriving data | Phase 9 |
| Re-running a load could double-count rows | Breaks every metric | Phase 7, MERGE |
| Numeric values as text, inconsistent nulls | Silent coercion errors | Phase 5 |
| SEC requires User-Agent and rate-limits traffic | Requests get blocked | Phase 4 |

## 8. Non-goals for the build

- Not optimizing for cost. Free Edition constrains compute anyway.
- Not building full CI/CD. Asset Bundles and unit tests only.
- Not supporting multiple users or row-level security. Single-owner project.

## 9. Definition of done

All ten committed questions answerable from Gold, pipeline runs on a schedule and
re-runs safely, validation results visible in a table, README a hiring manager can
follow, and the author can present the whole thing in five minutes without notes.
