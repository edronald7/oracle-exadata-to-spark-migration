SELECT COUNT(*)
FROM fact_events
WHERE TRUNC(event_ts) = DATE '2025-12-19';
