# Caso 01: Hints y Paralelismo

Aprende cómo traducir hints de Oracle Exadata a configuraciones y patrones de Spark.

---

## 🎯 Objetivo de Aprendizaje

Entender cómo Spark maneja paralelismo de forma diferente a Oracle:
- **Oracle**: Hints explícitos (`PARALLEL`, `USE_HASH`, `FULL`)
- **Spark**: Adaptive Query Execution (AQE) + configuraciones

---

## 📊 Comparativa de Enfoques

### 1️⃣ Oracle Exadata SQL

**Contexto**: En Exadata usamos hints para controlar el optimizador.

**Archivo**: `1_oracle.sql`

```sql
SELECT /*+ PARALLEL(8) FULL(f) USE_HASH(d) */
  d.region, SUM(f.amount) total
FROM fact_sales f
JOIN dim_region d ON d.region_id = f.region_id
WHERE f.sale_date >= DATE '2025-01-01'
GROUP BY d.region;
```

**Características Exadata**:
- `PARALLEL(8)`: Fuerza 8 parallel workers
- `FULL(f)`: Full table scan en fact_sales
- `USE_HASH(d)`: Hash join con dimensión
- Exadata Smart Scan procesa en storage layer

---

### 2️⃣ Spark SQL

**Enfoque**: Eliminar hints Oracle; usar hints Spark solo cuando necesario.

**Archivo**: `2_sparksql.sql`

```sql
-- SparkSQL: hints Oracle se eliminan; si aplica usar hints de Spark
SELECT /*+ BROADCAST(d) */
  d.region_name, SUM(f.amount) AS total
FROM fact_sales f
JOIN dim_region d ON d.region_id = f.region_id
WHERE f.sale_date >= DATE '2025-01-01'
GROUP BY d.region_name;
```

**Diferencias clave**:
- ❌ No hay `PARALLEL` hint - Spark maneja automáticamente
- ❌ No hay `FULL` hint - predicate pushdown en Parquet
- ✅ `BROADCAST(d)` - solo si dimensión < 10MB
- ✅ AQE optimiza en runtime

**Ejecutar**:
```bash
spark-sql -f 2_sparksql.sql
```

---

### 3️⃣ PySpark (DataFrame API)

**Enfoque**: Programático, testeable, modular.

**Archivo**: `3_pyspark.py`

```python
from pyspark.sql import SparkSession
from pyspark.sql.functions import sum as _sum, broadcast

spark = SparkSession.builder \
    .appName("Case 01") \
    .config("spark.sql.adaptive.enabled", "true") \
    .config("spark.sql.shuffle.partitions", "200") \
    .getOrCreate()

# Leer datos
fact_sales = spark.read.parquet("../../data/output/fact_sales")
dim_region = spark.read.parquet("../../data/output/dim_region")

# Filtrar antes del join (pushdown)
filtered_sales = fact_sales.filter("sale_date >= '2025-01-01'")

# Join con broadcast hint
result = filtered_sales.join(
    broadcast(dim_region),
    "region_id"
).groupBy("region_name") \
 .agg(_sum("amount").alias("total")) \
 .orderBy("total", ascending=False)

result.show()
```

**Ventajas**:
- ✅ Type hints (IDE autocomplete)
- ✅ Fácil testing con pytest
- ✅ Composición de transformaciones
- ✅ Mejor para pipelines de producción

**Ejecutar**:
```bash
spark-submit 3_pyspark.py --input-path ../../data/output
```

---

### 4️⃣ Scala Spark (Dataset API)

**Enfoque**: Type-safe, máximo performance.

**Archivo**: `4_scala.scala`

```scala
import org.apache.spark.sql.{SparkSession, functions => F}

val spark = SparkSession.builder()
  .appName("Case 01")
  .config("spark.sql.adaptive.enabled", "true")
  .getOrCreate()

import spark.implicits._

// Leer datos
val factSales = spark.read.parquet("../../data/output/fact_sales")
val dimRegion = spark.read.parquet("../../data/output/dim_region")

// Query con type-safety
val result = factSales
  .filter($"sale_date" >= "2025-01-01")
  .join(F.broadcast(dimRegion), Seq("region_id"))
  .groupBy("region_name")
  .agg(F.sum("amount").as("total"))
  .orderBy(F.desc("total"))

result.show()
```

**Ventajas**:
- ✅ Type-safe en compile time
- ✅ Mejor performance (sin overhead Python)
- ✅ Acceso completo a API Spark
- ✅ Dataset API con case classes

**Compilar y ejecutar**:
```bash
scalac -classpath "$(spark-submit --version 2>&1 | grep 'Spark home' | cut -d' ' -f3)/jars/*" 4_scala.scala
spark-submit --class Case01HintsParallel 4_scala.jar
```

---

## 🚀 Ejecutar el Caso Completo

### Prerequisitos

1. **Generar datos de prueba**:
```bash
cd ../../data/generators
python generate_all.py --size small --output ../output
```

2. **Verificar datos**:
```bash
ls -lh ../../data/output/
```

### Opción 1: Ejecutar todos los enfoques

```bash
# Desde casos/01-hints-parallel/

# Spark SQL
spark-sql -f 2_sparksql.sql

# PySpark
spark-submit 3_pyspark.py --approach both

# Scala (después de compilar)
spark-submit --class com.migration.cases.Case01HintsParallel \
  target/scala-2.12/case01.jar
```

### Opción 2: Notebook interactivo

Ver `../../notebooks/01-hints-parallel.ipynb` para versión interactiva con todos los enfoques.

---

## 📊 Comparativa de Performance

### Configuraciones Equivalentes

| Oracle Hint | Spark Equivalent | Notas |
|-------------|------------------|-------|
| `/*+ PARALLEL(8) */` | `spark.sql.shuffle.partitions=200` | Spark auto-paralleliza por particiones |
| `/*+ FULL(t) */` | Predicate pushdown automático | Parquet columnar + partition pruning |
| `/*+ USE_HASH(d) */` | `broadcast(dim)` si dim < 10MB | O shuffle hash join automático |
| `/*+ INDEX(t idx) */` | Partitioning + bucketing | Ver caso 04 |

### Ejemplo de Plan Físico

```bash
spark-submit 3_pyspark.py 2>&1 | grep -A 20 "Physical Plan"
```

**Spark plan esperado**:
```
== Physical Plan ==
AdaptiveSparkPlan
+- BroadcastHashJoin [region_id]
   :- Filter (sale_date >= 2025-01-01)
   :  +- FileScan parquet [sale_date, amount, region_id]
   :     Pushed filters: [sale_date >= 2025-01-01]
   +- BroadcastExchange
      +- FileScan parquet [region_id, region_name]
```

**Observa**:
- ✅ `BroadcastHashJoin` - equivalente a `USE_HASH` con dim pequeña
- ✅ `Pushed filters` - equivalente a Smart Scan de Exadata
- ✅ `FileScan parquet` - lectura columnar eficiente

---

## ✅ Validación

### 1. Conteo de Filas

```python
# Oracle
SELECT COUNT(*), SUM(total) FROM (
  SELECT d.region, SUM(f.amount) total
  FROM fact_sales f
  JOIN dim_region d ON d.region_id = f.region_id
  WHERE f.sale_date >= DATE '2025-01-01'
  GROUP BY d.region
);

# Spark (cualquier enfoque)
result.agg(count("*"), sum("total")).show()
```

### 2. Checksums por Región

```python
# Ver template: ../../templates/reconciliation_full_outer_join.sql
oracle_result = spark.read.csv("oracle_export.csv", header=True)
spark_result = result

# Comparar
diff = oracle_result.exceptAll(spark_result)
if diff.count() == 0:
    print("✅ Resultados idénticos")
else:
    print(f"⚠️ Diferencias: {diff.count()}")
    diff.show()
```

### 3. Validación de Performance

```bash
# Establecer baseline Oracle
# Tiempo: 45s, Rows: 10

# Ejecutar en Spark
time spark-submit 3_pyspark.py
# Tiempo esperado: 30-40s (con datos en cache)
```

---

## 💡 Lecciones Clave

### ✅ DO's

1. **Elimina hints Oracle**: Spark AQE es más inteligente
2. **Usa `broadcast()` solo para dims < 10MB**: Evita OOM
3. **Filtra antes de join**: Reduce shuffle
4. **Habilita AQE**: `spark.sql.adaptive.enabled=true`
5. **Particiona datos correctamente**: Por fecha/región

### ❌ DON'Ts

1. ❌ No traduzcas hints literalmente (`PARALLEL` → configuraciones)
2. ❌ No uses `broadcast()` en tablas grandes (OOM)
3. ❌ No ignores el plan físico (`explain()`)
4. ❌ No asumas que más partitions = más rápido
5. ❌ No uses `SELECT *` en fact tables grandes

---

## 🎓 Para Aprender Más

### Conceptos Relacionados

- **Caso 02**: Smart Scan / Predicate Pushdown
- **Caso 03**: Partition Pruning (evitar funciones en partition col)
- **Caso 05**: Star Joins / Bloom Filters

### Documentación

- [PySpark Best Practices](../../docs/pyspark-best-practices.md)
- [Scala Spark Patterns](../../docs/scala-spark-patterns.md)
- [SQL vs DataFrame API](../../docs/sql-vs-dataframe-api.md)
- [Spark Performance Tuning](../../docs/spark-performance-tuning.md)

### Tutoriales

- [Databricks: Broadcast Joins](https://docs.databricks.com/optimizations/semi-structured.html)
- [Spark SQL Guide](https://spark.apache.org/docs/latest/sql-performance-tuning.html)

---

## 📁 Archivos del Caso

```
cases/01-hints-parallel/
├── README.md           # Este archivo
├── 1_oracle.sql        # Query original Oracle con hints
├── 2_sparksql.sql      # Spark SQL equivalente
├── 3_pyspark.py        # Implementación PySpark (production-ready)
├── 4_scala.scala       # Implementación Scala (type-safe)
└── output/             # Resultados de ejecución
    ├── result_sql/
    ├── result_dataframe/
    └── result_typesafe/
```

---

## 🤝 Contribuir

¿Encontraste una mejor forma de hacer esto? ¡Abre un PR!

Ver [CONTRIBUTING.md](../../CONTRIBUTING.md) para guías.
