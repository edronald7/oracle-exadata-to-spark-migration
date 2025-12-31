SELECT /*+ RESULT_CACHE */
  region, SUM(amount) total
FROM fact_sales
GROUP BY region;
