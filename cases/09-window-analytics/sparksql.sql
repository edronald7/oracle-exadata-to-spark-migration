SELECT
  user_id,
  event_ts,
  SUM(amount) OVER (
    PARTITION BY user_id
    ORDER BY event_ts
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
  ) AS running_sum
FROM events;
