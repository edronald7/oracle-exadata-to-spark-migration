# Contributing

## Add a new Exadata-focused case
Create a folder under `cases/NN-short-title/` with:
- `README.md` (Exadata behavior, Oracle SQL, SparkSQL rewrite, perf notes, validation)
- `oracle.sql`
- `sparksql.sql`
- Optional: `test_data/`, `expected/`, `pyspark/`

## Principles
- Always document the **Exadata feature** being replaced (offload, HCC, partitioning, MV, result cache, hints).
- Always include **data layout** assumptions in Spark (partitioning, bucketing, file format).
- Include a **validation query** (row counts, checksums) when possible.
