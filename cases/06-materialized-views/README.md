    # Case 06: Materialized Views

    Convertir MV a tabla derivada (gold) con refresh incremental por partición.

    ## Exadata context
    ¿Qué parte de Exadata toca este caso? (offload, HCC, bloom, MV, cache, flashback, hints).

    ## Oracle SQL (representativo)
    ```sql
    -- Oracle MV (conceptual)
-- CREATE MATERIALIZED VIEW mv_sales_daily
-- BUILD IMMEDIATE REFRESH FAST ON COMMIT AS
SELECT sale_date, store_id, SUM(amount) total
FROM fact_sales
GROUP BY sale_date, store_id;
    ```

    ## SparkSQL rewrite / approach
    ```sql
    -- SparkSQL: tabla derivada (ej. Delta) + job incremental
-- Full rebuild:
CREATE TABLE IF NOT EXISTS mv_sales_daily AS
SELECT sale_date, store_id, SUM(amount) AS total
FROM fact_sales
GROUP BY sale_date, store_id;

-- Incremental idea (por partición):
-- INSERT OVERWRITE mv_sales_daily PARTITION (sale_date='2025-12-19')
-- SELECT ... WHERE sale_date='2025-12-19' GROUP BY ...

    ```

    ## Notas de performance (Spark)
    - Define estrategia de refresh (diario/hora) en scheduler.
- En Delta/Iceberg puedes hacer MERGE incremental.
- Documenta dependencias (latencia de datos).

    ## Validación recomendada
    - Conteo de filas por partición
    - Sumas por métricas
    - Diff por llave (full outer join)

    Ver plantillas en `templates/`.
