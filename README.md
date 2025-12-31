# Oracle Exadata → SparkSQL Migration Playbook

Repositorio para migrar workloads **Oracle Exadata** (SQL + performance patterns) hacia **SparkSQL** en un data lake (Parquet/Delta/Iceberg).

> Diferencia clave: Exadata acelera SQL con **Smart Scan / Storage Offload / HCC / Indexes**.
> En Spark, el performance se gana con **data layout (partitioning/bucketing/ZORDER)**, **file format**, y **buenas prácticas de joins/aggregations**.

---

## ¿Qué incluye?

- `docs/` — guía estratégica (assessment, mapping de features Exadata, checklist, performance)
- `cases/` — recetas de migración con ejemplos Oracle → SparkSQL (cada caso con README)
- `templates/` — plantillas de validación (conteos, checksums, reconciliación)
- `snippets/` — snippets reutilizables
- `runbooks/` — runbooks de ejecución (export/ingest, tuning, control de calidad)

---

## Ruta recomendada de migración (alto nivel)

1. **Inventario** de queries (top N por consumo / tiempo / frecuencia)
2. **Clasificar** por patrón:
   - filtros + agregaciones (smart scan)
   - star-schema joins (bloom filters / join offload)
   - jerarquías / analíticas
   - MVs / cache / reports
3. **Diseño de datos** en lake:
   - formato (Parquet vs Delta/Iceberg)
   - particiones (fecha, región, tenant, etc.)
   - clustering/bucketing (si aplica)
4. **Reescritura SQL** (Oracle → SparkSQL) + eliminar hints
5. **Validación**: row counts + sum checks + diffs
6. **Tuning**: broadcast joins, skew, adaptive execution, partition pruning
7. **Operacionalización**: jobs, scheduling, SLAs, monitoreo

---

## Índice de casos (Exadata-aware)

| Caso | Enfoque Exadata | Migración en Spark |
|---|---|---|
| [01 - Hints & Parallel](cases/01-hints-parallel/README.md) | `/*+ PARALLEL */`, hints | remover hints + tuning Spark |
| [02 - Smart Scan / filter pushdown](cases/02-smart-scan-filter-pushdown/README.md) | Offload de predicados | particiones + pushdown Parquet |
| [03 - Partition pruning](cases/03-partition-pruning/README.md) | Range/list partitions | particionado en lake + evitar funciones |
| [04 - Indexes vs file layout](cases/04-indexes-vs-layout/README.md) | B-tree/bitmap | bucketing/clustering + stats |
| [05 - Bloom filters / star joins](cases/05-star-joins-bloom/README.md) | join acceleration | broadcast + AQE + skew fixes |
| [06 - Materialized Views](cases/06-materialized-views/README.md) | query rewrite / refresh | tablas derivadas + incremental |
| [07 - Result Cache](cases/07-result-cache/README.md) | cache resultados | cache/persist + lakehouse caching |
| [08 - Flashback / Time travel](cases/08-flashback-time-travel/README.md) | `AS OF TIMESTAMP` | Delta/Iceberg time travel |
| [09 - Analíticas (window)](cases/09-window-analytics/README.md) | heavy analytics | ventanas + particiones correctas |
| [10 - MERGE / SCD](cases/10-merge-scd/README.md) | upserts | Delta MERGE / SCD2 patterns |
| [11 - Datatypes & NLS](cases/11-datatypes-nls/README.md) | NUMBER/NLS/DATE | casting + formatos + timezone |
| [12 - Minus/set semantics](cases/12-set-semantics/README.md) | MINUS, duplicates | EXCEPT / EXCEPT ALL |

---

## Docs esenciales

- [Mapa de features Exadata → Spark](docs/exadata-feature-map.md)
- [Checklist de migración](docs/migration-checklist.md)
- [Performance & tuning en Spark](docs/spark-performance-tuning.md)
- [Estrategia de validación](docs/validation-strategy.md)

---

## Nota
Este repo es neutral respecto al lakehouse:
- Si usas **Delta Lake**, puedes usar `MERGE` y time travel.
- Si usas **Iceberg**, hay alternativas equivalentes.
- Si usas Parquet “plano”, algunas capacidades requieren jobs adicionales.

---

## Licencia
MIT
