-- SparkSQL: la optimización viene del layout:
-- - Particionar por country (si cardinalidad razonable)
-- - Bucketing/clustering por customer_id (si aplica en tu motor)
SELECT *
FROM customers
WHERE country = 'CL'
  AND customer_id = 12345;
