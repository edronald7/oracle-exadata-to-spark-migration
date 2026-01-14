# Caso 13: CDC e Ingesta Incremental

**Criticidad**: ⭐⭐⭐⭐⭐ (MÁXIMA)  
**Frecuencia**: DIARIA - Es el 50% del trabajo de un data engineer  
**Complejidad**: Alta

Aprende cómo implementar Change Data Capture (CDC) e ingesta incremental desde Oracle a Spark/Delta Lake.

---

## 🎯 Objetivo de Aprendizaje

Entender cómo manejar actualizaciones incrementales de datos:
- **Oracle**: Trigger-based CDC, GoldenGate, Flashback queries
- **Spark**: Incremental reads, Merge operations, Deduplicación
- **Delta Lake**: MERGE, Time travel, Vacuum

---

## 📊 Escenario Real

**Problema**: Tienes una tabla Oracle `customers` con 100M registros que se actualiza constantemente.

**Necesitas**:
1. Cargar solo los cambios (INSERT/UPDATE/DELETE)
2. Aplicar cambios a Delta Lake
3. Deduplicar registros
4. Mantener historial (SCD Type 2)
5. Ejecutar diariamente

---

## 🔷 Approach Oracle (Baseline)

### Opción 1: Full Load (Ineficiente)

```sql
-- ❌ MAL: Cargar todo diariamente
SELECT * FROM customers;
-- 100M registros x 365 días = costoso e innecesario
```

### Opción 2: Incremental con Timestamp

```sql
-- ✅ MEJOR: Solo cambios recientes
SELECT *
FROM customers
WHERE last_modified_date >= TO_DATE('2026-01-12', 'YYYY-MM-DD')
   OR created_date >= TO_DATE('2026-01-12', 'YYYY-MM-DD');

-- Problema: No captura DELETEs
```

### Opción 3: Oracle GoldenGate (CDC Real)

```sql
-- Oracle GoldenGate captura:
-- - INSERT operations
-- - UPDATE (before/after images)
-- - DELETE operations
-- - Metadata (SCN, timestamp, operation type)

-- Output formato Avro/JSON:
{
  "table": "customers",
  "op_type": "U",  -- U=Update, I=Insert, D=Delete
  "op_ts": "2026-01-12T10:30:00",
  "before": {"customer_id": 123, "name": "John"},
  "after": {"customer_id": 123, "name": "John Doe"}
}
```

---

## ⚡ Enfoque 1: Spark SQL (Incremental Load)

**Archivo**: `2_sparksql.sql`

```sql
-- 1. Leer cambios desde staging (exportados desde Oracle)
CREATE OR REPLACE TEMP VIEW cdc_staging AS
SELECT *
FROM parquet.`s3://bucket/cdc/customers/date=2026-01-12`;

-- 2. Merge a tabla target (Delta Lake)
MERGE INTO customers_delta AS target
USING cdc_staging AS source
ON target.customer_id = source.customer_id

-- UPDATE cuando coincide
WHEN MATCHED AND source.op_type = 'U' THEN
  UPDATE SET
    name = source.name,
    email = source.email,
    updated_at = source.op_ts

-- DELETE cuando coincide
WHEN MATCHED AND source.op_type = 'D' THEN
  DELETE

-- INSERT cuando no coincide
WHEN NOT MATCHED AND source.op_type IN ('I', 'U') THEN
  INSERT (customer_id, name, email, created_at, updated_at)
  VALUES (source.customer_id, source.name, source.email, source.op_ts, source.op_ts);

-- 3. Ver estadísticas del merge
SELECT 
  COUNT(*) as total_records,
  COUNT(DISTINCT customer_id) as distinct_customers,
  MAX(updated_at) as last_update
FROM customers_delta;
```

---

## 💻 Enfoque 2: PySpark (Production-Grade)

**Archivo**: `3_pyspark.py`

```python
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, max as _max, row_number, lit
from pyspark.sql.window import Window
from delta.tables import DeltaTable

def incremental_load_with_dedup(
    spark,
    source_path: str,
    target_path: str,
    business_keys: list,
    date_partition: str
):
    '''
    Carga incremental con deduplicación.
    
    Args:
        source_path: Ruta de datos CDC
        target_path: Ruta Delta Lake target
        business_keys: Columnas que identifican unicidad
        date_partition: Fecha de partición a procesar
    '''
    print(f'\\n📊 Procesando CDC para fecha: {date_partition}')
    
    # 1. Leer datos CDC del día
    cdc_df = spark.read.parquet(f'{source_path}/date={date_partition}')
    
    print(f'   CDC records: {cdc_df.count():,}')
    print(f'   Operations: {cdc_df.groupBy('op_type').count().show()}')
    
    # 2. Deduplicación: Si hay múltiples cambios del mismo registro,
    #    quedarnos con el más reciente
    window_spec = Window.partitionBy(*business_keys) \\
        .orderBy(col('op_ts').desc())
    
    deduplicated = cdc_df.withColumn(
        'rn', row_number().over(window_spec)
    ).filter(col('rn') == 1).drop('rn')
    
    print(f'   After dedup: {deduplicated.count():,}')
    
    # 3. Verificar si target existe
    if DeltaTable.isDeltaTable(spark, target_path):
        print('   Target exists: performing MERGE')
        
        # Tabla Delta existente
        target_table = DeltaTable.forPath(spark, target_path)
        
        # Preparar merge condition
        merge_condition = ' AND '.join([
            f'target.{key} = source.{key}' for key in business_keys
        ])
        
        # MERGE operation
        target_table.alias('target').merge(
            deduplicated.alias('source'),
            merge_condition
        ).whenMatchedUpdate(
            condition='source.op_type = 'U'',
            set={
                'name': 'source.name',
                'email': 'source.email',
                'phone': 'source.phone',
                'updated_at': 'source.op_ts'
            }
        ).whenMatchedDelete(
            condition='source.op_type = 'D''
        ).whenNotMatchedInsert(
            condition='source.op_type IN ('I', 'U')',
            values={
                'customer_id': 'source.customer_id',
                'name': 'source.name',
                'email': 'source.email',
                'phone': 'source.phone',
                'created_at': 'source.op_ts',
                'updated_at': 'source.op_ts'
            }
        ).execute()
        
        print('   ✅ MERGE completed')
        
    else:
        print('   Target doesn't exist: performing initial load')
        
        # Primera carga
        initial_load = deduplicated.filter(
            col('op_type').isin(['I', 'U'])
        ).select(
            'customer_id', 'name', 'email', 'phone',
            col('op_ts').alias('created_at'),
            col('op_ts').alias('updated_at')
        )
        
        initial_load.write \\
            .format('delta') \\
            .mode('overwrite') \\
            .save(target_path)
        
        print(f'   ✅ Initial load: {initial_load.count():,} records')
    
    # 4. Estadísticas finales
    final_df = spark.read.format('delta').load(target_path)
    print(f'\\n📊 Final stats:')
    print(f'   Total records: {final_df.count():,}')
    print(f'   Last update: {final_df.agg(_max('updated_at')).collect()[0][0]}')
    
    return final_df


def handle_late_arriving_data(
    spark,
    target_path: str,
    lookback_days: int = 7
):
    '''
    Maneja datos que llegan tarde (late-arriving data).
    
    Reprocess últimos N días por si hay datos que llegaron tarde.
    '''
    print(f'\\n🔄 Checking for late-arriving data ({lookback_days} days lookback)')
    
    target_table = DeltaTable.forPath(spark, target_path)
    
    # Usar Time Travel para comparar versiones
    current_version = spark.read.format('delta').load(target_path)
    
    # Leer versión de hace N días
    previous_version = spark.read \\
        .format('delta') \\
        .option('versionAsOf', '7') \\
        .load(target_path)
    
    # Comparar
    late_arrivals = current_version.exceptAll(previous_version)
    
    late_count = late_arrivals.count()
    if late_count > 0:
        print(f'   ⚠️  {late_count:,} late-arriving records detected')
        late_arrivals.show(10)
    else:
        print('   ✅ No late-arriving data')
    
    return late_arrivals


def main():
    spark = SparkSession.builder \\
        .appName('CDC Incremental Load') \\
        .config('spark.sql.extensions', 'io.delta.sql.DeltaSparkSessionExtension') \\
        .config('spark.sql.catalog.spark_catalog', 'org.apache.spark.sql.delta.catalog.DeltaCatalog') \\
        .getOrCreate()
    
    # Configuración
    source_path = 's3://bucket/cdc/customers'
    target_path = 's3://bucket/delta/customers'
    date_partition = '2026-01-12'
    
    # Ejecutar carga incremental
    final_df = incremental_load_with_dedup(
        spark,
        source_path,
        target_path,
        business_keys=['customer_id'],
        date_partition=date_partition
    )
    
    # Check late arrivals
    handle_late_arriving_data(spark, target_path, lookback_days=7)
    
    # Validación
    print('\\n✅ CDC pipeline completed')
    
    spark.stop()


if __name__ == '__main__':
    main()
```

---

## 🔧 Enfoque 3: Scala (Type-Safe)

**Archivo**: `4_scala.scala`

```scala
package com.migration.cases

import org.apache.spark.sql.{DataFrame, SparkSession}
import org.apache.spark.sql.functions._
import io.delta.tables.DeltaTable

case class CDCRecord(
  customer_id: Int,
  name: String,
  email: String,
  phone: String,
  op_type: String,  // I, U, D
  op_ts: java.sql.Timestamp
)

object Case13CDCIncremental {
  
  def incrementalLoadWithDedup(
    spark: SparkSession,
    sourcePath: String,
    targetPath: String,
    businessKeys: Seq[String],
    datePartition: String
  ): DataFrame = {
    
    println(s'\\n📊 Processing CDC for date: $datePartition')
    
    import spark.implicits._
    
    // 1. Read CDC data
    val cdcDF = spark.read
      .parquet(s'$sourcePath/date=$datePartition')
    
    println(s'   CDC records: ${cdcDF.count()}')
    
    // 2. Deduplication
    val windowSpec = Window
      .partitionBy(businessKeys.map(col): _*)
      .orderBy(col('op_ts').desc)
    
    val deduplicated = cdcDF
      .withColumn('rn', row_number().over(windowSpec))
      .filter($'rn' === 1)
      .drop('rn')
    
    println(s'   After dedup: ${deduplicated.count()}')
    
    // 3. Merge or initial load
    if (DeltaTable.isDeltaTable(spark, targetPath)) {
      println('   Performing MERGE')
      
      val targetTable = DeltaTable.forPath(spark, targetPath)
      val mergeCondition = businessKeys
        .map(key => s'target.$key = source.$key')
        .mkString(' AND ')
      
      targetTable.as('target')
        .merge(
          deduplicated.as('source'),
          mergeCondition
        )
        .whenMatched('source.op_type = 'U'')
        .updateExpr(Map(
          'name' -> 'source.name',
          'email' -> 'source.email',
          'phone' -> 'source.phone',
          'updated_at' -> 'source.op_ts'
        ))
        .whenMatched('source.op_type = 'D'')
        .delete()
        .whenNotMatched('source.op_type IN ('I', 'U')')
        .insertExpr(Map(
          'customer_id' -> 'source.customer_id',
          'name' -> 'source.name',
          'email' -> 'source.email',
          'phone' -> 'source.phone',
          'created_at' -> 'source.op_ts',
          'updated_at' -> 'source.op_ts'
        ))
        .execute()
      
      println('   ✅ MERGE completed')
      
    } else {
      println('   Performing initial load')
      
      val initialLoad = deduplicated
        .filter($'op_type'.isin('I', 'U'))
        .select(
          $'customer_id',
          $'name',
          $'email',
          $'phone',
          $'op_ts'.as('created_at'),
          $'op_ts'.as('updated_at')
        )
      
      initialLoad.write
        .format('delta')
        .mode('overwrite')
        .save(targetPath)
      
      println(s'   ✅ Initial load: ${initialLoad.count()} records')
    }
    
    // 4. Return final state
    spark.read.format('delta').load(targetPath)
  }
  
  def main(args: Array[String]): Unit = {
    val spark = SparkSession.builder()
      .appName('CDC Incremental Load')
      .config('spark.sql.extensions', 'io.delta.sql.DeltaSparkSessionExtension')
      .config('spark.sql.catalog.spark_catalog', 'org.apache.spark.sql.delta.catalog.DeltaCatalog')
      .getOrCreate()
    
    val sourcePath = 's3://bucket/cdc/customers'
    val targetPath = 's3://bucket/delta/customers'
    val datePartition = '2026-01-12'
    
    val result = incrementalLoadWithDedup(
      spark,
      sourcePath,
      targetPath,
      Seq('customer_id'),
      datePartition
    )
    
    println('\\n✅ CDC pipeline completed')
    println(s'   Total records: ${result.count()}')
    
    spark.stop()
  }
}
```

---

## ✅ Validación y Testing

### 1. Generar Datos CDC de Prueba

```python
# Script para generar CDC sintético
from pyspark.sql import SparkSession
from pyspark.sql.functions import expr, lit
from datetime import datetime, timedelta

spark = SparkSession.builder.appName('Generate CDC').getOrCreate()

# Día 1: Initial load (1000 customers)
initial = spark.range(1, 1001).selectExpr(
    'id as customer_id',
    'concat('Customer ', id) as name',
    'concat('customer', id, '@example.com') as email',
    'concat('+1-555-', lpad(id, 4, '0')) as phone',
    ''I' as op_type',
    'timestamp('2026-01-10 00:00:00') as op_ts'
)

initial.write.partitionBy('op_ts').parquet('testdata/cdc/customers')

# Día 2: Updates (100 customers)
updates = spark.range(1, 101).selectExpr(
    'id as customer_id',
    'concat('Updated Customer ', id) as name',
    'concat('customer', id, '_updated@example.com') as email',
    'concat('+1-555-', lpad(id, 4, '0')) as phone',
    ''U' as op_type',
    'timestamp('2026-01-11 12:00:00') as op_ts'
)

# Día 2: Deletes (10 customers)
deletes = spark.range(991, 1001).selectExpr(
    'id as customer_id',
    'null as name',
    'null as email',
    'null as phone',
    ''D' as op_type',
    'timestamp('2026-01-11 18:00:00') as op_ts'
)

updates.union(deletes).write \\
    .partitionBy('op_ts') \\
    .mode('append') \\
    .parquet('testdata/cdc/customers')
```

### 2. Validar Resultados

```python
# Verificar estado final
final = spark.read.format('delta').load('testdata/delta/customers')

print(f'Total customers: {final.count()}')  # Esperado: 990 (1000 - 10 deletes)

print('Updated customers:')
final.filter('name LIKE 'Updated%'').show(5)  # 100 updated

print('Deleted customers:')
deleted_ids = list(range(991, 1001))
assert final.filter(col('customer_id').isin(deleted_ids)).count() == 0
print('✅ Deletes validated')
```

---

## 📊 Performance Considerations

### Optimizaciones Clave

1. **Partition Pruning**:
   ```python
   # Leer solo particiones necesarias
   cdc_df = spark.read \\
       .parquet('cdc/customers') \\
       .filter(f'date >= '{start_date}' AND date <= '{end_date}'')
   ```

2. **Z-Ordering** (Delta Lake):
   ```sql
   OPTIMIZE customers_delta ZORDER BY (customer_id, updated_at);
   ```

3. **Compaction**:
   ```sql
   -- Consolidar archivos pequeños
   OPTIMIZE customers_delta;
   
   -- Limpiar versiones antiguas
   VACUUM customers_delta RETAIN 168 HOURS;
   ```

4. **Checkpointing** (Streaming):
   ```python
   query = df.writeStream \\
       .format('delta') \\
       .option('checkpointLocation', '/checkpoints/customers') \\
       .start('/delta/customers')
   ```

---

## 💡 Lecciones Clave

### ✅ Best Practices

1. **Siempre deduplicar**: Múltiples cambios del mismo registro en CDC
2. **Manejar DELETEs**: No solo INSERT/UPDATE
3. **Idempotencia**: Pipeline debe ser re-ejecutable
4. **Watermarking**: Para streaming, define límites de late data
5. **Monitoreo**: Alertas si volumen de CDC es anormal

### ❌ Anti-Patterns

1. ❌ Full load diario (costoso e innecesario)
2. ❌ No validar duplicados (genera inconsistencias)
3. ❌ Ignorar DELETEs (data drift)
4. ❌ No usar MERGE (overwrites pierden historia)
5. ❌ No manejar late-arriving data

---

## 🔗 Ver También

- **Caso 10**: MERGE / SCD - Patrones de upsert
- **Caso 15**: Streaming - CDC en tiempo real
- **Caso 14**: Data Quality - Validar CDC data
- **Caso 18**: Schema Evolution - Manejar cambios de schema

---

## 📚 Recursos

- [Delta Lake MERGE](https://docs.delta.io/latest/delta-update.html#upsert-into-a-table-using-merge)
- [CDC Patterns](https://www.databricks.com/blog/2021/06/09/how-to-simplify-cdc-with-delta-lakes-change-data-feed.html)
- [Change Data Feed](https://docs.databricks.com/delta/delta-change-data-feed.html)

---

**Próximo**: Caso 14 - Data Quality & Error Handling
