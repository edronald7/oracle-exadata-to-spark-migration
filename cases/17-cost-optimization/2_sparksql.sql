-- Spark SQL: Cost Optimization Techniques

-- En Cloud, cost = compute hours + storage + data transfer
-- Optimizar es CRÍTICO para no quebrar el presupuesto

-- =====================================================
-- Optimización 1: Broadcast Join (evita shuffle costoso)
-- =====================================================

-- ❌ BAD: Shuffle join (cost alto)
SELECT f.*, d.region_name
FROM fact_sales f
JOIN dim_region d ON f.region_id = d.region_id;
-- Cost: $50/día si fact_sales es grande

-- ✅ GOOD: Broadcast join (dimension pequeña)
SELECT /*+ BROADCAST(d) */ f.*, d.region_name
FROM fact_sales f
JOIN dim_region d ON f.region_id = d.region_id;
-- Cost: $5/día (10x más barato)

-- =====================================================
-- Optimización 2: Partition Pruning
-- =====================================================

-- ❌ BAD: Escanea toda la tabla (1TB)
SELECT * FROM fact_sales WHERE sale_date = '2026-01-12';
-- Cost: $10

-- ✅ GOOD: Solo lee partición necesaria (1GB)
-- Asume partitionBy('sale_date') al escribir
SELECT * FROM fact_sales WHERE sale_date = '2026-01-12';
-- Spark automáticamente hace pruning si está particionado
-- Cost: $0.10 (100x más barato)

-- =====================================================
-- Optimización 3: Column Pruning (Parquet columnar)
-- =====================================================

-- ❌ BAD: Lee todas las 50 columnas
SELECT * FROM fact_sales;

-- ✅ GOOD: Solo lee columnas necesarias
SELECT customer_id, amount FROM fact_sales;
-- Parquet solo lee esas 2 columnas del disco
-- Cost: 25x más barato

-- =====================================================
-- Optimización 4: Compaction (Small Files Problem)
-- =====================================================

-- Consolidar archivos pequeños
OPTIMIZE fact_sales_delta;

-- Z-Ordering para mejor data layout
OPTIMIZE fact_sales_delta ZORDER BY (customer_id);

-- Resultado: 
-- - 10x faster queries
-- - 50% less cost (menos S3 API calls)

-- =====================================================
-- Optimización 5: Caching (queries repetitivas)
-- =====================================================

-- Cache tabla en memoria si se usa múltiples veces
CACHE TABLE dim_product;

SELECT * FROM dim_product WHERE category = 'Electronics';
SELECT * FROM dim_product WHERE category = 'Clothing';
-- Segunda query es instant (desde cache)

-- Limpiar cache cuando termine
UNCACHE TABLE dim_product;

-- =====================================================
-- Optimización 6: Vacuum (Delta Lake)
-- =====================================================

-- Limpiar versiones antiguas (reduce storage cost)
VACUUM fact_sales_delta RETAIN 168 HOURS;  -- 7 días
-- Ahorra: 30-50% storage costs

-- =====================================================
-- Optimización 7: AQE (Adaptive Query Execution)
-- =====================================================

-- Habilitar en configuración Spark:
-- spark.sql.adaptive.enabled = true
-- spark.sql.adaptive.coalescePartitions.enabled = true

-- AQE automáticamente:
-- - Optimiza joins en runtime
-- - Maneja data skew
-- - Reduce partitions después de shuffle

-- =====================================================
-- Monitoreo de Costos
-- =====================================================

-- Query para analizar tamaño de tablas
SELECT 
    table_name,
    size_in_bytes / 1024 / 1024 / 1024 as size_gb,
    num_files,
    CASE 
        WHEN num_files > 10000 THEN 'OPTIMIZE needed'
        ELSE 'OK'
    END as recommendation
FROM (
    DESCRIBE DETAIL fact_sales_delta
);

-- Ver archivos por partición
SELECT 
    partition,
    COUNT(*) as file_count,
    SUM(size) / 1024 / 1024 as size_mb
FROM (
    LIST 's3://bucket/delta/fact_sales'
)
GROUP BY partition
HAVING file_count > 100
ORDER BY file_count DESC;
