# PySpark Best Practices

Guía de mejores prácticas para desarrollar pipelines eficientes en PySpark.

---

## 📌 Cuándo usar PySpark vs Spark SQL

| Criterio | PySpark DataFrame API | Spark SQL |
|----------|----------------------|-----------|
| **Audiencia** | Data Engineers, programadores | Analistas, DBAs |
| **Ventajas** | Type hints, IDE autocomplete, composición programática | Familiar para usuarios SQL, fácil de leer |
| **Testing** | Fácil con pytest | Requiere framework adicional |
| **Debugging** | Stack traces claros | Errores en runtime |
| **Performance** | Equivalente (ambos usan Catalyst) | Equivalente |
| **Casos de uso** | Pipelines complejos, ETL, lógica condicional | Queries ad-hoc, reports, análisis exploratorio |

### Recomendación
- **Prototipos y análisis**: Spark SQL
- **Producción y pipelines**: PySpark DataFrame API
- **Híbrido**: Usar ambos según convenga

---

## 🚀 Optimizaciones Fundamentales

### 1. Broadcast Joins

**Anti-pattern**:
```python
# Join sin optimización con dimensión pequeña
result = large_fact.join(small_dim, "id")
```

**Best practice**:
```python
from pyspark.sql.functions import broadcast

# Broadcast para dimensiones <10MB
result = large_fact.join(broadcast(small_dim), "id")
```

**Cuándo usar**:
- Tabla derecha < 10MB
- Join con dimensiones
- Evita shuffle costoso

### 2. Partition Pruning

**Anti-pattern**:
```python
# Función sobre columna partición rompe pruning
df.filter(F.year(F.col("event_date")) == 2025)
```

**Best practice**:
```python
# Filtro directo sobre columna partición
df.filter((F.col("event_date") >= "2025-01-01") & 
          (F.col("event_date") < "2026-01-01"))
```

### 3. Column Pruning

**Anti-pattern**:
```python
# SELECT * innecesario
df = spark.read.parquet("s3://bucket/large_table")
result = df.filter(F.col("status") == "ACTIVE")
```

**Best practice**:
```python
# Seleccionar solo columnas necesarias
df = spark.read.parquet("s3://bucket/large_table") \
    .select("id", "name", "status", "amount")
result = df.filter(F.col("status") == "ACTIVE")
```

### 4. Caching Estratégico

**Anti-pattern**:
```python
# Cache indiscriminado
df.cache()
df.count()  # materializa
# ... nunca se usa de nuevo
```

**Best practice**:
```python
# Cache solo datasets reutilizados
df_filtered = df.filter(F.col("date") == "2025-01-01")
df_filtered.cache()

# Primera acción materializa
result1 = df_filtered.groupBy("region").count()

# Segunda acción usa cache
result2 = df_filtered.groupBy("product").sum("amount")

# Limpiar cache al terminar
df_filtered.unpersist()
```

### 5. Repartitionamiento Inteligente

**Anti-pattern**:
```python
# Demasiadas particiones pequeñas
df = spark.read.parquet("s3://bucket/data")  # 10,000 particiones
df.write.parquet("output")  # 10,000 archivos pequeños
```

**Best practice**:
```python
# Consolidar particiones antes de escribir
df = spark.read.parquet("s3://bucket/data")
df.coalesce(200).write.parquet("output")

# O repartition si necesitas distribución uniforme
df.repartition(200, "customer_id").write.parquet("output")
```

---

## 🏗️ Estructura de Código

### Pattern: Builder para Transformaciones

```python
from pyspark.sql import DataFrame
from pyspark.sql.functions import col, sum as _sum, when

class SalesTransformer:
    """Transformaciones reutilizables para fact_sales"""
    
    @staticmethod
    def filter_by_date_range(df: DataFrame, start: str, end: str) -> DataFrame:
        """Filtra por rango de fechas"""
        return df.filter(
            (col("sale_date") >= start) & (col("sale_date") < end)
        )
    
    @staticmethod
    def add_computed_columns(df: DataFrame) -> DataFrame:
        """Agrega columnas calculadas"""
        return df.withColumn(
            "revenue_tier",
            when(col("amount") > 1000, "high")
            .when(col("amount") > 100, "medium")
            .otherwise("low")
        )
    
    @staticmethod
    def aggregate_by_region(df: DataFrame) -> DataFrame:
        """Agrega por región"""
        return df.groupBy("region_id") \
            .agg(
                _sum("amount").alias("total_amount"),
                count("*").alias("transaction_count")
            )

# Uso
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("Sales Pipeline").getOrCreate()
sales_df = spark.read.parquet("s3://bucket/fact_sales")

result = (sales_df
    .transform(SalesTransformer.filter_by_date_range, "2025-01-01", "2025-12-31")
    .transform(SalesTransformer.add_computed_columns)
    .transform(SalesTransformer.aggregate_by_region)
)

result.show()
```

### Pattern: Validación de Esquemas

```python
from pyspark.sql.types import StructType, StructField, IntegerType, StringType, DecimalType, DateType

def validate_fact_sales_schema(df: DataFrame) -> None:
    """Valida que el DataFrame tenga el esquema esperado"""
    expected_schema = StructType([
        StructField("sale_id", IntegerType(), False),
        StructField("sale_date", DateType(), False),
        StructField("amount", DecimalType(10, 2), False),
        StructField("region_id", IntegerType(), True),
        StructField("status", StringType(), True)
    ])
    
    if df.schema != expected_schema:
        raise ValueError(f"Schema mismatch!\nExpected: {expected_schema}\nGot: {df.schema}")

# Uso
df = spark.read.parquet("input/")
validate_fact_sales_schema(df)
```

---

## 🐛 Debugging y Logging

### 1. Explain Plans

```python
# Ver plan físico
df.explain(mode="formatted")

# Diferentes modos
df.explain(mode="simple")    # Plan lógico
df.explain(mode="extended")  # Lógico + físico + stats
df.explain(mode="cost")      # Con estimates de costo
df.explain(mode="codegen")   # Código Java generado
```

### 2. Logging Estructurado

```python
import logging
from datetime import datetime

# Configurar logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def process_sales_data(date: str):
    """Pipeline con logging"""
    logger.info(f"Iniciando procesamiento para fecha: {date}")
    
    try:
        # Leer datos
        logger.info("Leyendo datos fuente...")
        df = spark.read.parquet(f"s3://bucket/sales/date={date}")
        row_count = df.count()
        logger.info(f"Leídas {row_count:,} filas")
        
        # Transformar
        logger.info("Aplicando transformaciones...")
        result = df.transform(SalesTransformer.filter_by_date_range, date, date)
        
        # Escribir
        logger.info("Escribiendo resultado...")
        result.write.mode("overwrite").parquet(f"output/processed_sales/date={date}")
        
        logger.info(f"✅ Procesamiento completado para {date}")
        
    except Exception as e:
        logger.error(f"❌ Error procesando {date}: {str(e)}", exc_info=True)
        raise
```

### 3. Data Quality Checks

```python
from pyspark.sql.functions import col, count, sum as _sum, isnan, when

def data_quality_report(df: DataFrame, name: str) -> None:
    """Genera reporte de calidad de datos"""
    print(f"\n{'='*60}")
    print(f"Data Quality Report: {name}")
    print(f"{'='*60}\n")
    
    # Row count
    total_rows = df.count()
    print(f"Total rows: {total_rows:,}")
    
    # Null counts por columna
    print("\nNull counts:")
    null_counts = df.select([
        count(when(col(c).isNull(), c)).alias(c)
        for c in df.columns
    ])
    null_counts.show()
    
    # Duplicados
    distinct_count = df.distinct().count()
    duplicates = total_rows - distinct_count
    print(f"\nDuplicate rows: {duplicates:,}")
    
    # Estadísticas numéricas
    print("\nNumeric statistics:")
    df.describe().show()

# Uso
df = spark.read.parquet("input/")
data_quality_report(df, "fact_sales")
```

---

## 🧪 Testing con pytest

### Estructura de tests

```python
# tests/test_transformers.py
import pytest
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, IntegerType, DecimalType, DateType
from datetime import date

@pytest.fixture(scope="session")
def spark():
    """Spark session para testing"""
    return SparkSession.builder \
        .master("local[2]") \
        .appName("pytest-pyspark") \
        .config("spark.sql.shuffle.partitions", "2") \
        .getOrCreate()

@pytest.fixture
def sample_sales_df(spark):
    """DataFrame de prueba"""
    schema = StructType([
        StructField("sale_id", IntegerType(), False),
        StructField("sale_date", DateType(), False),
        StructField("amount", DecimalType(10, 2), False),
        StructField("region_id", IntegerType(), False)
    ])
    
    data = [
        (1, date(2025, 1, 15), 100.50, 1),
        (2, date(2025, 1, 16), 250.00, 2),
        (3, date(2025, 2, 10), 75.25, 1),
    ]
    
    return spark.createDataFrame(data, schema)

def test_filter_by_date_range(spark, sample_sales_df):
    """Test filtrado por fecha"""
    result = SalesTransformer.filter_by_date_range(
        sample_sales_df, "2025-01-01", "2025-02-01"
    )
    
    assert result.count() == 2
    assert result.filter("sale_date >= '2025-02-01'").count() == 0

def test_aggregate_by_region(spark, sample_sales_df):
    """Test agregación"""
    result = SalesTransformer.aggregate_by_region(sample_sales_df)
    
    assert result.count() == 2  # 2 regiones
    
    region_1 = result.filter("region_id = 1").first()
    assert region_1["total_amount"] == 175.75
    assert region_1["transaction_count"] == 2
```

### Ejecutar tests

```bash
# Instalar dependencias
pip install pytest pyspark

# Ejecutar todos los tests
pytest tests/

# Con coverage
pytest --cov=src tests/

# Tests específicos
pytest tests/test_transformers.py::test_filter_by_date_range -v
```

---

## 📊 Monitoreo y Performance

### 1. Acceder a Spark UI Programáticamente

```python
def print_spark_ui_url():
    """Imprime URL del Spark UI"""
    sc = spark.sparkContext
    print(f"\n🌐 Spark UI: {sc.uiWebUrl}")
    print(f"📊 Application ID: {sc.applicationId}")
    print(f"👤 Spark User: {sc.sparkUser()}")

print_spark_ui_url()
```

### 2. Métricas de Ejecución

```python
from time import time

def log_execution_metrics(func):
    """Decorator para medir tiempo y métricas"""
    def wrapper(*args, **kwargs):
        start_time = time()
        start_row_count = spark.sparkContext.statusTracker().getExecutorInfos()
        
        result = func(*args, **kwargs)
        
        end_time = time()
        duration = end_time - start_time
        
        print(f"\n⏱️  Execution time: {duration:.2f}s")
        print(f"📊 Stages completed: {len(spark.sparkContext.statusTracker().getJobIdsForGroup())}")
        
        return result
    return wrapper

@log_execution_metrics
def process_pipeline():
    df = spark.read.parquet("input/")
    result = df.groupBy("region").count()
    result.write.parquet("output/")
    return result
```

---

## ✅ Checklist de Review

Antes de merge, verifica:

- [ ] ¿Usas `broadcast()` para dimensiones pequeñas?
- [ ] ¿Evitas UDFs cuando hay funciones built-in equivalentes?
- [ ] ¿Filtros sobre columnas partición no usan funciones?
- [ ] ¿Seleccionas solo columnas necesarias (column pruning)?
- [ ] ¿Cache solo datasets reutilizados múltiples veces?
- [ ] ¿Coalesce/repartition antes de escribir?
- [ ] ¿Esquemas explícitos en reads?
- [ ] ¿Tests unitarios para transformaciones críticas?
- [ ] ¿Logging en operaciones de producción?
- [ ] ¿Explain plan revisado para queries complejas?

---

## 📚 Recursos Adicionales

- [PySpark API Docs](https://spark.apache.org/docs/latest/api/python/)
- [Spark SQL Guide](https://spark.apache.org/docs/latest/sql-programming-guide.html)
- [PySpark Testing Best Practices](https://github.com/MrPowers/chispa)
- [Databricks PySpark Guide](https://docs.databricks.com/spark/latest/spark-sql/index.html)
