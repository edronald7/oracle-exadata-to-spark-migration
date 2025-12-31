# Estrategia de validación (Oracle vs Spark)

## 1) Validación de volumen
- row count total
- row count por partición (día/mes/tenant)

## 2) Validación de métricas
- sum(amount), count(distinct), min/max
- comparar por llaves de negocio

## 3) Detección de diffs
- full outer join por llave + comparar columnas
- muestrear discrepancias

## 4) Considerar diferencias esperadas
- timezone / parseo de timestamps
- redondeos DECIMAL vs NUMBER
- ordenamiento / null ordering

Ver `templates/` para queries de reconciliación.
