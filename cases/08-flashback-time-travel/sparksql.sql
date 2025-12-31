-- Delta Lake example (si aplica)
-- SELECT * FROM accounts TIMESTAMP AS OF '2025-12-19T09:00:00Z' WHERE status='ACTIVE';

-- Alternativa sin time travel: mantener snapshots particionados por load_ts y consultar el snapshot deseado.
