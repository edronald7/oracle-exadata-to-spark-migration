# Caso 19: Troubleshooting & Debugging

**Criticidad**: ⭐⭐⭐⭐⭐ (CRÍTICA)  
**Frecuencia**: DIARIA - Siempre hay issues  

Tu Spark job falló. Tienes 1 hora para arreglarlo. ¿Qué haces?

---

## 🚨 Errores Comunes y Soluciones

### 1. OutOfMemoryError

```
ERROR: java.lang.OutOfMemoryError: Java heap space
```

**Causas**:
- Skewed data (una partición muy grande)
- `collect()` en dataset grande
- Broadcast join de tabla grande
- Small number of partitions

**Soluciones**:

```python
# ❌ BAD
df.collect()  # Trae TODO a driver
big_table.join(broadcast(huge_dim), 'key')  # Broadcast muy grande

# ✅ GOOD
df.write.parquet('output')  # Escribe distribuido

# Más particiones
df.repartition(400)

# Más memoria
--conf spark.driver.memory=8g \\
--conf spark.executor.memory=16g

# Salting para skew
df.withColumn('salt', (rand() * 10).cast('int')) \\
  .repartition('key', 'salt')
```

---

### 2. Shuffle Errors

```
ERROR: FetchFailedException: Failed to fetch shuffle block
```

**Causas**:
- Network issues
- Executor crashes
- Shuffle data too large

**Soluciones**:

```python
# Configuraciones
--conf spark.shuffle.compress=true \\
--conf spark.shuffle.spill.compress=true \\
--conf spark.network.timeout=600s \\
--conf spark.shuffle.io.maxRetries=5 \\
--conf spark.shuffle.io.retryWait=30s

# Reducir shuffle size
df.coalesce(100)  # Menos partitions
```

---

### 3. Slow Query / Hung Job

**Debugging Steps**:

1. **Spark UI** (`http://driver:4040`):
   ```
   - Stages: ¿Cuál stage es lento?
   - Tasks: ¿Alguna task con 10x más tiempo?
   - SQL Tab: ¿Qué operación?
   ```

2. **Check for Skew**:
   ```python
   # Ver distribución de particiones
   df.rdd.glom().map(len).collect()
   # Output: [1000, 1050, 980, ..., 50000]  ← SKEWED!
   
   # Fix: Repartition o salting
   ```

3. **Explain Plan**:
   ```python
   df.explain(mode='formatted')
   # Buscar:
   # - BroadcastHashJoin vs SortMergeJoin
   # - Exchange (shuffle)
   # - FileScan (cuántos archivos?)
   ```

---

### 4. File Not Found / Path Issues

```
ERROR: Path does not exist: s3://bucket/data
```

**Debugging**:

```python
# Check si existe
from pyspark.sql.utils import AnalysisException
try:
    df = spark.read.parquet('s3://bucket/data')
except AnalysisException as e:
    print(f'Path doesn't exist: {e}')
    # Fallback o alerta

# Listar archivos
hadoop_conf = spark._jsc.hadoopConfiguration()
fs = spark._jvm.org.apache.hadoop.fs.FileSystem.get(hadoop_conf)
path = spark._jvm.org.apache.hadoop.fs.Path('s3://bucket/')
files = fs.listStatus(path)
for f in files:
    print(f.getPath())
```

---

### 5. Data Skew en Join

```
Stage 3: 199 tasks completed, 1 task running for 2 hours
```

**Identificar**:

```python
# Count por key
df1.groupBy('join_key').count().orderBy(col('count').desc()).show()
# Output:
# key=NULL: 10,000,000  ← PROBLEMA!
# key=123: 50,000
# key=456: 30,000
```

**Soluciones**:

```python
# 1. Filter nulls antes de join
df1_clean = df1.filter(col('join_key').isNotNull())
df2_clean = df2.filter(col('join_key').isNotNull())

# 2. Salting
from pyspark.sql.functions import rand, concat, lit

# Add salt a tabla grande
df1_salted = df1.withColumn(
    'salted_key',
    concat(col('join_key'), lit('_'), (rand() * 10).cast('int'))
)

# Replicate tabla pequeña
df2_exploded = df2.withColumn(
    'salt',
    explode(array([lit(i) for i in range(10)]))
).withColumn(
    'salted_key',
    concat(col('join_key'), lit('_'), col('salt'))
)

# Join on salted key
result = df1_salted.join(df2_exploded, 'salted_key')
```

---

## 🔍 Herramientas de Debugging

### 1. Spark UI

```bash
# Acceder a Spark UI
http://<driver-node>:4040

# Tabs clave:
# - Jobs: Ver progreso
# - Stages: Identificar stage lento
# - Storage: Cached data
# - SQL: Query plans
# - Executors: Recursos por executor
```

### 2. Logs

```bash
# Driver logs
yarn logs -applicationId <app_id> | grep ERROR

# Executor logs (EMR)
aws s3 cp s3://logs-bucket/<cluster-id>/containers/ . --recursive

# Buscar errores comunes
grep -i 'outofmemory\\|exception\\|failed' *.log
```

### 3. Explain Plans

```python
# Simple
df.explain()

# Detallado
df.explain(extended=True)

# Formatted (Spark 3.0+)
df.explain(mode='formatted')

# Cost-based
df.explain(mode='cost')
```

---

## 💡 Debugging Checklist

```
[ ] Check Spark UI - ¿Qué stage falla?
[ ] Check logs - ¿Qué dice el error?
[ ] Explain plan - ¿Shuffle innecesario?
[ ] Data skew? - Count por key
[ ] Memory suficiente? - Executor memory
[ ] Correct partitioning? - Num partitions
[ ] File count? - Many small files?
[ ] Broadcast join? - Table size
[ ] Schema issues? - mergeSchema
[ ] Permissions? - S3/IAM roles
```

---

## 📚 Recursos

- [Spark Monitoring](https://spark.apache.org/docs/latest/monitoring.html)
- [Performance Tuning Guide](https://spark.apache.org/docs/latest/sql-performance-tuning.html)
