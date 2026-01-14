-- Spark SQL: Data Quality con badRecordsPath

-- 1. Leer con manejo de registros corruptos
CREATE OR REPLACE TEMP VIEW raw_data AS
SELECT *, _corrupt_record
FROM json.`s3://bucket/input/customers.json`
OPTIONS (
    mode = 'PERMISSIVE',
    columnNameOfCorruptRecord = '_corrupt_record',
    badRecordsPath = '/quarantine/bad_records'
);

-- 2. Separar registros buenos
CREATE OR REPLACE TEMP VIEW good_records AS
SELECT 
    customer_id,
    name,
    email,
    phone,
    age
FROM raw_data 
WHERE _corrupt_record IS NULL;

-- 3. Aplicar validaciones de negocio
CREATE OR REPLACE TEMP VIEW validated_records AS
SELECT 
    *,
    CASE 
        WHEN customer_id IS NULL THEN 'NULL_ID'
        WHEN email IS NULL OR email NOT LIKE '%@%' THEN 'INVALID_EMAIL'
        WHEN age < 0 OR age > 120 THEN 'INVALID_AGE'
        WHEN phone IS NULL OR LENGTH(phone) < 10 THEN 'INVALID_PHONE'
        ELSE 'VALID'
    END as quality_status
FROM good_records;

-- 4. Insertar registros válidos a tabla limpia
INSERT INTO customers_clean
SELECT 
    customer_id,
    name,
    email,
    phone,
    age,
    current_timestamp() as processed_at
FROM validated_records 
WHERE quality_status = 'VALID';

-- 5. Quarantine registros inválidos
INSERT INTO quarantine_table
SELECT 
    *,
    current_timestamp() as quarantined_at
FROM validated_records 
WHERE quality_status != 'VALID';

-- 6. Reporte de calidad
SELECT 
    quality_status,
    COUNT(*) as record_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM validated_records
GROUP BY quality_status
ORDER BY record_count DESC;

-- 7. Registros corruptos
SELECT 
    COUNT(*) as corrupt_records
FROM raw_data 
WHERE _corrupt_record IS NOT NULL;
