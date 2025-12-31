    # Case 08: Flashback → Time travel

    Oracle `AS OF TIMESTAMP` a time travel (Delta/Iceberg) o snapshots.

    ## Exadata context
    ¿Qué parte de Exadata toca este caso? (offload, HCC, bloom, MV, cache, flashback, hints).

    ## Oracle SQL (representativo)
    ```sql
    SELECT *
FROM accounts AS OF TIMESTAMP (SYSTIMESTAMP - INTERVAL '1' HOUR)
WHERE status = 'ACTIVE';
    ```

    ## SparkSQL rewrite / approach
    ```sql
    -- Delta Lake example (si aplica)
-- SELECT * FROM accounts TIMESTAMP AS OF '2025-12-19T09:00:00Z' WHERE status='ACTIVE';

-- Alternativa sin time travel: mantener snapshots particionados por load_ts y consultar el snapshot deseado.

    ```

    ## Notas de performance (Spark)
    - Requiere lakehouse con time travel o estrategia de snapshots.
- Define retención y compliance.

    ## Validación recomendada
    - Conteo de filas por partición
    - Sumas por métricas
    - Diff por llave (full outer join)

    Ver plantillas en `templates/`.
