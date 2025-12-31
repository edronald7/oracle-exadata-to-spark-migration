# Evitar romper partition pruning

## Anti-pattern
```sql
WHERE date(event_ts) = '2025-12-19'
```

## Better
```sql
WHERE event_ts >= '2025-12-19 00:00:00'
  AND event_ts <  '2025-12-20 00:00:00'
```

o si ya tienes columna `event_date` particionada:
```sql
WHERE event_date = '2025-12-19'
```
