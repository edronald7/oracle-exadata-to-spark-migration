-- SparkSQL: tabla derivada (ej. Delta) + job incremental
-- Full rebuild:
CREATE TABLE IF NOT EXISTS mv_sales_daily AS
SELECT sale_date, store_id, SUM(amount) AS total
FROM fact_sales
GROUP BY sale_date, store_id;

-- Incremental idea (por partición):
-- INSERT OVERWRITE mv_sales_daily PARTITION (sale_date='2025-12-19')
-- SELECT ... WHERE sale_date='2025-12-19' GROUP BY ...
