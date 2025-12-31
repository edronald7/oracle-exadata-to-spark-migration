# Spark performance tuning (en contexto Exadata)

## Equivalentes mentales
- Smart Scan → partition pruning + pushdown + column pruning
- Bloom filter join → broadcast join + AQE + skew fixes
- Storage index → clustering + data skipping stats
- Result cache → cache/persist + lakehouse cache
- MV rewrite → gold tables + incremental

## Ajustes típicos
- Habilitar AQE: `spark.sql.adaptive.enabled=true`
- Broadcast: `/*+ BROADCAST(dim) */` cuando corresponda
- Skew: `spark.sql.adaptive.skewJoin.enabled=true`
- Control de shuffle partitions: `spark.sql.shuffle.partitions`
- Evitar `SELECT *` en hechos grandes
- Filtrar antes de join cuando sea posible
