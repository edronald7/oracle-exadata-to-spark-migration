# Runbook: Testing Local con Docker

Guía para ejecutar los casos de migración localmente usando Docker, antes de ir a cloud.

---

## 🎯 Objetivo

Validar casos de migración en tu laptop antes de desplegar en AWS/Azure/GCP.

**Ventajas**:
- Sin costos de cloud
- Iteración rápida
- Debugging fácil
- CI/CD local

---

## 📦 Prerequisites

```bash
# 1. Docker instalado
docker --version
# Docker version 24.0+

# 2. Docker Compose (opcional)
docker-compose --version

# 3. Al menos 8GB RAM disponible
# 4. 10GB espacio en disco
```

---

## 🚀 Quick Start (5 minutos)

### Opción 1: Jupyter PySpark (Recomendado para desarrollo)

```bash
# 1. Iniciar container con Jupyter
docker run -it --rm \
  -p 8888:8888 \
  -v $(pwd):/workspace \
  -w /workspace \
  --name spark-jupyter \
  jupyter/pyspark-notebook:spark-3.5.0

# 2. Abrir browser en la URL mostrada (contiene token)
# http://127.0.0.1:8888/lab?token=...

# 3. Abrir notebook: notebooks/01-getting-started.ipynb
```

### Opción 2: PySpark CLI

```bash
# Iniciar container interactivo
docker run -it --rm \
  -v $(pwd):/workspace \
  -w /workspace \
  apache/spark:3.5.0-python3 \
  /opt/spark/bin/pyspark

# Dentro de PySpark
>>> from pyspark.sql import SparkSession
>>> spark = SparkSession.builder.appName("test").getOrCreate()
>>> spark.range(10).show()
```

### Opción 3: spark-submit

```bash
# Ejecutar script Python
docker run -it --rm \
  -v $(pwd):/workspace \
  -w /workspace \
  apache/spark:3.5.0-python3 \
  /opt/spark/bin/spark-submit \
  cases/01-hints-parallel/3_pyspark.py
```

---

## 🏗️ Setup Completo con Docker Compose

### 1. Crear docker-compose.yml

```yaml
version: '3.8'

services:
  spark-master:
    image: apache/spark:3.5.0
    container_name: spark-master
    hostname: spark-master
    ports:
      - "8080:8080"  # Spark Master UI
      - "7077:7077"  # Spark Master port
      - "4040:4040"  # Spark UI
    environment:
      - SPARK_MODE=master
      - SPARK_RPC_AUTHENTICATION_ENABLED=no
      - SPARK_RPC_ENCRYPTION_ENABLED=no
    command: /opt/spark/bin/spark-class org.apache.spark.deploy.master.Master
    volumes:
      - ./:/workspace

  spark-worker-1:
    image: apache/spark:3.5.0
    container_name: spark-worker-1
    depends_on:
      - spark-master
    environment:
      - SPARK_MODE=worker
      - SPARK_MASTER_URL=spark://spark-master:7077
      - SPARK_WORKER_MEMORY=2G
      - SPARK_WORKER_CORES=2
    command: /opt/spark/bin/spark-class org.apache.spark.deploy.worker.Worker spark://spark-master:7077
    volumes:
      - ./:/workspace

  spark-worker-2:
    image: apache/spark:3.5.0
    container_name: spark-worker-2
    depends_on:
      - spark-master
    environment:
      - SPARK_MODE=worker
      - SPARK_MASTER_URL=spark://spark-master:7077
      - SPARK_WORKER_MEMORY=2G
      - SPARK_WORKER_CORES=2
    command: /opt/spark/bin/spark-class org.apache.spark.deploy.worker.Worker spark://spark-master:7077
    volumes:
      - ./:/workspace

  jupyter:
    image: jupyter/pyspark-notebook:spark-3.5.0
    container_name: spark-jupyter
    ports:
      - "8888:8888"
    environment:
      - SPARK_MASTER=spark://spark-master:7077
      - JUPYTER_ENABLE_LAB=yes
    volumes:
      - ./:/home/jovyan/work
    depends_on:
      - spark-master
```

### 2. Iniciar Cluster

```bash
# Iniciar todos los servicios
docker-compose up -d

# Ver logs
docker-compose logs -f

# Verificar servicios
docker-compose ps
```

### 3. Acceder a UIs

```bash
# Spark Master UI
open http://localhost:8080

# Jupyter Lab
open http://localhost:8888
# Token en logs: docker-compose logs jupyter | grep token

# Spark Application UI (cuando ejecutes jobs)
open http://localhost:4040
```

---

## 📊 Ejecutar Casos de Migración

### 1. Generar Datos de Prueba

```bash
# Entrar al container de jupyter
docker exec -it spark-jupyter bash

# Dentro del container
cd /home/jovyan/work/data/generators
python generate_all.py --size small --output /home/jovyan/work/testdata

# Verificar
ls -lh /home/jovyan/work/testdata/
```

### 2. Ejecutar Caso 01 - PySpark

```bash
# Opción A: En container jupyter
docker exec -it spark-jupyter bash
cd /home/jovyan/work/cases/01-hints-parallel
spark-submit 3_pyspark.py --input-path ../../testdata

# Opción B: Directo con docker run
docker run -it --rm \
  -v $(pwd):/workspace \
  -w /workspace/cases/01-hints-parallel \
  apache/spark:3.5.0-python3 \
  /opt/spark/bin/spark-submit 3_pyspark.py \
  --input-path /workspace/testdata
```

### 3. Ejecutar Caso 01 - Scala

```bash
# Primero compilar (si tienes sbt localmente)
sbt package

# Ejecutar
docker run -it --rm \
  -v $(pwd):/workspace \
  -w /workspace/cases/01-hints-parallel \
  apache/spark:3.5.0 \
  /opt/spark/bin/spark-submit \
  --class com.migration.cases.Case01HintsParallel \
  /workspace/target/scala-2.12/spark-migration-cases.jar \
  /workspace/testdata
```

### 4. Ejecutar Notebook Interactivo

1. Abrir Jupyter Lab: http://localhost:8888
2. Navegar a `notebooks/01-getting-started.ipynb`
3. Ejecutar todas las celdas: Run → Run All Cells
4. Ver resultados inline

---

## 🔍 Debugging y Troubleshooting

### Ver Logs de Spark

```bash
# Logs del master
docker-compose logs spark-master

# Logs de workers
docker-compose logs spark-worker-1

# Logs de jupyter
docker-compose logs jupyter

# Logs en tiempo real
docker-compose logs -f --tail=100
```

### Acceder a Spark Shell

```bash
# PySpark shell
docker exec -it spark-master /opt/spark/bin/pyspark

# Spark SQL
docker exec -it spark-master /opt/spark/bin/spark-sql

# Scala shell
docker exec -it spark-master /opt/spark/bin/spark-shell
```

### Common Issues

**Error: "Container exited with code 137"**
```bash
# Out of memory - aumentar Docker memory
# Docker Desktop → Settings → Resources → Memory → 8GB+
```

**Error: "Address already in use"**
```bash
# Puerto ocupado - cambiar puerto
docker-compose down
# Editar docker-compose.yml ports: "8889:8888"
docker-compose up -d
```

**Error: "Permission denied" en /workspace**
```bash
# Fix permisos
docker exec -it spark-jupyter bash
sudo chown -R jovyan:users /home/jovyan/work
```

---

## 🧪 Testing Automatizado

### 1. Crear Script de Tests

`scripts/run-local-tests.sh`:

```bash
#!/bin/bash
set -e

echo "🚀 Ejecutando tests locales..."

# Generar datos
echo "📊 Generando datos de prueba..."
docker run -it --rm \
  -v $(pwd):/workspace \
  -w /workspace/data/generators \
  apache/spark:3.5.0-python3 \
  /opt/spark/bin/spark-submit generate_all.py \
  --size small \
  --output /workspace/testdata

# Ejecutar casos
echo "✅ Ejecutando casos..."
for case in 01-hints-parallel; do
  echo "  Testing case: $case"
  docker run -it --rm \
    -v $(pwd):/workspace \
    -w /workspace/cases/$case \
    apache/spark:3.5.0-python3 \
    /opt/spark/bin/spark-submit 3_pyspark.py \
    --input-path /workspace/testdata \
    --output-path /workspace/test-output/$case
done

echo "✅ Tests completados!"
```

### 2. Ejecutar Tests

```bash
chmod +x scripts/run-local-tests.sh
./scripts/run-local-tests.sh
```

---

## 📊 Performance Profiling Local

### 1. Habilitar Spark UI

```bash
# Spark UI está en http://localhost:4040 cuando hay job corriendo

# Para ver history de jobs terminados:
docker run -d --rm \
  -p 18080:18080 \
  -v $(pwd)/spark-events:/tmp/spark-events \
  --name spark-history \
  apache/spark:3.5.0 \
  /opt/spark/bin/spark-class org.apache.spark.deploy.history.HistoryServer
```

### 2. Configurar Logging

```bash
# Crear spark-defaults.conf
cat > conf/spark-defaults.conf << EOF
spark.eventLog.enabled=true
spark.eventLog.dir=/tmp/spark-events
spark.history.fs.logDirectory=/tmp/spark-events
spark.sql.adaptive.enabled=true
spark.sql.adaptive.coalescePartitions.enabled=true
EOF

# Montar en docker
docker run -it --rm \
  -v $(pwd):/workspace \
  -v $(pwd)/conf:/opt/spark/conf \
  -v $(pwd)/spark-events:/tmp/spark-events \
  apache/spark:3.5.0-python3 \
  /opt/spark/bin/spark-submit ...
```

---

## 💾 Persistir Datos entre Runs

### Usar Volumes

```bash
# Crear volume
docker volume create spark-data

# Usar volume
docker run -it --rm \
  -v spark-data:/data \
  -v $(pwd):/workspace \
  apache/spark:3.5.0-python3 \
  /opt/spark/bin/spark-submit \
  data/generators/generate_all.py \
  --output /data/bronze

# Verificar
docker run --rm -v spark-data:/data alpine ls -lh /data
```

---

## 🧹 Cleanup

```bash
# Detener containers
docker-compose down

# Eliminar containers y volúmenes
docker-compose down -v

# Eliminar datos de prueba
rm -rf testdata/ test-output/ spark-events/

# Limpiar imágenes Docker (opcional)
docker system prune -a
```

---

## 🎯 Workflow Recomendado

### Para Desarrollo de Casos

1. **Iterar rápido con Jupyter**:
   ```bash
   docker-compose up jupyter
   # Abrir notebook, editar, ejecutar celdas
   ```

2. **Validar con spark-submit**:
   ```bash
   docker exec spark-jupyter spark-submit 3_pyspark.py
   ```

3. **Commit cuando funcione**:
   ```bash
   git add cases/01-hints-parallel/3_pyspark.py
   git commit -m "Case 01: PySpark implementation"
   ```

### Para Testing

1. **Tests locales**:
   ```bash
   ./scripts/run-local-tests.sh
   ```

2. **Push a GitHub**:
   ```bash
   git push origin feature/case-01
   ```

3. **CI/CD valida automáticamente** (GitHub Actions)

4. **Deploy a cloud si tests pasan**

---

## 📚 Recursos

- [Docker Spark Images](https://hub.docker.com/r/apache/spark)
- [Jupyter Docker Stacks](https://jupyter-docker-stacks.readthedocs.io/)
- [Spark Standalone Mode](https://spark.apache.org/docs/latest/spark-standalone.html)

---

## ✅ Checklist

- [ ] Docker instalado y corriendo
- [ ] docker-compose.yml creado
- [ ] Cluster iniciado (master + workers)
- [ ] Jupyter accesible en localhost:8888
- [ ] Datos de prueba generados
- [ ] Caso 01 ejecutado exitosamente
- [ ] Spark UI accesible y muestra jobs
- [ ] Tests automatizados funcionando
