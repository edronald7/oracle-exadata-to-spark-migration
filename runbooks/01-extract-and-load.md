# Runbook: Extract (Oracle/Exadata) → Load (Lakehouse)

## Extract options
- Oracle Data Pump / External Tables
- JDBC batch export
- Oracle GoldenGate / CDC
- Cloud services (OCI GoldenGate, etc.)

## Load options
- Parquet/Delta/Iceberg
- Control de tipos (DECIMAL, TIMESTAMP, CHAR/VARCHAR)
- Normalización de NLS / timezone

## Always capture
- DDL (column types, constraints)
- partitioning info
- sample data + edge cases
