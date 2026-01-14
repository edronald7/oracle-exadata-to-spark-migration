-- Spark SQL: CDC con Delta Lake MERGE

-- 1. Crear tabla target (si no existe)
CREATE TABLE IF NOT EXISTS customers_delta (
    customer_id INT,
    name STRING,
    email STRING,
    phone STRING,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
) USING DELTA
LOCATION 's3://bucket/delta/customers';

-- 2. Leer datos CDC de staging
CREATE OR REPLACE TEMP VIEW cdc_staging AS
SELECT *
FROM parquet.`s3://bucket/cdc/customers/date=2026-01-12`;

-- 3. Deduplicar registros CDC (quedarse con el más reciente)
CREATE OR REPLACE TEMP VIEW cdc_deduped AS
SELECT 
    customer_id,
    name,
    email,
    phone,
    op_type,
    op_ts,
    ROW_NUMBER() OVER (
        PARTITION BY customer_id 
        ORDER BY op_ts DESC
    ) as rn
FROM cdc_staging
QUALIFY rn = 1;

-- 4. Merge a tabla Delta
MERGE INTO customers_delta AS target
USING cdc_deduped AS source
ON target.customer_id = source.customer_id

-- UPDATE cuando hay match y es update
WHEN MATCHED AND source.op_type = 'U' THEN
  UPDATE SET
    name = source.name,
    email = source.email,
    phone = source.phone,
    updated_at = source.op_ts

-- DELETE cuando hay match y es delete
WHEN MATCHED AND source.op_type = 'D' THEN
  DELETE

-- INSERT cuando no hay match y es insert o update
WHEN NOT MATCHED AND source.op_type IN ('I', 'U') THEN
  INSERT (customer_id, name, email, phone, created_at, updated_at)
  VALUES (source.customer_id, source.name, source.email, source.phone, 
          source.op_ts, source.op_ts);

-- 5. Verificar resultado
SELECT 
    COUNT(*) as total_customers,
    MAX(updated_at) as last_update,
    COUNT(DISTINCT DATE(updated_at)) as days_with_updates
FROM customers_delta;

-- 6. Optimizar tabla (compaction + Z-ORDER)
OPTIMIZE customers_delta ZORDER BY (customer_id);

-- 7. Limpiar versiones antiguas (después de 7 días)
VACUUM customers_delta RETAIN 168 HOURS;
