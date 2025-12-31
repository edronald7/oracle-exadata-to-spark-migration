# Checklist de migración Exadata → Spark

## Antes de migrar
- Identificar top queries por costo/tiempo/frecuencia
- Extraer DDL + particiones + índices + MVs
- Identificar NLS, timezones, formatos de fechas
- Definir SLA y tolerancia de diferencias (exact vs approx)

## Diseño de datos en lake
- Elegir formato (Delta/Iceberg/Parquet)
- Definir particiones (por fecha/tenant/región)
- Plan de compaction y orden (clustering/ZORDER)
- Estrategia de retención y time travel

## Reescritura SQL
- Eliminar hints Oracle
- Reemplazar constructs Oracle-only (CONNECT BY, PIVOT, etc.)
- Cuidar semántica de NULL/'' y DATE/TIMESTAMP
- Evitar funciones sobre columnas partición en WHERE

## Validación
- Conteo de filas por partición
- Sumas por métricas clave
- Checksums por llaves (hash)
- Diffs para top 100 discrepancias

## Operación
- Scheduling (Airflow/ADF/OCI Data Flow/etc.)
- Observabilidad (logs, métricas, data quality)
- Control de costos (shuffle, storage, autoscaling)
