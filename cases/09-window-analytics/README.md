    # Case 09: Analíticas pesadas (window)

    Buenas prácticas para ventanas sobre grandes particiones.

    ## Exadata context
    ¿Qué parte de Exadata toca este caso? (offload, HCC, bloom, MV, cache, flashback, hints).

    ## Oracle SQL (representativo)
    ```sql
    SELECT
  user_id,
  event_ts,
  SUM(amount) OVER (PARTITION BY user_id ORDER BY event_ts
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) running_sum
FROM events;
    ```

    ## SparkSQL rewrite / approach
    ```sql
    SELECT
  user_id,
  event_ts,
  SUM(amount) OVER (
    PARTITION BY user_id
    ORDER BY event_ts
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
  ) AS running_sum
FROM events;
    ```

    ## Notas de performance (Spark)
    - Particionar por clave con cardinalidad razonable.
- Evitar ORDER BY innecesario.
- Si user_id enorme/skew, considerar pre-aggregations.

    ## Validación recomendada
    - Conteo de filas por partición
    - Sumas por métricas
    - Diff por llave (full outer join)

    Ver plantillas en `templates/`.
