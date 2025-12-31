-- Reconciliación genérica (SparkSQL)
-- Reemplaza <pk_cols> y <compare_cols>
WITH o AS (SELECT * FROM oracle_exported_table),
     s AS (SELECT * FROM spark_table)
SELECT
  COALESCE(o.<pk>, s.<pk>) AS pk,
  CASE WHEN o.<pk> IS NULL THEN 'ONLY_IN_SPARK'
       WHEN s.<pk> IS NULL THEN 'ONLY_IN_ORACLE'
       ELSE 'IN_BOTH' END AS presence,
  -- ejemplo de comparación
  o.<col> AS oracle_col,
  s.<col> AS spark_col
FROM o
FULL OUTER JOIN s
ON o.<pk> = s.<pk>
WHERE NOT (o.<col> <=> s.<col>);
