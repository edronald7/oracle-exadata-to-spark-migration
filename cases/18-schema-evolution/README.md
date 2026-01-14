# Caso 18: Schema Evolution

**Criticidad**: ⭐⭐⭐⭐ (Alta)  
**Frecuencia**: Mensual - Los schemas cambian  

Tu tabla tiene 100M registros. El negocio pide agregar columna. ¿Y ahora?

---

## 🎯 El Problema

**Realidad**: En Oracle, hacer `ALTER TABLE ADD COLUMN` en tabla de 100M registros puede tomar horas y bloquear toda la tabla.

**En Data Lakes**: Es diferente, pero tiene sus propios challenges.

---

## 📊 Comparativa

### Oracle (DDL Locks)

```sql
-- ❌ BLOQUEA la tabla por horas
ALTER TABLE customers ADD (loyalty_points NUMBER DEFAULT 0);
-- Durante este tiempo: no reads, no writes

-- ✅ Online DDL (Oracle 12c+)
ALTER TABLE customers ADD (loyalty_points NUMBER DEFAULT 0) ONLINE;
-- Permite reads, pero aún costoso
```

---

## ⚡ Delta Lake (Schema Evolution)

### Add Column (Fácil)

```python
# Datos originales
original = spark.read.format('delta').load('/data/customers')
# Schema: (id, name, email)

# Agregar columna nueva
updated = original.withColumn('loyalty_points', lit(0))

# Escribir con mergeSchema
updated.write \\
    .format('delta') \\
    .mode('append') \\
    .option('mergeSchema', 'true') \\
    .save('/data/customers')

# ✅ Instantáneo, no bloquea reads
```

### Rename Column

```python
# Delta no soporta rename directo
# Workaround: Add new + drop old

# 1. Add con nuevo nombre
df = spark.read.format('delta').load('/data/customers')
df_new = df.withColumn('customer_name', col('name'))

df_new.write \\
    .format('delta') \\
    .mode('overwrite') \\
    .option('overwriteSchema', 'true') \\
    .save('/data/customers')

# 2. Drop old column (opcional)
# Delta soporta column mapping para evitar rewrites
```

### Change Data Type

```python
# ❌ RIESGOSO: De STRING a INT puede fallar
df = spark.read.format('delta').load('/data/customers')

# Validar primero
invalid = df.filter(~col('age').cast('int').isNotNull())
if invalid.count() > 0:
    print(f'⚠️ {invalid.count()} registros no convertibles')
    # Manejar casos especiales

# Cast + overwrite
df_casted = df.withColumn('age', col('age').cast('int'))
df_casted.write \\
    .format('delta') \\
    .mode('overwrite') \\
    .option('overwriteSchema', 'true') \\
    .save('/data/customers')
```

---

## 🔧 Production Patterns

### Pattern 1: Backward Compatible Changes

```python
# ✅ SAFE: Agregar columnas con defaults
df.withColumn('new_col', lit(None).cast('string'))

# Old code sigue funcionando (ignora nueva columna)
# New code puede usar nueva columna
```

### Pattern 2: Versioning con Branches

```python
# Delta Lake 2.0+: Table branches
from delta.tables import DeltaTable

# Crear branch para testing
DeltaTable.forPath(spark, '/data/customers') \\
    .createBranch('schema_v2')

# Escribir cambios a branch
df_new_schema.write \\
    .format('delta') \\
    .mode('overwrite') \\
    .option('branch', 'schema_v2') \\
    .save('/data/customers')

# Testear con branch
test_df = spark.read \\
    .format('delta') \\
    .option('branch', 'schema_v2') \\
    .load('/data/customers')

# Merge a main cuando listo
DeltaTable.forPath(spark, '/data/customers') \\
    .mergeBranch('schema_v2')
```

### Pattern 3: Schema Registry (Avro/Protobuf)

```python
# Usar schema registry (Confluent Schema Registry)
from confluent_kafka.schema_registry import SchemaRegistryClient

registry = SchemaRegistryClient({'url': 'http://schema-registry:8081'})

# Registrar schema v2
schema_v2 = {
    'type': 'record',
    'name': 'Customer',
    'fields': [
        {'name': 'id', 'type': 'int'},
        {'name': 'name', 'type': 'string'},
        {'name': 'email', 'type': 'string'},
        {'name': 'loyalty_points', 'type': ['null', 'int'], 'default': None}
    ]
}

registry.register_schema('customers-value', schema_v2)

# Produce/consume con schema validation
```

---

## ✅ Best Practices

### DO's
1. ✅ Agregar columnas con defaults (backward compatible)
2. ✅ Usar `mergeSchema=true` para adds
3. ✅ Validar antes de cambiar data types
4. ✅ Testear en branch/staging primero
5. ✅ Documentar cambios de schema

### DON'Ts
1. ❌ Renombrar columnas sin plan de migración
2. ❌ Cambiar data types sin validación
3. ❌ `overwriteSchema=true` en producción sin backup
4. ❌ Eliminar columnas en uso
5. ❌ No comunicar cambios de schema al equipo

---

## 🔍 Schema Enforcement

```python
# Delta Lake enforces schema
df_wrong_schema.write \\
    .format('delta') \\
    .mode('append') \\
    .save('/data/customers')
# ❌ ERROR: "A schema mismatch detected"

# Options:
# 1. mergeSchema=true (permite adds)
# 2. overwriteSchema=true (replace completo, PELIGROSO)
# 3. Fix upstream para match schema
```

---

## 📚 Recursos

- [Delta Lake Schema Evolution](https://docs.delta.io/latest/delta-update.html#automatic-schema-evolution)
- [Schema Registry](https://docs.confluent.io/platform/current/schema-registry/index.html)
