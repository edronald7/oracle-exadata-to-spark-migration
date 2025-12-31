-- Validación simple (SparkSQL)
-- Comparar contra un export Oracle en lake: oracle_trx
SELECT
  COUNT(*) AS cnt,
  SUM(amount) AS sum_amount
FROM trx
WHERE trx_date >= DATE '2025-12-01'
  AND trx_date <  DATE '2026-01-01'
  AND status = 'OK';

SELECT
  COUNT(*) AS cnt,
  SUM(amount) AS sum_amount
FROM oracle_trx
WHERE trx_date >= DATE '2025-12-01'
  AND trx_date <  DATE '2026-01-01'
  AND status = 'OK';
