    # Case 01: Hints Oracle & paralelismo

    Eliminar hints (PARALLEL, FULL, USE_HASH) y trasladar la intención a tuning Spark.

    ## Exadata context
    ¿Qué parte de Exadata toca este caso? (offload, HCC, bloom, MV, cache, flashback, hints).

    ## Oracle SQL (representativo)
    ```sql
    SELECT /*+ PARALLEL(8) FULL(f) USE_HASH(d) */
  d.region, SUM(f.amount) total
FROM fact_sales f
JOIN dim_region d ON d.region_id = f.region_id
WHERE f.sale_date >= DATE '2025-01-01'
GROUP BY d.region;
    ```

    ## SparkSQL rewrite / approach
    ```sql
    -- SparkSQL: hints Oracle se eliminan; si aplica usar hints de Spark
SELECT /*+ BROADCAST(d) */
  d.region, SUM(f.amount) AS total
FROM fact_sales f
JOIN dim_region d ON d.region_id = f.region_id
WHERE f.sale_date >= DATE '2025-01-01'
GROUP BY d.region;
    ```

    ## Notas de performance (Spark)
    - Spark maneja paralelismo por particiones/shuffle.
- Ajusta `spark.sql.shuffle.partitions` y usa AQE.
- Usa BROADCAST solo si dim es pequeña.

    ## Validación recomendada
    - Conteo de filas por partición
    - Sumas por métricas
    - Diff por llave (full outer join)

    Ver plantillas en `templates/`.
