    # Case 02: Smart Scan / filter pushdown

    Equivalente práctico: particiones + predicate pushdown + column pruning.

    ## Exadata context
    ¿Qué parte de Exadata toca este caso? (offload, HCC, bloom, MV, cache, flashback, hints).

    ## Oracle SQL (representativo)
    ```sql
    SELECT /*+ FULL(t) */
  t.customer_id, t.amount
FROM trx t
WHERE t.trx_date BETWEEN DATE '2025-12-01' AND DATE '2025-12-31'
  AND t.status = 'OK';
    ```

    ## SparkSQL rewrite / approach
    ```sql
    SELECT
  customer_id, amount
FROM trx
WHERE trx_date >= DATE '2025-12-01'
  AND trx_date <  DATE '2026-01-01'
  AND status = 'OK';
    ```

    ## Notas de performance (Spark)
    - Evita `SELECT *`.
- Si `trx_date` es partición, el rango permite pruning.
- Usar formatos Parquet/Delta para pushdown.

    ## Validación recomendada
    - Conteo de filas por partición
    - Sumas por métricas
    - Diff por llave (full outer join)

    Ver plantillas en `templates/`.
