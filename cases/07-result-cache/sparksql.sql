-- SparkSQL
CACHE TABLE fact_sales; -- o cache de una vista/resultado intermedio
SELECT region, SUM(amount) AS total
FROM fact_sales
GROUP BY region;
