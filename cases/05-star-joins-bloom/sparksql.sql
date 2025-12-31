SELECT /*+ BROADCAST(p), BROADCAST(s) */
  SUM(f.amount) AS total
FROM fact_sales f
JOIN dim_product p ON p.product_id = f.product_id
JOIN dim_store s ON s.store_id = f.store_id
WHERE p.category = 'PHONES'
  AND s.country = 'PE';
