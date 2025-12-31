    # Case 10: MERGE / SCD

    Exadata MERGE a Delta MERGE o estrategia append+reconcile.

    ## Exadata context
    ¿Qué parte de Exadata toca este caso? (offload, HCC, bloom, MV, cache, flashback, hints).

    ## Oracle SQL (representativo)
    ```sql
    MERGE INTO dim_customer t
USING stg_customer s
ON (t.customer_id = s.customer_id)
WHEN MATCHED THEN UPDATE SET t.name = s.name, t.updated_at = SYSDATE
WHEN NOT MATCHED THEN INSERT (customer_id, name, updated_at) VALUES (s.customer_id, s.name, SYSDATE);
    ```

    ## SparkSQL rewrite / approach
    ```sql
    -- Delta Lake (si aplica)
MERGE INTO dim_customer t
USING stg_customer s
ON t.customer_id = s.customer_id
WHEN MATCHED THEN UPDATE SET name = s.name, updated_at = current_timestamp()
WHEN NOT MATCHED THEN INSERT (customer_id, name, updated_at)
VALUES (s.customer_id, s.name, current_timestamp());
    ```

    ## Notas de performance (Spark)
    - Si no hay Delta: usar estrategia insert-only + view latest, o jobs de compaction.
- Para SCD2, ver README del caso.

    ## Validación recomendada
    - Conteo de filas por partición
    - Sumas por métricas
    - Diff por llave (full outer join)

    Ver plantillas en `templates/`.
