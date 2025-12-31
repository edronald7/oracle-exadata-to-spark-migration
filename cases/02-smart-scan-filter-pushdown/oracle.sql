SELECT /*+ FULL(t) */
  t.customer_id, t.amount
FROM trx t
WHERE t.trx_date BETWEEN DATE '2025-12-01' AND DATE '2025-12-31'
  AND t.status = 'OK';
