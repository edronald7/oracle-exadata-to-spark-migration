    # Case 12: Set semantics (MINUS/duplicates)

    Alinear semántica DISTINCT vs ALL.

    ## Exadata context
    ¿Qué parte de Exadata toca este caso? (offload, HCC, bloom, MV, cache, flashback, hints).

    ## Oracle SQL (representativo)
    ```sql
    SELECT customer_id FROM a
MINUS
SELECT customer_id FROM b;
    ```

    ## SparkSQL rewrite / approach
    ```sql
    SELECT customer_id FROM a
EXCEPT
SELECT customer_id FROM b;
    ```

    ## Notas de performance (Spark)
    - `EXCEPT` suele ser DISTINCT.
- Si necesitas multiset, evalúa `EXCEPT ALL` (si aplica) o implementa con counts.

    ## Validación recomendada
    - Conteo de filas por partición
    - Sumas por métricas
    - Diff por llave (full outer join)

    Ver plantillas en `templates/`.
