# Azure Databricks: Setup para Migración Oracle → Spark

Guía rápida para configurar Azure Databricks y ejecutar los casos de migración.

---

## 🎯 Overview

**Databricks** es la plataforma líder para Spark, con ventajas únicas:
- Notebooks colaborativos potentes
- Delta Lake nativo (ACID, time travel)
- Unity Catalog para governance
- MLflow integrado
- Workflows para orquestación

---

## 🚀 Quick Start (10 minutos)

### 1. Crear Workspace

**Portal Azure**:
1. Buscar "Azure Databricks"
2. Click "Create"
3. Configuración básica:
   - Subscription: Tu suscripción
   - Resource Group: rg-spark-migration
   - Workspace name: spark-migration-ws
   - Region: East US (o tu preferida)
   - Pricing tier: **Premium** (necesario para Unity Catalog)
4. Click "Review + Create"

**Azure CLI**:
```bash
az databricks workspace create \
  --resource-group rg-spark-migration \
  --name spark-migration-ws \
  --location eastus \
  --sku premium
```

### 2. Crear Cluster

1. Abrir workspace → Compute → Create Cluster
2. Configuración:
   - Cluster name: "Migration Cluster"
   - Cluster mode: Standard
   - Databricks runtime: **14.3 LTS** (Spark 3.5.0)
   - Node type: Standard_DS3_v2 (4 cores, 14GB)
   - Workers: Min 2, Max 8 (autoscaling)
   - Autotermination: 120 minutes

3. Spark Config (Advanced options):
```
spark.sql.adaptive.enabled true
spark.sql.adaptive.coalescePartitions.enabled true
spark.databricks.delta.optimizeWrite.enabled true
spark.databricks.delta.autoCompact.enabled true
```

4. Click "Create Cluster"

---

## 💾 Setup de Storage

### 1. Crear Storage Account

```bash
# Crear storage account
az storage account create \
  --name sparkmigrationdata \
  --resource-group rg-spark-migration \
  --location eastus \
  --sku Standard_LRS \
  --kind StorageV2 \
  --enable-hierarchical-namespace true

# Crear containers
az storage container create \
  --name bronze \
  --account-name sparkmigrationdata

az storage container create \
  --name silver \
  --account-name sparkmigrationdata

az storage container create \
  --name gold \
  --account-name sparkmigrationdata
```

### 2. Montar ADLS en Databricks

**Notebook cell**:
```python
# Configurar service principal (recomendado) o storage key
storage_account = "sparkmigrationdata"
container = "bronze"
tenant_id = "your-tenant-id"
client_id = "your-client-id"
client_secret = "your-client-secret"

# Montar usando service principal
configs = {
  "fs.azure.account.auth.type": "OAuth",
  "fs.azure.account.oauth.provider.type": "org.apache.hadoop.fs.azurebfs.oauth2.ClientCredsTokenProvider",
  "fs.azure.account.oauth2.client.id": client_id,
  "fs.azure.account.oauth2.client.secret": client_secret,
  "fs.azure.account.oauth2.client.endpoint": f"https://login.microsoftonline.com/{tenant_id}/oauth2/token"
}

dbutils.fs.mount(
  source = f"abfss://{container}@{storage_account}.dfs.core.windows.net/",
  mount_point = "/mnt/bronze",
  extra_configs = configs
)

# Verificar
display(dbutils.fs.ls("/mnt/bronze"))
```

---

## 📊 Ejecutar Casos

### 1. Importar Código

**Opción A: Via Repos (Recomendado)**

1. Workspace → Repos → Add Repo
2. Git URL: `https://github.com/tu-usuario/oracle-exadata-to-spark-migration`
3. Provider: GitHub
4. Click "Create Repo"

**Opción B: Upload directo**

1. Workspace → Create → Upload
2. Subir archivos `.py` de casos

### 2. Generar Datos

**Nuevo notebook**:
```python
%pip install -r /Workspace/Repos/migration/data/generators/requirements.txt

# Generar datos
%run /Workspace/Repos/migration/data/generators/generate_all.py --size medium --output /mnt/bronze
```

### 3. Ejecutar Caso 01

**Nuevo notebook: "Case 01: Hints & Parallel"**

```python
# Cell 1: Setup
from pyspark.sql.functions import sum as _sum, broadcast, col

# Cell 2: Leer datos
fact_sales = spark.read.parquet("/mnt/bronze/fact_sales")
dim_region = spark.read.parquet("/mnt/bronze/dim_region")

# Cell 3: Query Oracle original (comentado)
# SELECT /*+ PARALLEL(8) FULL(f) USE_HASH(d) */
#   d.region, SUM(f.amount) total
# FROM fact_sales f
# JOIN dim_region d ON d.region_id = f.region_id
# WHERE f.sale_date >= DATE '2025-01-01'
# GROUP BY d.region;

# Cell 4: Spark SQL
spark.sql("""
  SELECT /*+ BROADCAST(d) */
    d.region_name,
    SUM(f.amount) AS total
  FROM fact_sales f
  JOIN dim_region d ON d.region_id = f.region_id
  WHERE f.sale_date >= DATE '2025-01-01'
  GROUP BY d.region_name
  ORDER BY total DESC
""").display()

# Cell 5: DataFrame API
result = fact_sales \
    .filter(col("sale_date") >= "2025-01-01") \
    .join(broadcast(dim_region), "region_id") \
    .groupBy("region_name") \
    .agg(_sum("amount").alias("total")) \
    .orderBy(col("total").desc())

display(result)

# Cell 6: Plan de ejecución
result.explain(mode="formatted")

# Cell 7: Guardar resultado en Delta
result.write.format("delta").mode("overwrite").save("/mnt/gold/case01_result")
```

---

## 🏗️ Unity Catalog Setup

### 1. Habilitar Unity Catalog

1. Account Console → Metastores → Create Metastore
2. Asociar workspace

### 2. Crear Estructura de Catálogo

```sql
-- Cell en notebook
CREATE CATALOG IF NOT EXISTS oracle_migration;
USE CATALOG oracle_migration;

CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;

-- Crear tablas externas
CREATE TABLE bronze.fact_sales
USING DELTA
LOCATION '/mnt/bronze/fact_sales';

CREATE TABLE bronze.dim_region
USING DELTA
LOCATION '/mnt/bronze/dim_region';
```

### 3. Governance y Permisos

```sql
-- Permisos para analistas
GRANT SELECT ON SCHEMA oracle_migration.gold TO `analysts@company.com`;

-- Permisos para engineers
GRANT ALL PRIVILEGES ON SCHEMA oracle_migration.bronze TO `engineers@company.com`;
```

---

## 💰 Cost Optimization

### 1. Cluster Policies

**Admin Console → Compute → Cluster Policies**:

```json
{
  "spark_version": {
    "type": "fixed",
    "value": "14.3.x-scala2.12"
  },
  "node_type_id": {
    "type": "allowlist",
    "values": ["Standard_DS3_v2", "Standard_DS4_v2"]
  },
  "autotermination_minutes": {
    "type": "fixed",
    "value": 60
  },
  "spark_conf.spark.databricks.delta.optimizeWrite.enabled": {
    "type": "fixed",
    "value": "true"
  }
}
```

### 2. Jobs vs Interactive

- **Interactive notebooks**: $0.55/DBU (más caro)
- **Jobs compute**: $0.15/DBU (75% más barato)

**Usar Jobs para**:
- Generación de datos
- Pipelines de producción
- Validaciones automatizadas

### 3. Spot Instances

**En cluster config**:
- Worker type: Select "Spot" instances
- Ahorro: ~60-80%

---

## 📅 Workflows (Orchestration)

### 1. Crear Job

**Workflows → Create Job**:

1. Task 1: Generate Data
   - Type: Python
   - Source: `/Repos/migration/data/generators/generate_all.py`
   - Cluster: Job cluster (nuevo)
   
2. Task 2: Run Case 01
   - Type: Notebook
   - Path: `/Repos/migration/notebooks/case01.ipynb`
   - Depends on: Task 1

3. Task 3: Validate Results
   - Type: Python
   - Source: `/Repos/migration/templates/pyspark/validation.py`
   - Depends on: Task 2

### 2. Schedule

- Trigger: Scheduled
- Cron: `0 2 * * *` (diario a las 2 AM)
- Timezone: America/New_York

---

## 📊 Monitoreo

### 1. Spark UI

Disponible en cada notebook/job execution:
- Query plans
- Stage timelines
- Executor metrics

### 2. Query History

**SQL Warehouse → Query History**:
- Todas las queries ejecutadas
- Performance metrics
- Auto-optimization suggestions

### 3. System Tables (Unity Catalog)

```sql
-- Ver uso del cluster
SELECT * FROM system.compute.clusters
WHERE cluster_name = 'Migration Cluster';

-- Ver queries ejecutadas
SELECT * FROM system.query.history
WHERE user_email = current_user()
ORDER BY start_time DESC
LIMIT 100;
```

---

## ✅ Best Practices Databricks

### 1. Delta Lake Features

```python
# OPTIMIZE para compactar archivos pequeños
spark.sql("OPTIMIZE bronze.fact_sales")

# ZORDER para queries frecuentes
spark.sql("OPTIMIZE bronze.fact_sales ZORDER BY (region_id, sale_date)")

# VACUUM para limpiar archivos viejos
spark.sql("VACUUM bronze.fact_sales RETAIN 168 HOURS")

# Time travel
spark.sql("""
  SELECT * FROM bronze.fact_sales
  VERSION AS OF 10
  WHERE sale_date = '2025-01-01'
""")
```

### 2. Cache Optimization

```python
# Cache tabla en memoria
spark.sql("CACHE TABLE gold.sales_summary")

# Ver cached tables
spark.sql("SHOW TABLES IN global_temp").display()

# Limpiar cache
spark.sql("UNCACHE TABLE gold.sales_summary")
```

### 3. Secrets Management

```bash
# Databricks CLI
databricks secrets create-scope --scope migration-secrets

databricks secrets put --scope migration-secrets \
  --key oracle-connection-string

# Usar en notebook
oracle_conn = dbutils.secrets.get(scope="migration-secrets", key="oracle-connection-string")
```

---

## 🧹 Cleanup

```python
# Desmontar storage
dbutils.fs.unmount("/mnt/bronze")
dbutils.fs.unmount("/mnt/silver")
dbutils.fs.unmount("/mnt/gold")

# Eliminar tablas (Unity Catalog)
spark.sql("DROP SCHEMA oracle_migration.bronze CASCADE")

# Terminar cluster
# Se hace via UI: Compute → Terminate
```

---

## 📚 Recursos

- [Databricks Documentation](https://docs.databricks.com/)
- [Delta Lake Guide](https://docs.databricks.com/delta/index.html)
- [Unity Catalog](https://docs.databricks.com/data-governance/unity-catalog/index.html)
- [Spark Optimization](https://docs.databricks.com/optimizations/index.html)

---

## ✅ Checklist

- [ ] Workspace creado
- [ ] Cluster configurado con Spark 3.5
- [ ] Storage account + containers creados
- [ ] ADLS montado en Databricks
- [ ] Repos importado o código subido
- [ ] Datos de prueba generados
- [ ] Caso 01 ejecutado exitosamente
- [ ] Unity Catalog configurado (opcional)
- [ ] Job workflow creado (opcional)
- [ ] Políticas de cluster aplicadas
