-- Spark SQL: Structured Streaming
-- Nota: La sintaxis SQL para streaming es limitada
-- Para producción usar DataFrame API (PySpark/Scala)

-- 1. Crear tabla Delta para streaming output
CREATE TABLE IF NOT EXISTS customer_event_aggregates (
    time_window STRUCT<start: TIMESTAMP, end: TIMESTAMP>,
    customer_id INT,
    event_count BIGINT,
    total_amount DECIMAL(10, 2)
) USING DELTA
LOCATION 's3://bucket/delta/event_aggregates';

-- 2. Leer stream desde Kafka (vía DataFrame API)
-- Ver archivo 3_pyspark.py para implementación completa

-- 3. Query sobre tabla streaming (batch query sobre resultados)
SELECT 
    time_window.start as window_start,
    time_window.end as window_end,
    customer_id,
    event_count,
    total_amount
FROM customer_event_aggregates
WHERE time_window.start >= current_timestamp() - INTERVAL 1 HOUR
ORDER BY time_window.start DESC
LIMIT 100;

-- 4. Estadísticas de eventos por ventana de tiempo
SELECT 
    DATE_TRUNC('hour', time_window.start) as hour,
    COUNT(DISTINCT customer_id) as unique_customers,
    SUM(event_count) as total_events,
    SUM(total_amount) as total_revenue
FROM customer_event_aggregates
GROUP BY DATE_TRUNC('hour', time_window.start)
ORDER BY hour DESC;

-- Nota: Para configurar el stream propiamente, debes usar:
-- - PySpark: spark.readStream.format("kafka")...
-- - Scala: spark.readStream.format("kafka")...
-- SQL tiene soporte limitado para streaming setup
