# Cloud Deployment Guide

Guía estratégica para deployment de Spark en AWS, Azure y GCP.

---

## 🌥️ Comparativa de Plataformas

| Aspecto | AWS | Azure | GCP |
|---------|-----|-------|-----|
| **Servicio Managed Spark** | EMR | Databricks / Synapse | Dataproc |
| **Serverless Option** | Glue | Synapse Serverless | Dataproc Serverless |
| **Storage Nativo** | S3 | ADLS Gen2 | GCS |
| **Data Warehouse** | Redshift | Synapse DW | BigQuery |
| **Lakehouse Format** | Delta/Iceberg/Hudi | Delta (Databricks native) | Iceberg/BigLake |
| **Notebooks** | EMR Notebooks, SageMaker | Databricks, Synapse Notebooks | Vertex AI, Dataproc Notebooks |
| **Precio Compute** | $$ | $$$ (Databricks premium) | $ (más económico) |
| **Madurez Spark** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ (Databricks) | ⭐⭐⭐⭐ |

---

## 🏗️ Arquitecturas de Referencia

### Arquitectura 1: Batch ETL (Común en migraciones Oracle)

```
┌──────────────┐
│ Oracle Exadata│
│  (source)     │
└──────┬────────┘
       │ CDC / Batch Export
       ▼
┌──────────────────────────────────────────┐
│  Landing Zone (Bronze)                    │
│  S3/ADLS/GCS: raw Parquet files          │
│  Partitioned by: load_date                │
└──────┬───────────────────────────────────┘
       │
       ▼  Spark Job (EMR/Databricks/Dataproc)
┌──────────────────────────────────────────┐
│  Silver Layer                             │
│  Cleansed, validated, deduplicated        │
│  Partitioned by: business_date            │
└──────┬───────────────────────────────────┘
       │
       ▼  Spark Aggregations
┌──────────────────────────────────────────┐
│  Gold Layer                               │
│  Business aggregations, Marts             │
│  Optimized for queries                    │
└──────┬───────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│  Consumption                              │
│  - BI Tools (Tableau, Power BI)          │
│  - Ad-hoc queries (SQL)                   │
│  - ML models                              │
└───────────────────────────────────────────┘
```

### Arquitectura 2: Real-time + Batch (Kappa Architecture)

```
┌──────────────┐         ┌──────────────┐
│ Oracle CDC   │         │ App Events   │
│ (GoldenGate) │         │ (API/Kafka)  │
└──────┬───────┘         └──────┬───────┘
       │                        │
       └────────┬───────────────┘
                │
                ▼
         ┌──────────────┐
         │ Kafka/Kinesis│
         │ EventHub     │
         └──────┬───────┘
                │
        ┌───────┴────────┐
        │                │
        ▼                ▼
┌────────────┐    ┌──────────────┐
│Spark       │    │ Cold Storage │
│Streaming   │    │ S3/ADLS/GCS  │
│(real-time) │    │ (batch)      │
└────┬───────┘    └──────┬───────┘
     │                   │
     └────────┬──────────┘
              │
              ▼
       ┌──────────────┐
       │ Delta/Iceberg│
       │ Unified View │
       └──────────────┘
```

---

## ☁️ AWS: Amazon EMR

### Cuándo usar EMR

✅ **Ventajas**:
- Control completo del cluster (versiones, configs, dependencies)
- Integración nativa con S3, Glue Catalog, Athena
- Costo eficiente (spot instances, autoscaling)
- Soporte para Hive, Presto, Flink, además de Spark

⚠️ **Desventajas**:
- Más operacional (gestión de clusters, upgrades)
- Notebooks menos potentes que Databricks
- Requiere más expertise de infraestructura

### Setup Recomendado

```bash
# Crear cluster EMR con Spark 3.5
aws emr create-cluster \
  --name "Oracle-Spark-Migration" \
  --release-label emr-7.0.0 \
  --applications Name=Spark Name=Hadoop Name=Hive Name=JupyterEnterpriseGateway \
  --instance-type r5.4xlarge \
  --instance-count 5 \
  --ec2-attributes KeyName=mykey,SubnetId=subnet-xxx \
  --use-default-roles \
  --configurations file://configs/spark-config.json \
  --bootstrap-actions Path=s3://bucket/bootstrap.sh \
  --auto-scaling-role EMR_AutoScaling_DefaultRole \
  --steps file://steps/initial-load.json
```

**spark-config.json**:
```json
[
  {
    "Classification": "spark-defaults",
    "Properties": {
      "spark.sql.adaptive.enabled": "true",
      "spark.sql.adaptive.coalescePartitions.enabled": "true",
      "spark.sql.adaptive.skewJoin.enabled": "true",
      "spark.sql.shuffle.partitions": "400",
      "spark.sql.files.maxPartitionBytes": "134217728",
      "spark.serializer": "org.apache.spark.serializer.KryoSerializer",
      "spark.dynamicAllocation.enabled": "true",
      "spark.shuffle.service.enabled": "true"
    }
  },
  {
    "Classification": "spark-hive-site",
    "Properties": {
      "hive.metastore.client.factory.class": "com.amazonaws.glue.catalog.metastore.AWSGlueDataCatalogHiveClientFactory"
    }
  }
]
```

### Arquitectura de Datos en S3

```
s3://company-datalake/
├── bronze/                    # Raw data from Oracle
│   ├── fact_sales/
│   │   └── load_date=2025-01-12/
│   │       └── part-00000.parquet
│   └── dim_region/
│       └── snapshot=2025-01-12/
├── silver/                    # Cleansed data
│   ├── fact_sales/
│   │   └── sale_date=2025-01-01/
│   │       └── part-00000.parquet
│   └── dim_region/
│       └── region_id=1/
├── gold/                      # Business aggregations
│   ├── sales_by_region_daily/
│   │   └── report_date=2025-01-12/
│   └── customer_360/
└── artifacts/                 # Scripts, JARs
    ├── jobs/
    │   └── case01_hints_parallel.py
    └── jars/
        └── spark-migration-cases.jar
```

### Cost Optimization

```bash
# Usar spot instances para core/task nodes
aws emr create-cluster \
  --instance-groups \
    InstanceGroupType=MASTER,InstanceType=r5.2xlarge,InstanceCount=1 \
    InstanceGroupType=CORE,InstanceType=r5.4xlarge,InstanceCount=2,BidPrice=OnDemandPrice \
    InstanceGroupType=TASK,InstanceType=r5.4xlarge,InstanceCount=8,BidPrice=0.40

# Autoscaling basado en YARN metrics
aws emr put-auto-scaling-policy \
  --cluster-id j-XXXXX \
  --instance-group-id ig-XXXXX \
  --auto-scaling-policy file://autoscaling-policy.json
```

---

## ☁️ Azure: Databricks

### Cuándo usar Databricks

✅ **Ventajas**:
- Notebooks colaborativos potentes (mejor experiencia de desarrollo)
- Delta Lake nativo (ACID, time travel, merge)
- Unity Catalog para governance
- Workflows integrados (orquestación)
- MLflow integrado para ML

⚠️ **Desventajas**:
- Más costoso (DBU + compute)
- Vendor lock-in parcial
- Menos control sobre infraestructura

### Setup Recomendado

```bash
# Crear workspace con Azure CLI
az databricks workspace create \
  --resource-group rg-spark-migration \
  --name spark-migration-workspace \
  --location eastus \
  --sku premium

# Configurar con Terraform (recomendado)
```

**Terraform ejemplo**:
```hcl
resource "azurerm_databricks_workspace" "main" {
  name                = "spark-migration-workspace"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "premium"
}

resource "databricks_cluster" "shared_autoscaling" {
  cluster_name            = "Oracle Migration Cluster"
  spark_version           = "14.3.x-scala2.12"  # Spark 3.5.0
  node_type_id            = "Standard_DS4_v2"
  autotermination_minutes = 20
  
  autoscale {
    min_workers = 2
    max_workers = 10
  }
  
  spark_conf = {
    "spark.databricks.delta.preview.enabled"          = "true"
    "spark.databricks.delta.optimizeWrite.enabled"    = "true"
    "spark.databricks.delta.autoCompact.enabled"      = "true"
    "spark.sql.adaptive.enabled"                      = "true"
  }
  
  library {
    maven {
      coordinates = "io.delta:delta-core_2.12:2.4.0"
    }
  }
}
```

### Delta Lake Best Practices

```python
# Crear tabla Delta con optimizaciones
spark.sql("""
    CREATE TABLE IF NOT EXISTS fact_sales_delta
    USING DELTA
    PARTITIONED BY (sale_date)
    LOCATION 'abfss://container@storage.dfs.core.windows.net/gold/fact_sales'
    TBLPROPERTIES (
      'delta.autoOptimize.optimizeWrite' = 'true',
      'delta.autoOptimize.autoCompact' = 'true',
      'delta.deletedFileRetentionDuration' = 'interval 7 days'
    )
    AS SELECT * FROM bronze.fact_sales
""")

# OPTIMIZE + ZORDER para queries frecuentes
spark.sql("""
    OPTIMIZE fact_sales_delta
    ZORDER BY (region_id, customer_id)
""")

# Time travel (audit)
spark.sql("""
    SELECT * FROM fact_sales_delta
    VERSION AS OF 10
    WHERE sale_date = '2025-01-12'
""")

# MERGE para SCD (upsert)
spark.sql("""
    MERGE INTO dim_customer_delta target
    USING staging_customers source
    ON target.customer_id = source.customer_id
    WHEN MATCHED THEN UPDATE SET *
    WHEN NOT MATCHED THEN INSERT *
""")
```

### Unity Catalog para Governance

```python
# Crear catálogo y esquemas
spark.sql("CREATE CATALOG IF NOT EXISTS oracle_migration")
spark.sql("USE CATALOG oracle_migration")
spark.sql("CREATE SCHEMA IF NOT EXISTS bronze")
spark.sql("CREATE SCHEMA IF NOT EXISTS silver")
spark.sql("CREATE SCHEMA IF NOT EXISTS gold")

# Permisos granulares
spark.sql("""
    GRANT SELECT ON SCHEMA oracle_migration.gold TO `analysts@company.com`
""")

spark.sql("""
    GRANT ALL PRIVILEGES ON SCHEMA oracle_migration.bronze TO `engineers@company.com`
""")
```

---

## ☁️ GCP: Dataproc

### Cuándo usar Dataproc

✅ **Ventajas**:
- Más económico que EMR/Databricks
- Rápido aprovisionamiento (< 90 segundos)
- Integración nativa con BigQuery
- Autoscaling potente
- Serverless option (Dataproc Serverless)

⚠️ **Desventajas**:
- Notebooks menos maduros
- Menos features de governance que Databricks
- Delta Lake requiere configuración adicional

### Setup Recomendado

```bash
# Crear cluster Dataproc
gcloud dataproc clusters create oracle-migration-cluster \
  --region=us-central1 \
  --zone=us-central1-a \
  --master-machine-type=n2-highmem-4 \
  --master-boot-disk-size=100 \
  --num-workers=4 \
  --worker-machine-type=n2-highmem-8 \
  --worker-boot-disk-size=100 \
  --image-version=2.1-debian11 \
  --optional-components=JUPYTER,ZEPPELIN \
  --enable-component-gateway \
  --autoscaling-policy=my-autoscaling-policy \
  --properties=spark:spark.sql.adaptive.enabled=true,spark:spark.sql.shuffle.partitions=400
```

**Autoscaling policy**:
```bash
gcloud dataproc autoscaling-policies import my-autoscaling-policy \
  --source=autoscaling-policy.yaml \
  --region=us-central1
```

**autoscaling-policy.yaml**:
```yaml
workerConfig:
  minInstances: 2
  maxInstances: 20
  weight: 1
secondaryWorkerConfig:
  minInstances: 0
  maxInstances: 50
  weight: 1
basicAlgorithm:
  yarnConfig:
    gracefulDecommissionTimeout: 1h
    scaleUpFactor: 1.0
    scaleDownFactor: 1.0
    scaleUpMinWorkerFraction: 0.0
    scaleDownMinWorkerFraction: 0.0
```

### Integración con BigQuery

```python
# Leer de BigQuery (pushdown de predicados)
df = spark.read \
    .format("bigquery") \
    .option("table", "project.dataset.oracle_exported_sales") \
    .option("filter", "sale_date >= '2025-01-01'") \
    .load()

# Procesar en Spark
result = df.filter(df.status == "ACTIVE") \
    .groupBy("region_id") \
    .agg({"amount": "sum"})

# Escribir a BigQuery
result.write \
    .format("bigquery") \
    .option("table", "project.dataset.sales_aggregated") \
    .option("temporaryGcsBucket", "temp-bucket") \
    .mode("overwrite") \
    .save()
```

### Dataproc Serverless (para jobs batch)

```bash
# No requiere cluster pre-existente
gcloud dataproc batches submit pyspark \
  gs://bucket/jobs/case01_hints_parallel.py \
  --region=us-central1 \
  --batch=case01-batch-$(date +%s) \
  --deps-bucket=gs://bucket/dependencies \
  --properties=spark.sql.adaptive.enabled=true \
  --service-account=spark-jobs@project.iam.gserviceaccount.com \
  -- --input gs://bucket/data/sales --output gs://bucket/results
```

---

## 🔄 Estrategia Multi-Cloud

### Cuándo considerar multi-cloud

✅ **Casos de uso**:
- Regulación (data residency)
- Disaster recovery
- Aprovechar servicios específicos de cada cloud
- Negociación de precios

### Arquitectura Portable

```python
# config.py - Abstracción de storage
import os
from enum import Enum

class CloudProvider(Enum):
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"

class StoragePaths:
    def __init__(self, provider: CloudProvider, bucket: str):
        self.provider = provider
        self.bucket = bucket
    
    @property
    def bronze_path(self):
        if self.provider == CloudProvider.AWS:
            return f"s3://{self.bucket}/bronze/"
        elif self.provider == CloudProvider.AZURE:
            return f"abfss://{self.bucket}@storage.dfs.core.windows.net/bronze/"
        elif self.provider == CloudProvider.GCP:
            return f"gs://{self.bucket}/bronze/"
    
    @property
    def silver_path(self):
        # Similar pattern
        pass

# Uso
provider = CloudProvider(os.getenv("CLOUD_PROVIDER", "aws"))
storage = StoragePaths(provider, "my-datalake")

df = spark.read.parquet(storage.bronze_path + "fact_sales")
```

---

## 📊 Comparativa de Costos (Estimado)

### Escenario: Procesamiento diario de 1TB

| Cloud | Servicio | Config | Costo/día | Costo/mes |
|-------|----------|--------|-----------|-----------|
| AWS | EMR | 10 x r5.4xlarge (16h) | $80 | $2,400 |
| AWS | Glue | 100 DPU-hours | $44 | $1,320 |
| Azure | Databricks | Standard, 10 workers | $120 | $3,600 |
| GCP | Dataproc | 10 x n2-highmem-8 (16h) | $60 | $1,800 |
| GCP | Dataproc Serverless | 100 DCU-hours | $40 | $1,200 |

**Notas**:
- Precios aproximados (2025)
- No incluye storage (S3/ADLS/GCS)
- Spot/preemptible puede reducir 60-80%
- Databricks incluye UI premium

---

## ✅ Checklist de Deployment

### Pre-deployment
- [ ] Storage account creado (S3/ADLS/GCS)
- [ ] IAM roles/service accounts configurados
- [ ] VPC/VNet/subnet configurados
- [ ] Data catalog setup (Glue/Hive/Unity)
- [ ] Secrets management (Secrets Manager/Key Vault)

### Deployment
- [ ] Cluster/workspace aprovisionado
- [ ] Spark configs optimizados
- [ ] Autoscaling configurado
- [ ] Monitoreo habilitado (CloudWatch/Monitor/Cloud Logging)
- [ ] Jobs desplegados
- [ ] Notebooks importados

### Post-deployment
- [ ] Smoke tests ejecutados
- [ ] Performance baseline establecido
- [ ] Alertas configuradas
- [ ] Documentación actualizada
- [ ] Team capacity training completado

---

## 📚 Recursos por Cloud

### AWS
- [EMR Best Practices](https://docs.aws.amazon.com/emr/latest/ManagementGuide/emr-plan.html)
- [Glue ETL Guide](https://docs.aws.amazon.com/glue/latest/dg/aws-glue-programming-etl-glue-arguments.html)
- [S3 Performance](https://docs.aws.amazon.com/AmazonS3/latest/userguide/optimizing-performance.html)

### Azure
- [Databricks Best Practices](https://docs.databricks.com/optimizations/index.html)
- [Delta Lake Guide](https://docs.databricks.com/delta/index.html)
- [Unity Catalog](https://docs.databricks.com/data-governance/unity-catalog/index.html)

### GCP
- [Dataproc Best Practices](https://cloud.google.com/dataproc/docs/guides)
- [BigQuery Spark Integration](https://cloud.google.com/dataproc/docs/tutorials/bigquery-connector-spark-example)
- [Dataproc Serverless](https://cloud.google.com/dataproc-serverless/docs)
