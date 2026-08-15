# Architecture

**Project:** SEC Disclosure Integrity Platform
**Status:** Phase 1

## Data flow

SEC quarterly ZIP
  -> download and unzip (Phase 4)
  -> /Volumes/sec_dev/landing/raw/<quarter>/   (four TSV files)
  -> bronze.sub | bronze.tag | bronze.num | bronze.pre  (raw, append-only)
  -> validation and referential integrity (Phase 6)
       valid   -> silver.submission | silver.tag | silver.financial_fact
       invalid -> silver.quarantine (with reason code)
  -> gold.dim_filer | dim_tag | dim_period
     gold.fact_financial_fact_versioned  (SCD Type 2, revision history)
     gold.fact_financial_fact_current    (latest value per fact)
     gold.mart_fundamentals              (Revenues, Assets, NetIncomeLoss)
  -> Databricks SQL dashboard + Power BI report

Rule: each layer reads only from the layer immediately above it.
Gold never reads Bronze.

## Namespace

| Catalog | Schema | Contents |
|---|---|---|
| sec_dev | landing | Volume holding unzipped source files |
| sec_dev | bronze | sub, tag, num, pre |
| sec_dev | silver | submission, tag, financial_fact, quarantine, dq_results |
| sec_dev | gold | dim_filer, dim_tag, dim_period, fact_*, mart_fundamentals |

Single catalog because Free Edition allows one workspace and one metastore per
account. Production would use sec_dev, sec_staging, sec_prod as separate catalogs
promoted by the same Asset Bundle. Documented in Phase 17.

## Decision records

### ADR-001: Delta Lake for all tables
**Decision:** Every table is Delta, not plain Parquet.
**Why:** Schema enforcement stops a malformed quarterly load from silently
corrupting a table. Schema evolution is required because the SEC added a segments
field to NUM in December 2024. ACID means a job failing halfway leaves no partial
write to clean up.
**Rejected:** Plain Parquet. No transaction log, so no atomic writes, no
enforcement, no MERGE.

### ADR-002: Batch, not streaming
**Decision:** Scheduled batch job, manual triggers during development.
**Why:** The source publishes quarterly. Streaming adds operational complexity
and delivers no latency benefit.
**Rejected:** Structured Streaming with Auto Loader. Right for continuously
arriving files, wrong for a quarterly ZIP release.

### ADR-003: Manual PySpark and SQL, not declarative pipelines
**Decision:** Lakeflow Jobs orchestrating notebooks.
**Why:** The declarative framework abstracts away MERGE semantics, idempotency,
and incremental read logic. Those are the core skills this project exists to
build. Writing them by hand means being able to explain them.
**Rejected:** Lakeflow Declarative Pipelines. The right production choice for a
team optimising delivery speed, and the natural refactor target.

### ADR-004: Four separate Bronze tables
**Decision:** bronze.sub, bronze.tag, bronze.num, bronze.pre stay separate.
**Why:** Different grains and different natural keys. Merging at Bronze would
force a join before validation, and the Phase 6 referential integrity check needs
them independent so orphaned rows are detectable.
**Rejected:** One wide Bronze table. Loses which file a defect came from.

### ADR-005: Two Gold fact tables, versioned and current
**Decision:** Ship both.
**Why:** Revision history is the product, so the versioned table is mandatory.
Forcing every consumer to write windowing logic to find the latest value
guarantees that logic is eventually written wrong somewhere. Materialise
"current" once, correctly.
**Rejected:** Versioned only. Pushes complexity onto every consumer, including
Power BI, where it performs badly.

### ADR-006: Delta time travel is not a business feature
**Decision:** Time travel for operational recovery and debugging only. Business
revision history served exclusively by the SCD Type 2 fact table.
**Why:** Time travel answers "what did this table look like last week", an
operations question. It has retention limits, is not queryable as a dimension,
and disappears after VACUUM. Business history must be modelled explicitly.

### ADR-007: Unity Catalog Volumes, not DBFS
**Decision:** All file paths use /Volumes/... .
**Why:** Volumes are governed by Unity Catalog, so access control and lineage
apply to files as well as tables. DBFS predates Unity Catalog and is ungoverned.
**Rejected:** DBFS. Still works, appears in older tutorials, and is a visible
sign of dated practice.

### ADR-008: Table layout deferred to Phase 12
**Decision:** No partitioning or clustering keys until there is a measured
baseline.
**Why:** Databricks recommends liquid clustering over partitioning for new
tables, but the correct clustering keys depend on which columns queries actually
filter on, and those queries do not exist until Gold exists. Choosing keys now
would be guessing. The before-and-after measurement is worth more than an early
guess.

## Glossary

| Term | Meaning here |
|---|---|
| Driver | Coordinating process that plans work and assigns tasks |
| Executor | Worker process that reads and computes on one slice of data |
| Spark partition | Runtime slice processed by one task. Not storage layout. |
| Table partitioning | Physical storage layout declared on the table |
| Transformation | Describes a change, runs nothing (filter, select, join) |
| Action | Forces execution (count, collect, show, display, write) |
| Lazy evaluation | Transformations recorded, not run, until an action asks |
| Shuffle | Moving data between executors. The expensive operation. |
| Delta Lake | Parquet plus a transaction log giving ACID and time travel |
| Unity Catalog | Governance layer: naming, permissions, comments, lineage |
| Volume | Governed folder in Unity Catalog for files that are not tables |
| Medallion | Bronze (what arrived), Silver (what is true), Gold (what is useful) |
| Idempotent | Running it twice gives the same result as running it once |
| SCD Type 2 | Keep old rows with an end date, insert new rows, preserving history |
