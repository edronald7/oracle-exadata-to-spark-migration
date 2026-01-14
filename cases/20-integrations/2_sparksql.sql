-- Spark SQL: Integraciones del Ecosistema
-- Spark se integra con TODO: JDBC, Kafka, S3, warehouses, etc.

-- =====================================================
-- Integración 1: JDBC (Oracle, MySQL, PostgreSQL)
-- =====================================================

-- Leer de Oracle via JDBC
CREATE OR REPLACE TEMP VIEW oracle_customers
USING JDBC
OPTIONS (
    url 'jdbc:oracle:thin:@//oracle-host:1521/service',
    dbtable 'customers',
    user 'username',
    password 'password',
    driver 'oracle.jdbc.OracleDriver',
    fetchsize '10000',
    numPartitions '10',
    partitionColumn 'customer_id',
    lowerBound '1',
    upperBound '1000000'
);

-- Query como tabla normal
SELECT * FROM oracle_customers WHERE region_id = 10;

-- Join con tabla Spark
SELECT o.*, c.customer_name
FROM spark_orders o
JOIN oracle_customers c ON o.customer_id = c.customer_id;

-- Escribir a PostgreSQL
CREATE TABLE postgres_customers
USING JDBC
OPTIONS (
    url 'jdbc:postgresql://postgres-host:5432/db',
    dbtable 'customers_copy',
    user 'user',
    password 'pass'
)
AS SELECT * FROM spark_customers;

-- =====================================================
-- Integración 2: Object Storage (S3, ADLS, GCS)
-- =====================================================

-- AWS S3 (s3a://)
SELECT * FROM parquet.`s3a://bucket/customers/`;

-- Azure ADLS Gen2 (abfss://)
SELECT * FROM parquet.`abfss://container@account.dfs.core.windows.net/customers/`;

-- GCP GCS (gs://)
SELECT * FROM parquet.`gs://bucket/customers/`;

-- Escribir particionado
CREATE TABLE customers_partitioned
USING DELTA
PARTITIONED BY (region_id)
LOCATION 's3://bucket/delta/customers'
AS SELECT * FROM source_table;

-- =====================================================
-- Integración 3: Delta Lake
-- =====================================================

-- Crear tabla Delta
CREATE TABLE customers_delta
USING DELTA
LOCATION 's3://bucket/delta/customers'
AS SELECT * FROM source;

-- Time travel
SELECT * FROM customers_delta VERSION AS OF 10;
SELECT * FROM customers_delta TIMESTAMP AS OF '2026-01-11';

-- MERGE (upsert)
MERGE INTO customers_delta AS target
USING updates AS source
ON target.customer_id = source.customer_id
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *;

-- =====================================================
-- Integración 4: Redshift (via spark-redshift)
-- =====================================================

CREATE OR REPLACE TEMP VIEW redshift_customers
USING com.databricks.spark.redshift
OPTIONS (
    url 'jdbc:redshift://cluster.region.redshift.amazonaws.com:5439/db',
    dbtable 'customers',
    tempdir 's3://bucket/temp/',
    aws_iam_role 'arn:aws:iam::123456:role/RedshiftRole'
);

SELECT * FROM redshift_customers;

-- Escribir a Redshift
CREATE TABLE redshift_customers_new
USING com.databricks.spark.redshift
OPTIONS (
    url 'jdbc:redshift://cluster:5439/db',
    dbtable 'customers_new',
    tempdir 's3://bucket/temp/',
    aws_iam_role 'arn:aws:iam::123456:role/RedshiftRole'
)
AS SELECT * FROM spark_customers;

-- =====================================================
-- Integración 5: Snowflake
-- =====================================================

CREATE OR REPLACE TEMP VIEW snowflake_customers
USING snowflake
OPTIONS (
    sfURL 'account.snowflakecomputing.com',
    sfUser 'user',
    sfPassword 'pass',
    sfDatabase 'DB',
    sfSchema 'SCHEMA',
    sfWarehouse 'WAREHOUSE',
    dbtable 'CUSTOMERS'
);

SELECT * FROM snowflake_customers;

-- =====================================================
-- Integración 6: BigQuery (GCP)
-- =====================================================

CREATE OR REPLACE TEMP VIEW bigquery_customers
USING bigquery
OPTIONS (
    table 'project.dataset.customers',
    project 'my-gcp-project',
    parentProject 'my-gcp-project'
);

SELECT * FROM bigquery_customers;

-- =====================================================
-- Integración 7: Hive Metastore
-- =====================================================

-- Spark usa Hive Metastore por default
-- Tablas Hive son accesibles directamente

-- Listar databases
SHOW DATABASES;

-- Listar tablas
SHOW TABLES IN mydb;

-- Query tabla Hive
SELECT * FROM mydb.customers;

-- Crear tabla managed en Hive
CREATE TABLE mydb.customers (
    customer_id INT,
    name STRING
) USING PARQUET;

-- =====================================================
-- Integración 8: Iceberg (table format alternativo)
-- =====================================================

-- Crear tabla Iceberg
CREATE TABLE customers_iceberg (
    customer_id INT,
    name STRING,
    region_id INT
)
USING iceberg
PARTITIONED BY (region_id)
LOCATION 's3://bucket/iceberg/customers';

-- Time travel (como Delta)
SELECT * FROM customers_iceberg VERSION AS OF 1234567890;

-- =====================================================
-- Integración 9: Elasticsearch
-- =====================================================

CREATE OR REPLACE TEMP VIEW es_customers
USING org.elasticsearch.spark.sql
OPTIONS (
    es.nodes 'es-host',
    es.port '9200',
    es.resource 'customers/_doc',
    es.nodes.wan.only 'true'
);

SELECT * FROM es_customers WHERE name LIKE 'John%';

-- =====================================================
-- Integración 10: MongoDB
-- =====================================================

CREATE OR REPLACE TEMP VIEW mongo_customers
USING com.mongodb.spark.sql.DefaultSource
OPTIONS (
    uri 'mongodb://mongo-host:27017/db.customers'
);

SELECT * FROM mongo_customers;

-- =====================================================
-- Ventajas vs Oracle
-- =====================================================

-- ✅ Spark integra con TODO (cloud-native)
-- ✅ No requiere licenses adicionales (como GoldenGate)
-- ✅ Performance: Parallel reads via partitioning
-- ✅ Formato agnóstico: Parquet, Delta, Iceberg, JSON, Avro
-- ✅ Schema evolution built-in
-- ✅ Cost-effective en cloud

-- =====================================================
-- Best Practices
-- =====================================================

-- 1. SIEMPRE usar partitioning en JDBC reads:
--    numPartitions, partitionColumn, lowerBound, upperBound

-- 2. Usar tempdir para Redshift (staging en S3)

-- 3. Credentials vía Secrets Manager, no hardcoded

-- 4. Para writes grandes a DB, considera:
--    - Escribir a S3/ADLS primero
--    - Luego COPY INTO desde warehouse

-- 5. Monitor costos de data transfer between regions
