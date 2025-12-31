SELECT
  TO_CHAR(order_ts, 'YYYY-MM-DD HH24:MI:SS') as ts_str,
  TO_NUMBER(amount_str, '999D99', 'NLS_NUMERIC_CHARACTERS=,.') as amount
FROM raw_orders;
