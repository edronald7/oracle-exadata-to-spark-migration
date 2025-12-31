-- SparkSQL: hints Oracle se eliminan; si aplica usar hints de Spark
SELECT /*+ BROADCAST(d) */
  d.region, SUM(f.amount) AS total
FROM fact_sales f
JOIN dim_region d ON d.region_id = f.region_id
WHERE f.sale_date >= DATE '2025-01-01'
GROUP BY d.region;
