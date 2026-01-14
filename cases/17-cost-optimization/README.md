# Caso 17: Cost Optimization

**Criticidad**: ⭐⭐⭐⭐⭐ (CRÍTICA en cloud)  
**Frecuencia**: Análisis semanal  

En cloud, el costo es preocupación #1. Optimiza o quiebras el presupuesto.

---

## 📊 Dónde se va el dinero

1. **Shuffle** (40%): Datos moviéndose entre nodos
2. **Spill to disk** (20%): Out of memory
3. **Small files** (15%): Miles de archivos pequeños
4. **Compute idle** (15%): Clusters sin usar
5. **Storage** (10%): Datos duplicados/sin comprimir

---

## 💰 Optimizaciones Críticas

### 1. Evitar Shuffle Innecesario

```python
# ❌ BAD: Shuffle costoso (500GB)
df1 = large_fact.repartition(200)
df2 = df1.join(large_dim, 'key')  # Shuffle join
# Cost: $50/día

# ✅ GOOD: Broadcast join (0 shuffle)
df2 = large_fact.join(broadcast(small_dim), 'key')
# Cost: $5/día
```

### 2. Compaction (Small Files)

```sql
-- ❌ BAD: 10,000 archivos de 1MB cada uno
-- Read performance: SLOW
-- Cost: Alto (muchos API calls)

-- ✅ GOOD: 100 archivos de 100MB cada uno
OPTIMIZE customers_delta;
-- Consolida archivos

-- Resultado: 10x más rápido, 50% menos costo
```

### 3. Partition Pruning

```python
# ❌ BAD: Escanea todo (1TB)
df = spark.read.parquet('s3://bucket/sales')
result = df.filter('date = '2026-01-12'')
# Cost: $10

# ✅ GOOD: Solo lee partición necesaria (1GB)
df = spark.read.parquet('s3://bucket/sales/date=2026-01-12')
# Cost: $0.10 (100x más barato)
```

### 4. Column Pruning

```python
# ❌ BAD: Lee 50 columnas
df = spark.read.parquet('data')
result = df.select('id', 'amount')
# Pero lee TODAS las columnas del disco

# ✅ GOOD: Parquet columnar, solo lee 2 columnas
# Automático con Parquet
# 25x más rápido, 25x más barato
```

### 5. Spot/Preemptible Instances

```bash
# ❌ On-demand: $2/hora
# ✅ Spot: $0.40/hora (80% descuento)

# AWS EMR con spot
--instance-type r5.4xlarge \\
--bid-price 0.50

# Ahorro: $12,000/año por cluster
```

---

## 📊 Análisis de Spark UI

```
Identificar bottlenecks:
1. Stage con shuffle writes alto → Broadcast join
2. Tasks con spill to disk → Más memoria
3. Skewed partitions → Repartition
4. Muchos small tasks → Coalesce
```

---

## 💡 Quick Wins

| Optimización | Effort | Impacto | ROI |
|--------------|--------|---------|-----|
| Broadcast joins pequeñas dims | Bajo | 10x | ⭐⭐⭐⭐⭐ |
| Spot instances | Bajo | 5x | ⭐⭐⭐⭐⭐ |
| OPTIMIZE/compaction | Medio | 3x | ⭐⭐⭐⭐ |
| Partition pruning fix | Bajo | 10x | ⭐⭐⭐⭐⭐ |
| Column pruning (SELECT) | Bajo | 2x | ⭐⭐⭐⭐ |

---

## 📚 Recursos

- [Spark Performance Tuning](https://spark.apache.org/docs/latest/sql-performance-tuning.html)
- [AWS EMR Cost Optimization](https://docs.aws.amazon.com/emr/latest/ManagementGuide/emr-plan-instances-guidelines.html)
