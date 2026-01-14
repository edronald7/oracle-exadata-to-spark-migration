# Oracle Exadata → Apache Spark: Guía Comparativa SQL y Programática

**Repositorio de aprendizaje** para analistas y data engineers que trabajan con Oracle Exadata y necesitan aprender el ecosistema Apache Spark en la nube.

> **🎯 Objetivo**: Comparar sintaxis, patrones y mejores prácticas entre:
> - **Oracle Exadata SQL** (Smart Scan, Storage Offload, HCC, Indexes)
> - **Spark SQL** (data layout, partitioning, bucketing, file formats)
> - **PySpark** (DataFrame API, Python)
> - **Spark Scala** (Dataset API, type-safe)

---

## 👥 ¿Para quién es este repositorio?

| Perfil | Qué encontrarás |
|--------|-----------------|
| **Analistas SQL** | Traducción directa de queries Oracle a Spark SQL con explicaciones |
| **Data Engineers** | Implementaciones en PySpark y Scala con best practices |
| **Arquitectos de Datos** | Estrategias de migración y diseño de data lakes |
| **DBAs Oracle** | Mapeo de features Exadata a capacidades de Spark |
| **Equipos Cloud** | Guías de deployment en AWS, Azure y GCP |

---

## 🎓 Rutas de Aprendizaje

### 📘 Ruta para Analistas (SQL-first)
1. Lee [SQL vs DataFrame API](docs/sql-vs-dataframe-api.md)
2. Comienza con [Caso 02: Smart Scan](cases/02-smart-scan-filter-pushdown/)
3. Practica con notebooks en `notebooks/`
4. Ejecuta en [Databricks](cloud/azure/databricks-setup.md) o [EMR](cloud/aws/emr-setup.md)

### 💻 Ruta para Engineers (Code-first)
1. Lee [PySpark Best Practices](docs/pyspark-best-practices.md)
2. Estudia implementaciones en `cases/*/3_pyspark.py` y `cases/*/4_scala.scala`
3. Ejecuta generadores de datos: `data/generators/`
4. Implementa pipelines siguiendo [runbooks](runbooks/)

### 🏗️ Ruta para Arquitectos (Strategy-first)
1. Lee [Mapa de features Exadata → Spark](docs/exadata-feature-map.md)
2. Revisa [Checklist de migración](docs/migration-checklist.md)
3. Diseña arquitectura con [Cloud Deployment Guide](docs/cloud-deployment-guide.md)
4. Valida con [estrategia de testing](docs/validation-strategy.md)

---

## 🏗️ ¿Qué incluye?

- **`docs/`** — Guías conceptuales y estratégicas
  - Mapeo de features Exadata → Spark
  - Best practices PySpark y Scala
  - Estrategias de deployment en cloud
- **`cases/`** — 12 casos de uso con **4 implementaciones** cada uno:
  - `1_oracle.sql` - Query Oracle original
  - `2_sparksql.sql` - Equivalente en Spark SQL
  - `3_pyspark.py` - Implementación PySpark
  - `4_scala.scala` - Implementación Scala
- **`data/`** — Generadores de datos de prueba ejecutables
- **`notebooks/`** — Jupyter y Databricks notebooks interactivos
- **`cloud/`** — Guías específicas para AWS, Azure y GCP
- **`templates/`** — Código reutilizable (validación, performance, testing)
- **`runbooks/`** — Procedimientos paso a paso de deployment
- **`snippets/`** — Fragmentos de código reutilizables

---

## 📚 Índice de Casos

Cada caso incluye: **Oracle SQL** | **Spark SQL** | **PySpark** | **Scala** | **Datos de prueba** | **Notebook**

### 🔵 Casos Básicos: Features Exadata Core

| # | Caso | Exadata Feature | SQL | PySpark | Scala | Notebook |
|---|------|-----------------|-----|---------|-------|----------|
| 01 | [Hints & Parallel](cases/01-hints-parallel/) | `/*+ PARALLEL */`, optimizer hints | ✅ | ✅ | ✅ | ✅ |
| 02 | [Smart Scan / Filter Pushdown](cases/02-smart-scan-filter-pushdown/) | Storage offload, predicate pushdown | ✅ | ✅ | ✅ | ✅ |
| 03 | [Partition Pruning](cases/03-partition-pruning/) | Range/list partitions, partition-wise ops | ✅ | ✅ | ✅ | ✅ |
| 04 | [Indexes vs File Layout](cases/04-indexes-vs-layout/) | B-tree/bitmap indexes | ✅ | ✅ | ✅ | ✅ |
| 05 | [Star Joins / Bloom Filters](cases/05-star-joins-bloom/) | Bloom filter join acceleration | ✅ | ✅ | ✅ | ✅ |
| 06 | [Materialized Views](cases/06-materialized-views/) | MV query rewrite, refresh | ✅ | ✅ | ✅ | ✅ |
| 07 | [Result Cache](cases/07-result-cache/) | Result cache, query cache | ✅ | ✅ | ✅ | ✅ |
| 08 | [Flashback / Time Travel](cases/08-flashback-time-travel/) | `AS OF TIMESTAMP`, flashback | ✅ | ✅ | ✅ | ✅ |
| 09 | [Window Analytics](cases/09-window-analytics/) | Window functions, analytics | ✅ | ✅ | ✅ | ✅ |
| 10 | [MERGE / SCD](cases/10-merge-scd/) | MERGE statement, upserts | ✅ | ✅ | ✅ | ✅ |
| 11 | [Datatypes & NLS](cases/11-datatypes-nls/) | NUMBER, DATE, NLS settings | ✅ | ✅ | ✅ | ✅ |
| 12 | [Set Semantics](cases/12-set-semantics/) | MINUS, INTERSECT, duplicates | ✅ | ✅ | ✅ | ✅ |

### ⭐ Casos Avanzados: Día a Día del Data Engineer

| # | Caso | Tema | Criticidad | SQL | PySpark | Scala | Notebook |
|---|------|------|------------|-----|---------|-------|----------|
| 13 | [CDC / Incremental Ingestion](cases/13-cdc-incremental/) | Change Data Capture, MERGE, dedup | ⭐⭐⭐⭐⭐ | ✅ | ✅ | ✅ | 🔜 |
| 14 | [Data Quality & Error Handling](cases/14-data-quality/) | Bad records, quarantine, Great Expectations | ⭐⭐⭐⭐⭐ | ✅ | ✅ | 🔜 | 🔜 |
| 15 | [Spark Structured Streaming](cases/15-streaming/) | Kafka, near real-time, watermarking | ⭐⭐⭐⭐⭐ | ✅ | ✅ | 🔜 | 🔜 |
| 16 | [Orquestación Airflow](cases/16-orchestration/) | DAGs, scheduling, retries | ⭐⭐⭐⭐⭐ | — | ✅ | 🔜 | 🔜 |
| 17 | [Cost Optimization](cases/17-cost-optimization/) | Shuffle, compaction, spot instances | ⭐⭐⭐⭐⭐ | ✅ | ✅ | 🔜 | 🔜 |
| 18 | [Schema Evolution](cases/18-schema-evolution/) | ADD/DROP columns, mergeSchema | ⭐⭐⭐⭐ | ✅ | ✅ | 🔜 | 🔜 |
| 19 | [Troubleshooting & Debugging](cases/19-troubleshooting/) | OOM, skew, slow queries, Spark UI | ⭐⭐⭐⭐⭐ | — | ✅ | 🔜 | 🔜 |
| 20 | [Integraciones Ecosistema](cases/20-integrations/) | JDBC, Kafka, Redshift, Snowflake, MLflow | ⭐⭐⭐⭐ | ✅ | ✅ | 🔜 | 🔜 |

> 💡 **Leyenda**: ✅ Disponible | 🔜 Próximamente | — No aplica

---

## 🚀 Quick Start

### Opción 1: Ejecutar Localmente (Docker)

```bash
# 1. Clonar repositorio
git clone https://github.com/tu-usuario/oracle-exadata-to-spark-migration.git
cd oracle-exadata-to-spark-migration

# 2. Iniciar Spark con Docker
docker run -it -p 8888:8888 \
  -v $(pwd):/workspace \
  jupyter/pyspark-notebook

# 3. Generar datos de prueba
python data/generators/generate_all.py --size small

# 4. Ejecutar caso de ejemplo
cd cases/01-hints-parallel
spark-submit 3_pyspark.py
```

### Opción 2: Cloud (AWS EMR)

```bash
# Ver guía completa en cloud/aws/emr-setup.md
aws emr create-cluster --name "Spark-Learning" \
  --release-label emr-7.0.0 \
  --applications Name=Spark Name=Jupyter
```

### Opción 3: Cloud (Azure Databricks)

```bash
# Ver guía completa en cloud/azure/databricks-setup.md
# 1. Crear workspace en Azure Portal
# 2. Importar notebooks desde notebooks/databricks/
# 3. Ejecutar interactivamente
```

### Opción 4: Cloud (GCP Dataproc)

```bash
# Ver guía completa en cloud/gcp/dataproc-setup.md
gcloud dataproc clusters create spark-learning \
  --region=us-central1 \
  --image-version=2.1
```

---

## 📖 Documentación Completa

### Guías Estratégicas
- [Mapa de features Exadata → Spark](docs/exadata-feature-map.md)
- [Checklist de migración](docs/migration-checklist.md)
- [Estrategia de validación](docs/validation-strategy.md)
- [Cloud Deployment Guide](docs/cloud-deployment-guide.md)

### Guías de Desarrollo
- [PySpark Best Practices](docs/pyspark-best-practices.md)
- [Scala Spark Patterns](docs/scala-spark-patterns.md)
- [SQL vs DataFrame API](docs/sql-vs-dataframe-api.md)
- [Performance & Tuning](docs/spark-performance-tuning.md)

### Deployment por Cloud Provider
- [AWS EMR Setup](cloud/aws/emr-setup.md)
- [Azure Databricks Setup](cloud/azure/databricks-setup.md)
- [GCP Dataproc Setup](cloud/gcp/dataproc-setup.md)

---

## 🛠️ Stack Tecnológico

| Componente | Opciones Soportadas |
|-----------|---------------------|
| **Compute** | Spark 3.5+ (local, EMR, Databricks, Dataproc) |
| **Lenguajes** | SQL, Python 3.10+, Scala 2.12+ |
| **File Formats** | Parquet, Delta Lake, Iceberg |
| **Storage** | S3, ADLS Gen2, GCS, HDFS |
| **Notebooks** | Jupyter, Databricks, Zeppelin |

---

## 📊 Comparativa Oracle vs Spark

| Feature Oracle Exadata | Equivalente Spark | Caso |
|------------------------|-------------------|------|
| Smart Scan / Storage Offload | Partition pruning + predicate pushdown | [02](cases/02-smart-scan-filter-pushdown/) |
| Storage Indexes | Data skipping + Z-ORDER | [04](cases/04-indexes-vs-layout/) |
| Bloom Filter Joins | Broadcast joins + AQE | [05](cases/05-star-joins-bloom/) |
| HCC (Columnar Compression) | Parquet/ORC compression | [02](cases/02-smart-scan-filter-pushdown/) |
| Materialized Views | Delta tables + incremental refresh | [06](cases/06-materialized-views/) |
| Result Cache | `CACHE TABLE` / persist | [07](cases/07-result-cache/) |
| Flashback Query | Delta/Iceberg time travel | [08](cases/08-flashback-time-travel/) |
| Parallel Hints | AQE + partition tuning | [01](cases/01-hints-parallel/) |

---

## 🤝 Contribuir

¡Contribuciones son bienvenidas! Ver [CONTRIBUTING.md](CONTRIBUTING.md) para detalles.

Para agregar un nuevo caso:
1. Crea carpeta `cases/NN-nombre-caso/`
2. Incluye 4 implementaciones: Oracle SQL, Spark SQL, PySpark, Scala
3. Agrega datos de prueba y notebook
4. Documenta en README con comparativa

---

## 📝 Nota sobre Lakehouse Formats

Este repositorio es neutral respecto al formato de lakehouse:
- **Delta Lake**: Soporte completo para MERGE, time travel, ACID
- **Iceberg**: Alternativas equivalentes para todas las features
- **Parquet plano**: Algunas capacidades requieren jobs adicionales

---

## 📄 Licencia

MIT
