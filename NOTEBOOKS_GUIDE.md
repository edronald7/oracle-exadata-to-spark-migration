# 📚 Guía de Notebooks Jupyter

**Última actualización**: 2026-01-12  
**Total de notebooks**: 3

---

## 🎯 Resumen

Los notebooks Jupyter proporcionan experiencias **hands-on** ejecutables para aprender los casos más críticos del repositorio.

Cada notebook incluye:
- ✅ Código ejecutable paso a paso
- ✅ Datos sintéticos generados automáticamente
- ✅ Explicaciones detalladas
- ✅ Validaciones y verificaciones
- ✅ Conclusiones y best practices

---

## 📓 Notebooks Disponibles

### 1. Getting Started (01-getting-started.ipynb)

**Status**: ✅ Iniciado  
**Nivel**: Principiante  
**Duración**: 15-20 minutos

**Contenido**:
- Setup inicial de Spark
- Primeros queries SQL vs PySpark
- Comparativa básica de sintaxis

**Cómo ejecutar**:
```bash
cd notebooks
jupyter notebook 01-getting-started.ipynb
```

---

### 2. CDC e Ingesta Incremental (13-cdc-incremental.ipynb)

**Status**: ✅ **COMPLETO**  
**Nivel**: Intermedio-Avanzado  
**Duración**: 30-45 minutos  
**Criticidad**: ⭐⭐⭐⭐⭐ (MÁXIMA)

**Lo que aprenderás**:
1. Generar datos CDC sintéticos (simula Oracle GoldenGate)
2. Implementar deduplicación con Window Functions
3. Crear tabla Delta Lake
4. Ejecutar MERGE operation (UPDATE/DELETE/INSERT)
5. Validar resultados
6. Usar Time Travel para auditoría

**Celdas incluidas**: 17 celdas
- 8 celdas de código ejecutable
- 9 celdas markdown con explicaciones

**Highlights**:
```python
# Deduplicación
window_spec = Window.partitionBy("customer_id").orderBy(col("op_ts").desc())
deduplicated = cdc_df.withColumn("rn", row_number().over(window_spec))

# MERGE a Delta Lake
target_table.merge(source, condition)
  .whenMatchedUpdate(...)
  .whenMatchedDelete(...)
  .whenNotMatchedInsert(...)
```

**Cómo ejecutar**:
```bash
cd notebooks
jupyter notebook 13-cdc-incremental.ipynb
```

**Prerrequisitos**:
- Spark 3.x
- Delta Lake (`pip install delta-spark`)

---

### 3. Data Quality y Error Handling (14-data-quality.ipynb)

**Status**: ✅ **COMPLETO**  
**Nivel**: Intermedio  
**Duración**: 30 minutos  
**Criticidad**: ⭐⭐⭐⭐⭐ (MÁXIMA)

**Lo que aprenderás**:
1. Generar datos con errores (JSON corruptos, nulls, valores fuera de rango)
2. Leer con PERMISSIVE mode para capturar bad records
3. Aplicar validaciones de negocio
4. Separar datos válidos e inválidos
5. Implementar quarantine tables
6. Generar reportes de data quality

**Celdas incluidas**: 17 celdas
- 8 celdas de código ejecutable
- 9 celdas markdown con explicaciones

**Problemas que detecta**:
- ❌ JSON malformado (30 registros)
- ❌ Emails sin @ (30 registros)
- ❌ Edad negativa (20 registros)
- ❌ IDs nulos (20 registros)

**Highlights**:
```python
# PERMISSIVE mode
raw_df = spark.read \
    .option("mode", "PERMISSIVE") \
    .option("columnNameOfCorruptRecord", "_corrupt_record") \
    .json("file.json")

# Validaciones
validated = df.withColumn("quality_status",
    when(col("id").isNull(), "NULL_ID")
    .when(~col("email").contains("@"), "INVALID_EMAIL")
    .otherwise("VALID")
)

# Quarantine
invalid_records.write.partitionBy("reason").parquet("/quarantine")
```

**Cómo ejecutar**:
```bash
cd notebooks
jupyter notebook 14-data-quality.ipynb
```

---

## 🚀 Quick Start

### Opción 1: Localmente con Docker

```bash
# 1. Clonar repo
git clone https://github.com/tu-usuario/oracle-exadata-to-spark-migration.git
cd oracle-exadata-to-spark-migration

# 2. Iniciar Jupyter con Spark
docker run -it -p 8888:8888 \
  -v $(pwd):/workspace \
  jupyter/pyspark-notebook

# 3. Abrir notebooks en http://localhost:8888
```

### Opción 2: Azure Databricks

```bash
# 1. Crear workspace en Azure Portal
# 2. En Databricks UI:
#    - Workspace → Import
#    - Seleccionar notebooks/*.ipynb
#    - Ejecutar interactivamente
```

### Opción 3: AWS EMR con JupyterHub

```bash
# Ver cloud/aws/emr-setup.md para instrucciones detalladas

# 1. Crear cluster con Jupyter
aws emr create-cluster \
  --applications Name=Spark Name=JupyterHub \
  --release-label emr-7.0.0 \
  ...

# 2. Acceder a JupyterHub en puerto 9443
# 3. Upload notebooks
```

---

## 📊 Estado de Notebooks

| Notebook | Status | Celdas | Nivel | Tiempo |
|----------|--------|--------|-------|--------|
| 01-getting-started | ✅ Iniciado | 10+ | Principiante | 15min |
| 13-cdc-incremental | ✅ **COMPLETO** | 17 | Avanzado | 45min |
| 14-data-quality | ✅ **COMPLETO** | 17 | Intermedio | 30min |
| 15-streaming | 🔜 Pendiente | — | Avanzado | — |
| 17-cost-optimization | 🔜 Pendiente | — | Intermedio | — |

---

## 🎓 Ruta de Aprendizaje Recomendada

### Para Analistas SQL
1. ✅ **01-getting-started** - Introducción
2. ✅ **13-cdc-incremental** - Ver queries SQL
3. Leer READMEs de casos 02-12

### Para Data Engineers
1. ✅ **01-getting-started** - Setup
2. ✅ **14-data-quality** - Manejo de errores (CRÍTICO)
3. ✅ **13-cdc-incremental** - CDC patterns (CRÍTICO)
4. 🔜 **15-streaming** - Real-time (próximamente)
5. Implementar casos en producción

### Para Arquitectos
1. Revisar todos los notebooks para entender implementaciones
2. Leer `docs/cloud-deployment-guide.md`
3. Diseñar arquitectura usando patrones aprendidos

---

## 💡 Tips para Usar los Notebooks

### Ejecución Secuencial
- ⚠️ **Ejecuta las celdas en orden** (no saltar pasos)
- Algunas celdas dependen de resultados anteriores

### Limpieza de Datos
```python
# Si necesitas reiniciar:
import shutil
shutil.rmtree("/tmp/cdc_data", ignore_errors=True)
shutil.rmtree("/tmp/delta", ignore_errors=True)
# Luego re-ejecutar desde el inicio
```

### Modificar Volumen de Datos
```python
# En generadores, cambiar:
spark.range(1, 1001)  # 1000 registros
# A:
spark.range(1, 10001)  # 10,000 registros
```

### Verificar Spark UI
```bash
# Mientras el notebook está corriendo:
# Abrir http://localhost:4040 para ver Spark UI
# Ver stages, tasks, DAG, storage
```

---

## 🔧 Troubleshooting

### Error: Delta Lake no encontrado
```bash
pip install delta-spark==2.4.0
```

### Error: OutOfMemoryError
```python
# Aumentar memoria del driver
spark = SparkSession.builder \
    .config("spark.driver.memory", "4g") \
    .getOrCreate()
```

### Error: Permission denied en /tmp
```python
# Cambiar rutas a directorio del usuario
output_path = "/Users/tu-usuario/spark-data/cdc"
```

---

## 📚 Recursos Adicionales

### Documentación Complementaria
- `cases/13-cdc-incremental/README.md` - Teoría completa
- `cases/14-data-quality/README.md` - Patrones avanzados
- `docs/pyspark-best-practices.md` - Best practices

### Código de Referencia
- `cases/13-cdc-incremental/3_pyspark.py` - CDC production
- `templates/pyspark/validation.py` - Validations framework

---

## 🔜 Próximos Notebooks Planeados

1. **15-streaming.ipynb** (Prioridad Alta)
   - Kafka → Spark → Delta Lake
   - Watermarking
   - Windowed aggregations

2. **17-cost-optimization.ipynb** (Prioridad Alta)
   - Analizar Spark UI
   - Optimizar queries
   - Reducir costos 10x

3. **02-smart-scan.ipynb** (Prioridad Media)
   - Predicate pushdown
   - Partition pruning
   - Column pruning

---

## 🤝 Contribuir

¿Quieres agregar un notebook?

1. Usa notebooks existentes como template
2. Incluye:
   - Markdown intro con objetivos
   - Setup cell
   - Código ejecutable paso a paso
   - Validaciones
   - Conclusiones
3. Testea completamente
4. Abre PR

---

## 📞 Soporte

- **Issues**: Reportar problemas con notebooks
- **Discussions**: Preguntas sobre ejecución
- **Email**: edronald7@gmail.com

---

**Última actualización**: 2026-01-12  
**Mantenido por**: edronald7@gmail.com + community  
**Licencia**: MIT
