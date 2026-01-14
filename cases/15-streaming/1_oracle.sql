-- Oracle: Procesamiento Batch (no streaming nativo)

-- Oracle no tiene streaming nativo como Spark
-- Alternativa 1: Batch queries con intervals pequeños

-- Query ejecutado cada 5 minutos via scheduler
SELECT 
    customer_id,
    event_type,
    COUNT(*) as event_count,
    SUM(amount) as total_amount,
    TRUNC(event_timestamp, 'MI') as time_bucket
FROM customer_events
WHERE event_timestamp >= SYSDATE - INTERVAL '5' MINUTE
GROUP BY 
    customer_id,
    event_type,
    TRUNC(event_timestamp, 'MI');

-- Insertar resultados en tabla agregada
INSERT INTO customer_event_summary
SELECT 
    customer_id,
    event_type,
    COUNT(*) as event_count,
    SUM(amount) as total_amount,
    TRUNC(event_timestamp, 'MI') as time_window,
    SYSDATE as processed_at
FROM customer_events
WHERE event_timestamp >= SYSDATE - INTERVAL '5' MINUTE
  AND event_timestamp < SYSDATE
GROUP BY 
    customer_id,
    event_type,
    TRUNC(event_timestamp, 'MI');

-- Alternativa 2: Oracle GoldenGate para CDC real-time
-- (Requiere licencia y configuración separada)

-- Alternativa 3: Oracle Streams (deprecated en 19c)
-- Reemplazado por GoldenGate
