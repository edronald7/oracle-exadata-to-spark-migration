SELECT
  date_format(order_ts, 'yyyy-MM-dd HH:mm:ss') AS ts_str,
  CAST(regexp_replace(amount_str, ',', '.') AS DECIMAL(18,2)) AS amount
FROM raw_orders;
