-- Oracle: Ingesta Incremental Tradicional
-- Limitación: No captura DELETEs eficientemente

-- Opción 1: Basado en timestamp (común pero problemático)
SELECT 
    customer_id,
    name,
    email,
    phone,
    created_date,
    last_modified_date
FROM customers
WHERE last_modified_date >= TO_DATE('2026-01-12', 'YYYY-MM-DD')
   OR created_date >= TO_DATE('2026-01-12', 'YYYY-MM-DD');

-- Problema: No detecta registros eliminados

-- Opción 2: Oracle Flashback Query (requiere privilegios)
SELECT 
    customer_id,
    name,
    email,
    phone,
    ORA_ROWSCN as scn_number
FROM customers
WHERE ORA_ROWSCN > :last_processed_scn;

-- Opción 3: Change Data Capture con triggers (overhead)
-- CREATE TRIGGER customers_audit_trigger
-- AFTER INSERT OR UPDATE OR DELETE ON customers
-- FOR EACH ROW
-- BEGIN
--   INSERT INTO customers_audit_log (...)
-- END;

-- Consulta de log
SELECT op_type, customer_id, old_values, new_values, change_timestamp
FROM customers_audit_log
WHERE change_timestamp >= SYSDATE - 1;
