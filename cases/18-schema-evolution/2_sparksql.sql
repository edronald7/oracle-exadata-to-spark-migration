-- Spark SQL: Schema Evolution con Delta Lake

-- Delta Lake hace schema evolution MÁS FÁCIL que Oracle
-- No bloquea reads/writes
-- Time travel built-in para rollback

-- =====================================================
-- Operación 1: ADD COLUMN
-- =====================================================

-- ✅ Automático con mergeSchema
-- En código: df.write.option("mergeSchema", "true").save(...)

-- O explícitamente en SQL (Databricks):
ALTER TABLE customers ADD COLUMN loyalty_points INT;

-- ✅ Instantáneo, no bloquea reads
-- Old data: loyalty_points = NULL
-- New data: incluye loyalty_points

-- =====================================================
-- Operación 2: RENAME COLUMN (Delta Lake 2.0+)
-- =====================================================

ALTER TABLE customers RENAME COLUMN name TO customer_name;

-- En versiones anteriores, workaround:
-- 1. ADD nueva columna
ALTER TABLE customers ADD COLUMN customer_name STRING;

-- 2. UPDATE con datos de columna vieja
UPDATE customers SET customer_name = name WHERE customer_name IS NULL;

-- 3. (Opcional) DROP columna vieja
ALTER TABLE customers DROP COLUMN name;

-- =====================================================
-- Operación 3: CHANGE DATA TYPE
-- =====================================================

-- ⚠️ Requiere rewrite de datos
ALTER TABLE customers ALTER COLUMN age TYPE INT;

-- Con validación previa:
SELECT COUNT(*) FROM customers WHERE TRY_CAST(age AS INT) IS NULL;
-- Si hay registros inválidos, manejarlos primero

-- =====================================================
-- Operación 4: DROP COLUMN
-- =====================================================

ALTER TABLE customers DROP COLUMN old_column;

-- ✅ Con Delta, esto solo actualiza metadata
-- Los datos físicos se limpian con VACUUM

-- =====================================================
-- Operación 5: REPLACE COLUMNS (reordenar/restructure)
-- =====================================================

ALTER TABLE customers REPLACE COLUMNS (
    customer_id INT,
    customer_name STRING,
    email STRING,
    loyalty_points INT
);

-- ⚠️ Cuidado: esto reemplaza TODO el schema

-- =====================================================
-- Schema Enforcement & Evolution
-- =====================================================

-- Ver schema actual
DESCRIBE customers;

-- Ver historia de schema changes
DESCRIBE HISTORY customers;

-- Ver schema de versión específica
DESCRIBE TABLE customers VERSION AS OF 10;

-- =====================================================
-- Time Travel para Rollback
-- =====================================================

-- Si un schema change fue malo, rollback:
RESTORE TABLE customers TO VERSION AS OF 15;
-- O por timestamp:
RESTORE TABLE customers TO TIMESTAMP AS OF '2026-01-11 10:00:00';

-- =====================================================
-- Optimizar después de schema changes
-- =====================================================

-- Reescribir datos con nuevo schema (mejora performance)
OPTIMIZE customers;

-- Limpiar versiones antiguas
VACUUM customers RETAIN 168 HOURS;

-- =====================================================
-- Configuraciones útiles
-- =====================================================

-- Permitir schema evolution por default (tabla)
ALTER TABLE customers SET TBLPROPERTIES (
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true'
);

-- Enforcement modes
SET spark.databricks.delta.schema.autoMerge.enabled = true;
-- Permite agregar columnas automáticamente

-- =====================================================
-- Comparación con Oracle
-- =====================================================

-- | Operación | Oracle | Delta Lake |
-- |-----------|--------|------------|
-- | ADD COLUMN | Lento, bloquea | Instant, no bloquea |
-- | RENAME COLUMN | Soportado 12c+ | Soportado 2.0+ |
-- | CHANGE TYPE | Rewrite completo | Rewrite completo |
-- | DROP COLUMN | Bloquea, lento | Instant (metadata) |
-- | ROLLBACK | Difícil (backup) | Easy (time travel) |

-- ✅ Delta Lake gana por mucho en flexibilidad
