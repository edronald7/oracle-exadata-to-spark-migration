    # Case 11: Datatypes & NLS

    NUMBER/DATE/NLS y conversiones explícitas.

    ## Exadata context
    ¿Qué parte de Exadata toca este caso? (offload, HCC, bloom, MV, cache, flashback, hints).

    ## Oracle SQL (representativo)
    ```sql
    SELECT
  TO_CHAR(order_ts, 'YYYY-MM-DD HH24:MI:SS') as ts_str,
  TO_NUMBER(amount_str, '999D99', 'NLS_NUMERIC_CHARACTERS=,.') as amount
FROM raw_orders;
    ```

    ## SparkSQL rewrite / approach
    ```sql
    SELECT
  date_format(order_ts, 'yyyy-MM-dd HH:mm:ss') AS ts_str,
  CAST(regexp_replace(amount_str, ',', '.') AS DECIMAL(18,2)) AS amount
FROM raw_orders;
    ```

    ## Notas de performance (Spark)
    - Spark no usa NLS igual que Oracle: normaliza strings.
- Define DECIMAL(p,s) explícito.
- Timezone y parsing deben ser consistentes.

    ## Validación recomendada
    - Conteo de filas por partición
    - Sumas por métricas
    - Diff por llave (full outer join)

    Ver plantillas en `templates/`.
