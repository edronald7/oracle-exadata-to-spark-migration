# Caso 20: Integraciones del Ecosistema

**Criticidad**: ⭐⭐⭐⭐ (Alta)  
**Frecuencia**: Setup inicial + expansiones  

Spark no vive solo. Se integra con todo un ecosistema.

---

## 🔗 Stack Típico de Data Engineering (Cloud)

```
Data Sources        Orchestration       Processing          Storage             BI/ML
    |                    |                  |                  |                 |
Oracle DB  ────────► Airflow  ─────────► Spark  ─────────► Delta Lake ────► Tableau
MySQL      ────────► Prefect             PySpark            Parquet       ────► Power BI
Kafka      ────────► Step Fn             Scala              Iceberg       ────► Looker
S3 Files            Databricks                              Redshift      ────► SageMaker
APIs                Workflows                               Snowflake          MLflow
```

---

## 📊 Integraciones Críticas

### 1. Bases de Datos (JDBC)

```python
# Leer de Oracle
oracle_df = spark.read \\
    .format('jdbc') \\
    .option('url', 'jdbc:oracle:thin:@//host:1521/service') \\
    .option('dbtable', 'customers') \\
    .option('user', 'username') \\
    .option('password', 'password') \\
    .option('driver', 'oracle.jdbc.OracleDriver') \\
    .option('fetchsize', '10000') \\
    .option('numPartitions', '10') \\
    .option('partitionColumn', 'customer_id') \\
    .option('lowerBound', '1') \\
    .option('upperBound', '1000000') \\
    .load()

# Escribir a PostgreSQL
df.write \\
    .format('jdbc') \\
    .option('url', 'jdbc:postgresql://host:5432/db') \\
    .option('dbtable', 'customers_mirror') \\
    .option('user', 'user') \\
    .option('password', 'pass') \\
    .mode('overwrite') \\
    .save()
```

**Best Practice**: Pushdown predicates

```python
# ✅ GOOD: Filtro se ejecuta en Oracle
df = spark.read.jdbc(..., dbtable='customers') \\
    .filter('created_date >= '2026-01-01'')
# Oracle ejecuta: SELECT * FROM customers WHERE created_date >= ...

# ❌ BAD: Lee TODO, luego filtra en Spark
df = spark.read.jdbc(..., dbtable='customers')
all_data = df.collect()  # Trae millones de registros
filtered = [r for r in all_data if r.created_date >= ...]
```

---

### 2. Kafka (Streaming)

```python
# Leer de Kafka
kafka_df = spark.readStream \\
    .format('kafka') \\
    .option('kafka.bootstrap.servers', 'broker1:9092,broker2:9092') \\
    .option('subscribe', 'customer_events') \\
    .option('startingOffsets', 'earliest') \\
    .option('maxOffsetsPerTrigger', '100000') \\
    .load()

# Parse JSON
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StringType, IntegerType

schema = StructType() \\
    .add('customer_id', IntegerType()) \\
    .add('event_type', StringType()) \\
    .add('timestamp', StringType())

parsed = kafka_df.select(
    from_json(col('value').cast('string'), schema).alias('data')
).select('data.*')

# Escribir a Kafka
parsed.selectExpr('to_json(struct(*)) AS value') \\
    .writeStream \\
    .format('kafka') \\
    .option('kafka.bootstrap.servers', 'broker:9092') \\
    .option('topic', 'processed_events') \\
    .option('checkpointLocation', '/checkpoints/kafka') \\
    .start()
```

---

### 3. Object Storage (S3, ADLS, GCS)

```python
# AWS S3
spark.conf.set('spark.hadoop.fs.s3a.access.key', 'ACCESS_KEY')
spark.conf.set('spark.hadoop.fs.s3a.secret.key', 'SECRET_KEY')
df = spark.read.parquet('s3a://bucket/path')

# Azure ADLS Gen2
spark.conf.set('fs.azure.account.key.<account>.dfs.core.windows.net', 'KEY')
df = spark.read.parquet('abfss://container@account.dfs.core.windows.net/path')

# GCS
spark.conf.set('google.cloud.auth.service.account.json.keyfile', '/path/to/key.json')
df = spark.read.parquet('gs://bucket/path')
```

---

### 4. Data Warehouses (Redshift, Snowflake, BigQuery)

#### Redshift

```python
df.write \\
    .format('io.github.spark_redshift_community.spark.redshift') \\
    .option('url', 'jdbc:redshift://cluster:5439/db') \\
    .option('dbtable', 'customers') \\
    .option('tempdir', 's3://bucket/temp/') \\
    .option('aws_iam_role', 'arn:aws:iam::123:role/RedshiftRole') \\
    .mode('overwrite') \\
    .save()
```

#### Snowflake

```python
df.write \\
    .format('snowflake') \\
    .options(**{
        'sfURL': 'account.snowflakecomputing.com',
        'sfUser': 'user',
        'sfPassword': 'pass',
        'sfDatabase': 'DB',
        'sfSchema': 'SCHEMA',
        'sfWarehouse': 'WAREHOUSE'
    }) \\
    .option('dbtable', 'customers') \\
    .mode('overwrite') \\
    .save()
```

#### BigQuery

```python
df.write \\
    .format('bigquery') \\
    .option('table', 'project.dataset.customers') \\
    .option('temporaryGcsBucket', 'temp-bucket') \\
    .mode('overwrite') \\
    .save()
```

---

### 5. BI Tools (Tableau, Power BI)

**Opción A**: Direct Query (Lento en Spark)

```
❌ Tableau → Spark Thrift Server → Query cada vez
```

**Opción B**: Export a DWH (Recomendado)

```
✅ Spark → Delta Lake → Export to Redshift/Snowflake → Tableau
```

**Opción C**: Spark SQL con Thrift Server

```bash
# Start Thrift Server
$SPARK_HOME/sbin/start-thriftserver.sh \\
  --master spark://master:7077 \\
  --conf spark.sql.warehouse.dir=/data/warehouse

# Connect desde Tableau/Power BI
# Host: spark-master
# Port: 10000
# Type: Apache Spark SQL
```

---

### 6. ML Frameworks (MLflow, SageMaker)

```python
import mlflow
import mlflow.spark

# Train model
from pyspark.ml.classification import LogisticRegression
lr = LogisticRegression()
model = lr.fit(train_df)

# Log to MLflow
with mlflow.start_run():
    mlflow.log_param('maxIter', 10)
    mlflow.log_metric('accuracy', 0.95)
    mlflow.spark.log_model(model, 'model')

# Deploy
model_uri = 'runs:/<run_id>/model'
loaded_model = mlflow.spark.load_model(model_uri)
predictions = loaded_model.transform(test_df)
```

---

### 7. Monitoring (Datadog, Prometheus)

```python
# Custom metrics
from pyspark import SparkContext
sc = SparkContext.getOrCreate()

# Contador de registros procesados
sc.accumulator(0, 'records_processed')

# Enviar a Datadog/Prometheus
import requests
metrics = {
    'metric': 'spark.records.processed',
    'points': [(timestamp, count)],
    'tags': ['env:prod', 'job:etl']
}
requests.post(datadog_url, json=metrics)
```

---

## 📦 Connectors Populares

| Sistema | Connector | Docs |
|---------|-----------|------|
| Oracle | JDBC + ojdbc8.jar | [Link](https://www.oracle.com/database/technologies/appdev/jdbc-downloads.html) |
| MySQL | JDBC + mysql-connector | [Link](https://dev.mysql.com/downloads/connector/j/) |
| PostgreSQL | JDBC + postgresql.jar | [Link](https://jdbc.postgresql.org/) |
| Kafka | spark-sql-kafka | [Link](https://spark.apache.org/docs/latest/structured-streaming-kafka-integration.html) |
| Redshift | spark-redshift | [Link](https://github.com/spark-redshift-community/spark-redshift) |
| Snowflake | spark-snowflake | [Link](https://docs.snowflake.com/en/user-guide/spark-connector.html) |
| BigQuery | spark-bigquery | [Link](https://github.com/GoogleCloudDataproc/spark-bigquery-connector) |
| Elasticsearch | elasticsearch-spark | [Link](https://www.elastic.co/guide/en/elasticsearch/hadoop/current/index.html) |
| MongoDB | mongo-spark | [Link](https://www.mongodb.com/docs/spark-connector/current/) |

---

## 💡 Best Practices

1. **Use Managed Connectors**: Databricks/EMR pre-instalan muchos
2. **Partition JDBC Reads**: `numPartitions`, `partitionColumn`
3. **Credential Management**: AWS Secrets Manager, Azure Key Vault
4. **Network**: VPC peering, private endpoints
5. **Monitoring**: Track connector performance

---

## 📚 Recursos

- [Spark Data Sources](https://spark.apache.org/docs/latest/sql-data-sources.html)
- [Databricks Connectors](https://docs.databricks.com/data/data-sources/index.html)
