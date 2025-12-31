-- Oracle MV (conceptual)
-- CREATE MATERIALIZED VIEW mv_sales_daily
-- BUILD IMMEDIATE REFRESH FAST ON COMMIT AS
SELECT sale_date, store_id, SUM(amount) total
FROM fact_sales
GROUP BY sale_date, store_id;
