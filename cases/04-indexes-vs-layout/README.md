    # Case 04: Índices vs layout de archivos

    En vez de B-tree/bitmap: particiones, bucketing, clustering y stats por archivo.

    ## Exadata context
    ¿Qué parte de Exadata toca este caso? (offload, HCC, bloom, MV, cache, flashback, hints).

    ## Oracle SQL (representativo)
    ```sql
    SELECT *
FROM customers
WHERE country = 'CL'
  AND customer_id = 12345;
    ```

    ## SparkSQL rewrite / approach
    ```sql
    -- SparkSQL: la optimización viene del layout:
-- - Particionar por country (si cardinalidad razonable)
-- - Bucketing/clustering por customer_id (si aplica en tu motor)
SELECT *
FROM customers
WHERE country = 'CL'
  AND customer_id = 12345;
    ```

    ## Notas de performance (Spark)
    - Si `country` tiene baja cardinalidad, particionar funciona.
- Para alta cardinalidad, usar clustering/ZORDER.
- Compaction ayuda a data skipping.

    ## Validación recomendada
    - Conteo de filas por partición
    - Sumas por métricas
    - Diff por llave (full outer join)

    Ver plantillas en `templates/`.
