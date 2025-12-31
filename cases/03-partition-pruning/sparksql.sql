-- Mejor: si tienes event_date particionada
SELECT COUNT(*)
FROM fact_events
WHERE event_date = DATE '2025-12-19';

-- Alternativa (sin event_date):
-- WHERE event_ts >= '2025-12-19 00:00:00' AND event_ts < '2025-12-20 00:00:00'
