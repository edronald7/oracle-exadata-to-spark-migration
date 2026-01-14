-- Oracle: Schema Evolution (DDL Operations)

-- Problema en Oracle: ALTER TABLE puede bloquear tabla por horas

-- =====================================================
-- Operación 1: ADD COLUMN
-- =====================================================

-- ❌ Forma tradicional (BLOQUEA tabla)
ALTER TABLE customers ADD (loyalty_points NUMBER DEFAULT 0);
-- Durante este tiempo: no reads, no writes en tabla de 100M records

-- ✅ Forma online (Oracle 12c+)
ALTER TABLE customers ADD (loyalty_points NUMBER DEFAULT 0) ONLINE;
-- Permite reads, pero aún puede ser lento

-- =====================================================
-- Operación 2: MODIFY COLUMN (cambiar tipo)
-- =====================================================

-- ⚠️ PELIGROSO: Cambiar tipo puede fallar si hay incompatibilidad
ALTER TABLE customers MODIFY (age NUMBER(3));
-- Falla si hay valores como 'ABC' que no son numéricos

-- Approach seguro:
-- 1. Agregar columna nueva
ALTER TABLE customers ADD (age_new NUMBER(3));

-- 2. Migrar datos con validación
UPDATE customers 
SET age_new = CASE 
    WHEN REGEXP_LIKE(age, '^[0-9]+$') THEN TO_NUMBER(age)
    ELSE NULL
END;

-- 3. Drop old, rename new
ALTER TABLE customers DROP COLUMN age;
ALTER TABLE customers RENAME COLUMN age_new TO age;

-- =====================================================
-- Operación 3: RENAME COLUMN
-- =====================================================

-- Oracle 11g no soporta RENAME COLUMN directo
-- Oracle 12c+:
ALTER TABLE customers RENAME COLUMN name TO customer_name;

-- =====================================================
-- Operación 4: DROP COLUMN
-- =====================================================

-- ❌ Inmediato (puede bloquear)
ALTER TABLE customers DROP COLUMN old_column;

-- ✅ Marcar como unused primero (más rápido)
ALTER TABLE customers SET UNUSED (old_column);
-- Luego drop en maintenance window
ALTER TABLE customers DROP UNUSED COLUMNS;

-- =====================================================
-- Operación 5: ADD CONSTRAINT
-- =====================================================

-- Agregar constraint sin bloquear
ALTER TABLE customers ADD CONSTRAINT chk_age CHECK (age >= 0) ENABLE NOVALIDATE;
-- NOVALIDATE: no valida datos existentes (más rápido)

-- Validar después en background
ALTER TABLE customers MODIFY CONSTRAINT chk_age VALIDATE;

-- =====================================================
-- Limitaciones Oracle
-- =====================================================

-- 1. DDL operations bloquean (locks)
-- 2. No hay "time travel" nativo para rollback
-- 3. Schema changes requieren maintenance windows
-- 4. No hay versioning de schemas
-- 5. Rollback de DDL es difícil (requiere backup/restore)
