SELECT
  customer_id, amount
FROM trx
WHERE trx_date >= DATE '2025-12-01'
  AND trx_date <  DATE '2026-01-01'
  AND status = 'OK';
