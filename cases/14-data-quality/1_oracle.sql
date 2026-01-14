-- Oracle: Validación de Datos Tradicional
-- Limitado - requiere escribir todas las reglas manualmente

-- Validar calidad durante INSERT
INSERT INTO customers_clean
SELECT 
    customer_id,
    name,
    email,
    phone,
    age,
    CASE 
        WHEN email IS NULL OR email NOT LIKE '%@%' THEN 'INVALID_EMAIL'
        WHEN age < 0 OR age > 120 THEN 'INVALID_AGE'
        WHEN phone IS NULL THEN 'INVALID_PHONE'
        ELSE 'VALID'
    END as quality_status
FROM customers_staging
WHERE 
    email IS NOT NULL 
    AND email LIKE '%@%'
    AND age BETWEEN 0 AND 120
    AND phone IS NOT NULL;

-- Quarantine registros inválidos
INSERT INTO customers_quarantine
SELECT 
    customer_id,
    name,
    email,
    phone,
    age,
    SYSDATE as quarantined_at,
    CASE 
        WHEN email IS NULL OR email NOT LIKE '%@%' THEN 'INVALID_EMAIL'
        WHEN age < 0 OR age > 120 THEN 'INVALID_AGE'
        WHEN phone IS NULL THEN 'INVALID_PHONE'
    END as reason
FROM customers_staging
WHERE 
    email IS NULL 
    OR email NOT LIKE '%@%'
    OR age NOT BETWEEN 0 AND 120
    OR phone IS NULL;

-- Ver estadísticas
SELECT 
    quality_status,
    COUNT(*) as record_count
FROM customers_clean
GROUP BY quality_status;
