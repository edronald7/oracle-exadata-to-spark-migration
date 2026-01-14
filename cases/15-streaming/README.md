# Caso 15: Spark Structured Streaming

**Criticidad**: ⭐⭐⭐⭐⭐ (CRÍTICA en arquitecturas modernas)  
**Frecuencia**: Setup inicial, luego 24/7  
**Complejidad**: Alta

De batch a near real-time: Kafka → Spark Streaming → Delta Lake

---

## 🎯 Objetivo

**Evolución**:
- **Oracle**: Batch queries cada hora/día
- **Spark Batch**: Micro-batches cada 15 min
- **Spark Streaming**: Near real-time (<1 min latency)

**Casos de uso**:
- CDC en tiempo real
- Event processing
- Real-time analytics
- Alerting systems

---

## 📊 Arquitectura

```
Oracle GoldenGate → Kafka → Spark Streaming → Delta Lake
                                    ↓
                              Aggregations
                                    ↓
                           Real-time Dashboard
```

---

## ⚡ Spark SQL (Structured Streaming)

```sql
-- 1. Leer stream desde Kafka
CREATE OR REPLACE TEMP VIEW kafka_stream AS
SELECT 
    CAST(key AS STRING) as key,
    CAST(value AS STRING) as value,
    topic,
    partition,
    offset,
    timestamp
FROM kafka.`kafka-server:9092`.`customer_events`;

-- 2. Parse JSON
CREATE OR REPLACE TEMP VIEW parsed_stream AS
SELECT 
    get_json_object(value, '$.customer_id') as customer_id,
    get_json_object(value, '$.event_type') as event_type,
    get_json_object(value, '$.amount') as amount,
    timestamp
FROM kafka_stream;

-- 3. Aggregations en ventanas de tiempo
CREATE OR REPLACE TEMP VIEW windowed_aggregates AS
SELECT 
    window(timestamp, '5 minutes') as time_window,
    customer_id,
    COUNT(*) as event_count,
    SUM(CAST(amount AS DECIMAL)) as total_amount
FROM parsed_stream
GROUP BY window(timestamp, '5 minutes'), customer_id;

-- 4. Escribir a Delta (streaming)
-- Nota: Usar DataFrame API para writeStream
```

---

## 💻 PySpark (Production Streaming)

```python
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, window, sum as _sum, count
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DecimalType, TimestampType

spark = SparkSession.builder \\
    .appName('Streaming CDC') \\
    .config('spark.sql.streaming.checkpointLocation', '/checkpoints') \\
    .getOrCreate()

# 1. Define schema
schema = StructType([
    StructField('customer_id', IntegerType()),
    StructField('event_type', StringType()),
    StructField('amount', DecimalType(10, 2)),
    StructField('timestamp', TimestampType())
])

# 2. Leer de Kafka
kafka_df = spark.readStream \\
    .format('kafka') \\
    .option('kafka.bootstrap.servers', 'kafka:9092') \\
    .option('subscribe', 'customer_events') \\
    .option('startingOffsets', 'earliest') \\
    .load()

# 3. Parse JSON
parsed_df = kafka_df.select(
    from_json(col('value').cast('string'), schema).alias('data')
).select('data.*')

# 4. Watermarking (late data)
watermarked = parsed_df.withWatermark('timestamp', '10 minutes')

# 5. Aggregations
aggregated = watermarked.groupBy(
    window(col('timestamp'), '5 minutes'),
    col('customer_id')
).agg(
    count('*').alias('event_count'),
    _sum('amount').alias('total_amount')
)

# 6. Escribir a Delta
query = aggregated.writeStream \\
    .format('delta') \\
    .outputMode('append') \\
    .option('checkpointLocation', '/checkpoints/customers') \\
    .start('/delta/customer_aggregates')

query.awaitTermination()
```

---

## 💡 Conceptos Clave

### Watermarking
```python
# Permite manejar late-arriving data
df.withWatermark('timestamp', '10 minutes')
# Procesa eventos hasta 10 min tarde
```

### Checkpointing
```python
# Fault tolerance - guarda progreso
.option('checkpointLocation', '/checkpoints/job1')
```

### Output Modes
- **Append**: Solo nuevos registros
- **Complete**: Todo el resultado
- **Update**: Solo registros actualizados

---

## 📚 Recursos

- [Structured Streaming Guide](https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html)
- [Delta Lake Streaming](https://docs.delta.io/latest/delta-streaming.html)
