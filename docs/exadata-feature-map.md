# Exadata feature map → Spark/Lakehouse

## 1) Smart Scan / Storage Offload
**Exadata:** filtra/proyecta en storage; reduce IO.
**Spark:** logra algo parecido con:
- particionado correcto
- predicate pushdown en Parquet/ORC
- column pruning (seleccionar pocas columnas)
- evitar UDFs que rompan pushdown

## 2) Storage Indexes
**Exadata:** evita IO de regiones que no contienen valores.
**Spark:** data skipping / clustering:
- Z-Ordering (Delta)
- clustering/sorting en archivos (compaction)
- min/max stats por archivo (Parquet)

## 3) Bloom Filters (join acceleration)
**Exadata:** bloom filters para joins masivos.
**Spark:** 
- broadcast joins para dimensiones
- AQE (adaptive query execution)
- skew handling (salting, repartition, hints de Spark)

## 4) HCC (Hybrid Columnar Compression)
**Exadata:** compresión columnar en storage.
**Spark:** Parquet/ORC + compresión (snappy/zstd) + compaction.

## 5) Materialized Views / Query Rewrite
**Exadata:** MVs con refresh y rewrite.
**Spark:** tablas derivadas (gold) + incremental refresh (jobs) + caching.

## 6) Result Cache
**Exadata:** cache de resultados a nivel DB.
**Spark:** `CACHE TABLE`, `persist`, caching del motor/lakehouse.

## 7) Flashback
**Exadata/Oracle:** `AS OF TIMESTAMP/SCN`.
**Lakehouse:** time travel (Delta/Iceberg/Hudi) o snapshots/retención.

## 8) Optimizer stats
**Oracle:** stats del diccionario, histograms.
**Spark:** `ANALYZE TABLE ... COMPUTE STATISTICS` (si aplica), y tuning de joins/partitions.
