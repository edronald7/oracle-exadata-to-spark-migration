# SQL vs DataFrame API: Guía de Decisión

Comparativa práctica entre Spark SQL y DataFrame API (PySpark/Scala) para ayudarte a elegir el enfoque correcto.

---

## 🎯 Resumen Ejecutivo

| Criterio | Spark SQL | DataFrame API (PySpark/Scala) |
|----------|-----------|-------------------------------|
| **Curva de aprendizaje** | ⭐⭐⭐⭐⭐ Mínima (si sabes SQL) | ⭐⭐⭐ Moderada |
| **Flexibilidad** | ⭐⭐⭐ Limitada a SQL | ⭐⭐⭐⭐⭐ Programación completa |
| **Testing** | ⭐⭐ Complicado | ⭐⭐⭐⭐⭐ Fácil (pytest, ScalaTest) |
| **Refactoring** | ⭐⭐ Difícil (strings) | ⭐⭐⭐⭐⭐ Fácil (IDE support) |
| **Performance** | ⭐⭐⭐⭐⭐ Equivalente | ⭐⭐⭐⭐⭐ Equivalente |
| **Debugging** | ⭐⭐⭐ Errores en runtime | ⭐⭐⭐⭐ Stack traces claros |

### Recomendación Rápida

```
Análisis exploratorio       → Spark SQL
Queries simples             → Spark SQL  
Pipelines de producción     → DataFrame API
Lógica compleja/condicional → DataFrame API
ETL con transformaciones    → DataFrame API
```

---

## 📊 Ejemplos Lado a Lado

### Ejemplo 1: Filtro Simple

**Spark SQL**:
```sql
SELECT customer_id, amount
FROM sales
WHERE sale_date >= '2025-01-01'
  AND status = 'ACTIVE'
```

**PySpark**:
```python
from pyspark.sql.functions import col

df = spark.table("sales") \
    .select("customer_id", "amount") \
    .filter(
        (col("sale_date") >= "2025-01-01") &
        (col("status") == "ACTIVE")
    )
```

**Scala**:
```scala
import spark.implicits._

val df = spark.table("sales")
  .select($"customer_id", $"amount")
  .filter($"sale_date" >= "2025-01-01" && $"status" === "ACTIVE")
```

**Análisis**: 
- SQL es más conciso y familiar
- DataFrame API requiere imports y sintaxis específica
- **Ganador**: SQL para este caso simple

---

### Ejemplo 2: Agregación con Join

**Spark SQL**:
```sql
SELECT 
  r.region_name,
  COUNT(*) as transaction_count,
  SUM(s.amount) as total_amount,
  AVG(s.amount) as avg_amount
FROM sales s
JOIN regions r ON s.region_id = r.region_id
WHERE s.sale_date >= '2025-01-01'
GROUP BY r.region_name
HAVING SUM(s.amount) > 10000
ORDER BY total_amount DESC
```

**PySpark**:
```python
from pyspark.sql import functions as F

result = spark.table("sales") \
    .filter(F.col("sale_date") >= "2025-01-01") \
    .join(spark.table("regions"), "region_id") \
    .groupBy("region_name") \
    .agg(
        F.count("*").alias("transaction_count"),
        F.sum("amount").alias("total_amount"),
        F.avg("amount").alias("avg_amount")
    ) \
    .filter(F.col("total_amount") > 10000) \
    .orderBy(F.desc("total_amount"))
```

**Scala**:
```scala
import org.apache.spark.sql.functions._

val result = spark.table("sales")
  .filter($"sale_date" >= "2025-01-01")
  .join(spark.table("regions"), Seq("region_id"))
  .groupBy("region_name")
  .agg(
    count("*").as("transaction_count"),
    sum("amount").as("total_amount"),
    avg("amount").as("avg_amount")
  )
  .filter($"total_amount" > 10000)
  .orderBy(desc("total_amount"))
```

**Análisis**: 
- SQL sigue siendo más legible
- DataFrame API permite composición incremental
- **Ganador**: SQL para legibilidad, DataFrame para reusabilidad

---

### Ejemplo 3: Lógica Condicional Compleja

**Spark SQL**:
```sql
SELECT
  customer_id,
  amount,
  CASE 
    WHEN amount > 1000 AND loyalty_years > 5 THEN 'PLATINUM'
    WHEN amount > 500 AND loyalty_years > 3 THEN 'GOLD'
    WHEN amount > 100 OR loyalty_years > 1 THEN 'SILVER'
    ELSE 'BRONZE'
  END as tier,
  CASE
    WHEN tier = 'PLATINUM' THEN amount * 0.20
    WHEN tier = 'GOLD' THEN amount * 0.15
    WHEN tier = 'SILVER' THEN amount * 0.10
    ELSE amount * 0.05
  END as discount_amount
FROM sales
```

**PySpark** (mejor approach):
```python
from pyspark.sql.functions import when, col

def calculate_tier(df):
    """Calcula tier basado en lógica de negocio"""
    return df.withColumn("tier",
        when((col("amount") > 1000) & (col("loyalty_years") > 5), "PLATINUM")
        .when((col("amount") > 500) & (col("loyalty_years") > 3), "GOLD")
        .when((col("amount") > 100) | (col("loyalty_years") > 1), "SILVER")
        .otherwise("BRONZE")
    )

def calculate_discount(df):
    """Calcula descuento basado en tier"""
    discount_rates = {"PLATINUM": 0.20, "GOLD": 0.15, "SILVER": 0.10, "BRONZE": 0.05}
    
    discount_expr = when(col("tier") == "PLATINUM", col("amount") * 0.20)
    for tier, rate in list(discount_rates.items())[1:]:
        discount_expr = discount_expr.when(col("tier") == tier, col("amount") * rate)
    
    return df.withColumn("discount_amount", discount_expr.otherwise(col("amount") * 0.05))

# Uso: composición de transformaciones
result = (spark.table("sales")
    .transform(calculate_tier)
    .transform(calculate_discount)
)
```

**Scala**:
```scala
import org.apache.spark.sql.functions._
import org.apache.spark.sql.DataFrame

def calculateTier(df: DataFrame): DataFrame = {
  df.withColumn("tier",
    when($"amount" > 1000 && $"loyalty_years" > 5, "PLATINUM")
    .when($"amount" > 500 && $"loyalty_years" > 3, "GOLD")
    .when($"amount" > 100 || $"loyalty_years" > 1, "SILVER")
    .otherwise("BRONZE")
  )
}

def calculateDiscount(df: DataFrame): DataFrame = {
  df.withColumn("discount_amount",
    when($"tier" === "PLATINUM", $"amount" * 0.20)
    .when($"tier" === "GOLD", $"amount" * 0.15)
    .when($"tier" === "SILVER", $"amount" * 0.10)
    .otherwise($"amount" * 0.05)
  )
}

// Uso
val result = spark.table("sales")
  .transform(calculateTier)
  .transform(calculateDiscount)
```

**Análisis**: 
- SQL funciona pero es monolítico y difícil de testear
- DataFrame API permite modularizar lógica en funciones reutilizables
- Más fácil de testear y mantener
- **Ganador**: DataFrame API

---

### Ejemplo 4: Window Functions

**Spark SQL**:
```sql
SELECT
  customer_id,
  sale_date,
  amount,
  SUM(amount) OVER (
    PARTITION BY customer_id 
    ORDER BY sale_date
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
  ) as running_total,
  ROW_NUMBER() OVER (
    PARTITION BY customer_id 
    ORDER BY amount DESC
  ) as amount_rank
FROM sales
```

**PySpark**:
```python
from pyspark.sql import Window
from pyspark.sql.functions import sum as _sum, row_number

window_running = Window.partitionBy("customer_id") \
    .orderBy("sale_date") \
    .rowsBetween(Window.unboundedPreceding, Window.currentRow)

window_rank = Window.partitionBy("customer_id") \
    .orderBy(col("amount").desc())

result = spark.table("sales") \
    .withColumn("running_total", _sum("amount").over(window_running)) \
    .withColumn("amount_rank", row_number().over(window_rank))
```

**Scala**:
```scala
import org.apache.spark.sql.expressions.Window
import org.apache.spark.sql.functions._

val windowRunning = Window
  .partitionBy("customer_id")
  .orderBy("sale_date")
  .rowsBetween(Window.unboundedPreceding, Window.currentRow)

val windowRank = Window
  .partitionBy("customer_id")
  .orderBy($"amount".desc)

val result = spark.table("sales")
  .withColumn("running_total", sum("amount").over(windowRunning))
  .withColumn("amount_rank", row_number().over(windowRank))
```

**Análisis**: 
- SQL es más conciso para window functions
- DataFrame API permite reutilizar definiciones de windows
- **Empate**: depende del caso de uso

---

## 🔄 Interoperabilidad: Usar Ambos

La mejor estrategia es **usar ambos según convenga**.

### Pattern: SQL para queries complejas, DataFrame para transformaciones

```python
# Leer con SQL (conveniente)
df = spark.sql("""
    SELECT 
      s.customer_id,
      s.amount,
      r.region_name,
      p.product_category
    FROM sales s
    JOIN regions r ON s.region_id = r.region_id
    JOIN products p ON s.product_id = p.product_id
    WHERE s.sale_date >= '2025-01-01'
""")

# Transformar con DataFrame API (modular)
def add_business_logic(df):
    return df.withColumn("tier",
        when(col("amount") > 1000, "HIGH")
        .when(col("amount") > 100, "MEDIUM")
        .otherwise("LOW")
    )

result = df.transform(add_business_logic)

# Volver a registrar como temp view para usar en SQL
result.createOrReplaceTempView("enriched_sales")

# Agregar con SQL (familiar para analistas)
final = spark.sql("""
    SELECT region_name, tier, COUNT(*), SUM(amount)
    FROM enriched_sales
    GROUP BY region_name, tier
""")
```

### Pattern: Funciones UDF compartidas

```python
from pyspark.sql.functions import udf
from pyspark.sql.types import StringType

# Definir UDF
@udf(returnType=StringType())
def categorize_amount(amount):
    if amount > 1000:
        return "HIGH"
    elif amount > 100:
        return "MEDIUM"
    else:
        return "LOW"

# Registrar para SQL
spark.udf.register("categorize_amount", categorize_amount)

# Usar en SQL
spark.sql("""
    SELECT customer_id, categorize_amount(amount) as category
    FROM sales
""")

# Usar en DataFrame API
df = spark.table("sales") \
    .withColumn("category", categorize_amount(col("amount")))
```

---

## ✅ Matriz de Decisión

### Usa **Spark SQL** cuando:

✅ **Análisis exploratorio** / ad-hoc queries  
✅ **Analistas sin experiencia en programación**  
✅ **Migrando queries Oracle existentes**  
✅ **Query simple** (select, filter, join, group by)  
✅ **Reportes con sintaxis SQL familiar**  
✅ **Prototipado rápido**  
✅ **Notebooks interactivos**  

### Usa **DataFrame API** cuando:

✅ **Pipelines de producción**  
✅ **Lógica condicional compleja**  
✅ **Testing unitario requerido**  
✅ **Refactoring frecuente**  
✅ **Composición de transformaciones modulares**  
✅ **Integración con código Python/Scala**  
✅ **Type safety (Scala Datasets)**  
✅ **CI/CD pipelines**  

---

## 🧪 Testing: Ventaja del DataFrame API

### Testing SQL (complicado)

```python
def test_sales_query():
    # Difícil: query como string
    query = """
        SELECT region, SUM(amount)
        FROM sales
        WHERE date >= '2025-01-01'
        GROUP BY region
    """
    result = spark.sql(query)
    
    # Si cambias el esquema de sales, test rompe en runtime
    assert result.count() > 0
```

### Testing DataFrame API (fácil)

```python
import pytest
from pyspark.sql import SparkSession

@pytest.fixture
def spark():
    return SparkSession.builder.master("local[2]").getOrCreate()

@pytest.fixture
def sample_sales(spark):
    data = [
        ("region1", "2025-01-15", 100.0),
        ("region2", "2025-01-20", 200.0),
    ]
    return spark.createDataFrame(data, ["region", "date", "amount"])

def aggregate_by_region(df):
    """Función testeable"""
    return df.groupBy("region").agg({"amount": "sum"})

def test_aggregate_by_region(spark, sample_sales):
    # Test claro y específico
    result = aggregate_by_region(sample_sales)
    
    assert result.count() == 2
    
    region1_total = result.filter("region = 'region1'").first()["sum(amount)"]
    assert region1_total == 100.0
```

---

## 📊 Performance: Son Equivalentes

**Mito**: "DataFrame API es más rápido que SQL"  
**Realidad**: Ambos usan el mismo Catalyst Optimizer y generan el mismo plan físico.

### Prueba:

```python
# SQL
result_sql = spark.sql("""
    SELECT region, SUM(amount)
    FROM sales
    GROUP BY region
""")

# DataFrame API
result_df = spark.table("sales") \
    .groupBy("region") \
    .agg({"amount": "sum"})

# Mismo plan físico
result_sql.explain()
result_df.explain()
# Output idéntico
```

**Conclusión**: Elige basado en mantenibilidad, no en performance.

---

## 🎓 Estrategia de Adopción

### Para Equipos de Analistas
1. Comienza con 100% SQL
2. Introduce DataFrame API gradualmente para lógica compleja
3. Capacita en PySpark basics (filter, select, withColumn)
4. Mantén SQL para queries de reporte

### Para Equipos de Engineering
1. Usa DataFrame API como default
2. SQL solo para queries simples en notebooks
3. Todas las transformaciones en funciones testeables
4. CI/CD con pytest/ScalaTest

### Híbrido (Recomendado)
```
Exploración → SQL
Lógica → DataFrame API  
Reportes → SQL
Testing → DataFrame API
Producción → DataFrame API
```

---

## 📚 Cheat Sheet

| Operación | SQL | PySpark | Scala |
|-----------|-----|---------|-------|
| **Select** | `SELECT col1, col2` | `.select("col1", "col2")` | `.select($"col1", $"col2")` |
| **Filter** | `WHERE col > 10` | `.filter(col("col") > 10)` | `.filter($"col" > 10)` |
| **Join** | `FROM a JOIN b ON ...` | `.join(b, "key")` | `.join(b, Seq("key"))` |
| **Group By** | `GROUP BY col` | `.groupBy("col")` | `.groupBy("col")` |
| **Aggregate** | `SUM(amount)` | `.agg(sum("amount"))` | `.agg(sum("amount"))` |
| **Order** | `ORDER BY col DESC` | `.orderBy(desc("col"))` | `.orderBy($"col".desc)` |
| **Limit** | `LIMIT 10` | `.limit(10)` | `.limit(10)` |
| **Window** | `OVER (PARTITION BY ...)` | `.over(window_spec)` | `.over(windowSpec)` |

---

## 🎯 Conclusión

**No hay un "ganador" absoluto**. La mejor práctica es:

1. **Entender ambos enfoques**
2. **Elegir según el contexto**:
   - SQL para queries simples y análisis exploratorio
   - DataFrame API para pipelines de producción
3. **Combinar ambos** cuando tenga sentido
4. **Priorizar mantenibilidad** sobre preferencias personales

**Regla de oro**: Si vas a poner el código en producción y necesita tests → DataFrame API. Si es análisis exploratorio → SQL.
