-- Oracle Exadata: Optimizaciones de Costo (Licenciamiento)

-- En Oracle, el costo viene de:
-- 1. Licencias (muy caras)
-- 2. CPU/Cores (license per core)
-- 3. Storage (HCC compression ayuda)
-- 4. Mantenimiento anual (22% del costo de licencia)

-- Optimización 1: Compression (reduce storage cost)
ALTER TABLE fact_sales COMPRESS FOR QUERY HIGH;
-- Hybrid Columnar Compression (HCC)
-- Ratio de compresión: 10x-15x

-- Optimización 2: Partition Pruning (reduce I/O)
SELECT /*+ PARALLEL(8) */ 
    region, 
    SUM(amount) 
FROM fact_sales
WHERE sale_date = DATE '2026-01-12'  -- Solo lee esa partición
GROUP BY region;

-- Optimización 3: Materialized View (pre-compute)
CREATE MATERIALIZED VIEW mv_sales_summary
BUILD IMMEDIATE
REFRESH FAST ON COMMIT
AS
SELECT 
    region_id,
    product_id,
    TRUNC(sale_date, 'MM') as month,
    SUM(amount) as total_sales
FROM fact_sales
GROUP BY region_id, product_id, TRUNC(sale_date, 'MM');

-- Query usa MV automáticamente (query rewrite)
SELECT region_id, SUM(total_sales)
FROM mv_sales_summary
WHERE month = DATE '2026-01-01'
GROUP BY region_id;

-- Optimización 4: Result Cache
ALTER SYSTEM SET RESULT_CACHE_MODE = FORCE;
SELECT /*+ RESULT_CACHE */ COUNT(*) FROM customers;

-- En Cloud (OCI): Cost = CPU hours + storage GB
-- Pero migrar a Spark on AWS/Azure puede reducir 60-80% total cost
