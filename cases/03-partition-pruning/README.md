    # Case 03: Partition pruning

    Reescribir filtros para aprovechar particiones (no funciones sobre columna partición).

    ## Exadata context
    ¿Qué parte de Exadata toca este caso? (offload, HCC, bloom, MV, cache, flashback, hints).

    ## Oracle SQL (representativo)
    ```sql
    SELECT COUNT(*)
FROM fact_events
WHERE TRUNC(event_ts) = DATE '2025-12-19';
    ```

    ## SparkSQL rewrite / approach
    ```sql
    -- Mejor: si tienes event_date particionada
SELECT COUNT(*)
FROM fact_events
WHERE event_date = DATE '2025-12-19';

-- Alternativa (sin event_date):
-- WHERE event_ts >= '2025-12-19 00:00:00' AND event_ts < '2025-12-20 00:00:00'

    ```

    ## Notas de performance (Spark)
    - `TRUNC(event_ts)` rompe pruning/pushdown.
- Recomienda columna derivada `event_date` para particionar.

    ## Validación recomendada
    - Conteo de filas por partición
    - Sumas por métricas
    - Diff por llave (full outer join)

    Ver plantillas en `templates/`.
