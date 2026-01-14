# Contributing

## Add a new case
Create a folder under `cases/NN-short-title/` with:

### Required files:
- `README.md` - Comparativa conceptual con 4 secciones:
  - Oracle Exadata SQL (con contexto de features)
  - Spark SQL
  - PySpark (DataFrame API)
  - Scala Spark (Dataset API)
- `1_oracle.sql` - Query Oracle original
- `2_sparksql.sql` - Query Spark SQL
- `3_pyspark.py` - Implementación PySpark
- `4_scala.scala` - Implementación Scala

### Optional but recommended:
- `data/generate_data.py` - Script para generar datos de prueba
- `notebooks/example.ipynb` - Notebook ejecutable
- `validation.py` - Tests de validación
- `cloud/` - Notas específicas de cloud providers

## Principles
1. **Didáctico primero**: explica el "por qué", no solo el "cómo"
2. **Ejecutable**: todos los ejemplos deben correr con datos de prueba
3. **Multi-lenguaje**: siempre incluir SQL, PySpark y Scala
4. **Cloud-aware**: mencionar consideraciones de AWS/Azure/GCP
5. **Performance**: incluir métricas y explain plans
6. **Validación**: siempre incluir forma de comparar resultados

## Code style
- **PySpark**: PEP 8, type hints cuando sea posible
- **Scala**: Scala style guide, prefer immutable operations
- **SQL**: mayúsculas para keywords, snake_case para nombres

## Testing
Asegúrate que tu código pasa:
```bash
# PySpark
pytest tests/test_pyspark.py

# Scala
sbt test

# SQL
sqlfluff lint cases/**/*.sql
```
