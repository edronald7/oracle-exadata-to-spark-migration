    # Case 05: Star joins / Bloom filter acceleration

    Equivalente: broadcast dims, AQE y manejo de skew.

    ## Exadata context
    ¿Qué parte de Exadata toca este caso? (offload, HCC, bloom, MV, cache, flashback, hints).

    ## Oracle SQL (representativo)
    ```sql
    SELECT SUM(f.amount)
FROM fact_sales f
JOIN dim_product p ON p.product_id = f.product_id
JOIN dim_store s ON s.store_id = f.store_id
WHERE p.category = 'PHONES'
  AND s.country = 'PE';
    ```

    ## SparkSQL rewrite / approach
    ```sql
    SELECT /*+ BROADCAST(p), BROADCAST(s) */
  SUM(f.amount) AS total
FROM fact_sales f
JOIN dim_product p ON p.product_id = f.product_id
JOIN dim_store s ON s.store_id = f.store_id
WHERE p.category = 'PHONES'
  AND s.country = 'PE';
    ```

    ## Notas de performance (Spark)
    - Broadcast dims si son pequeñas.
- Si hay skew en claves, usa salting o AQE skew join.
- Filtra dims antes del join.

    ## Validación recomendada
    - Conteo de filas por partición
    - Sumas por métricas
    - Diff por llave (full outer join)

    Ver plantillas en `templates/`.
