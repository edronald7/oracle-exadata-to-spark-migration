    # Case 07: Result Cache

    Cache en Spark para reportes repetidos y datasets intermedios.

    ## Exadata context
    ¿Qué parte de Exadata toca este caso? (offload, HCC, bloom, MV, cache, flashback, hints).

    ## Oracle SQL (representativo)
    ```sql
    SELECT /*+ RESULT_CACHE */
  region, SUM(amount) total
FROM fact_sales
GROUP BY region;
    ```

    ## SparkSQL rewrite / approach
    ```sql
    -- SparkSQL
CACHE TABLE fact_sales; -- o cache de una vista/resultado intermedio
SELECT region, SUM(amount) AS total
FROM fact_sales
GROUP BY region;
    ```

    ## Notas de performance (Spark)
    - Útil en notebooks/BI con repetición.
- Controla memoria; considera cache por etapa.
- En lakehouse puede existir caching a nivel plataforma.

    ## Validación recomendada
    - Conteo de filas por partición
    - Sumas por métricas
    - Diff por llave (full outer join)

    Ver plantillas en `templates/`.
