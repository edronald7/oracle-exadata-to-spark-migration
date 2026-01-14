# AWS EMR: Setup Completo para Migración Oracle → Spark

Guía paso a paso para configurar Amazon EMR para ejecutar los casos de migración.

---

## 🎯 Overview

**EMR (Elastic MapReduce)** es el servicio managed de Spark en AWS. Ventajas:
- Control completo del cluster
- Integración nativa con S3, Glue Catalog, Athena
- Cost-effective con spot instances
- Soporte para múltiples frameworks (Spark, Hive, Presto, Flink)

---

## 📋 Prerequisites

```bash
# 1. AWS CLI instalado y configurado
aws --version
aws configure list

# 2. Permisos IAM necesarios
# - AmazonEMRFullAccessPolicy
# - AmazonS3FullAccess (o específico)
# - AmazonEC2FullAccess

# 3. Key pair para SSH
aws ec2 create-key-pair \
  --key-name spark-migration-key \
  --query 'KeyMaterial' \
  --output text > ~/.ssh/spark-migration-key.pem
chmod 400 ~/.ssh/spark-migration-key.pem
```

---

## 🚀 Quick Start (5 minutos)

### Opción 1: Cluster básico para desarrollo

```bash
aws emr create-cluster \
  --name "Spark-Migration-Dev" \
  --release-label emr-7.0.0 \
  --applications Name=Spark Name=Hadoop Name=JupyterEnterpriseGateway \
  --instance-type m5.xlarge \
  --instance-count 3 \
  --ec2-attributes KeyName=spark-migration-key \
  --use-default-roles

# Obtener cluster ID
CLUSTER_ID=$(aws emr list-clusters --active --query 'Clusters[0].Id' --output text)
echo "Cluster ID: $CLUSTER_ID"

# Monitorear estado
aws emr describe-cluster --cluster-id $CLUSTER_ID \
  --query 'Cluster.Status.State' \
  --output text

# Esperar a que esté WAITING
aws emr wait cluster-running --cluster-id $CLUSTER_ID
```

### Opción 2: Usando AWS Console

1. Ir a [EMR Console](https://console.aws.amazon.com/emr)
2. Click "Create cluster"
3. Quick options:
   - Release: emr-7.0.0 (Spark 3.5.0)
   - Instance type: m5.xlarge
   - Number of instances: 3 (1 master + 2 core)
4. Launch cluster

---

## ⚙️ Configuración Avanzada (Production)

### 1. Crear Bucket S3

```bash
# Crear bucket para datos y logs
BUCKET_NAME="spark-migration-$(aws sts get-caller-identity --query Account --output text)"
REGION="us-east-1"

aws s3 mb s3://$BUCKET_NAME --region $REGION

# Estructura de directorios
aws s3api put-object --bucket $BUCKET_NAME --key bronze/
aws s3api put-object --bucket $BUCKET_NAME --key silver/
aws s3api put-object --bucket $BUCKET_NAME --key gold/
aws s3api put-object --bucket $BUCKET_NAME --key scripts/
aws s3api put-object --bucket $BUCKET_NAME --key logs/
```

### 2. Subir Scripts y Datos

```bash
# Subir generadores
cd data/generators
aws s3 cp generate_all.py s3://$BUCKET_NAME/scripts/
aws s3 cp generate_fact_sales.py s3://$BUCKET_NAME/scripts/
aws s3 cp generate_dimensions.py s3://$BUCKET_NAME/scripts/

# Subir casos
cd ../../cases
for case in 01-hints-parallel 02-smart-scan-filter-pushdown; do
  aws s3 cp $case/3_pyspark.py s3://$BUCKET_NAME/scripts/$case/
done
```

### 3. Configuración de Spark (spark-config.json)

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
      "spark.shuffle.service.enabled": "true",
      "spark.sql.parquet.compression.codec": "snappy",
      "spark.sql.autoBroadcastJoinThreshold": "10485760"
    }
  },
  {
    "Classification": "spark-hive-site",
    "Properties": {
      "hive.metastore.client.factory.class": "com.amazonaws.glue.catalog.metastore.AWSGlueDataCatalogHiveClientFactory"
    }
  },
  {
    "Classification": "spark-env",
    "Configurations": [
      {
        "Classification": "export",
        "Properties": {
          "PYSPARK_PYTHON": "/usr/bin/python3",
          "SPARK_HOME": "/usr/lib/spark"
        }
      }
    ]
  }
]
```

Guardar como `configs/spark-config.json` y subir:

```bash
aws s3 cp configs/spark-config.json s3://$BUCKET_NAME/configs/
```

### 4. Bootstrap Script (Opcional)

```bash
#!/bin/bash
# bootstrap.sh - Instala dependencias adicionales

set -e

# Instalar librerías Python
sudo python3 -m pip install --upgrade pip
sudo python3 -m pip install delta-spark==2.4.0
sudo python3 -m pip install pyarrow

# Configurar timezone
sudo timedatectl set-timezone America/New_York

echo "✅ Bootstrap completado"
```

Subir:
```bash
aws s3 cp scripts/bootstrap.sh s3://$BUCKET_NAME/scripts/
```

### 5. Crear Cluster Production

```bash
aws emr create-cluster \
  --name "Spark-Migration-Production" \
  --release-label emr-7.0.0 \
  --applications Name=Spark Name=Hadoop Name=Hive Name=JupyterEnterpriseGateway \
  --ec2-attributes '{
    "KeyName": "spark-migration-key",
    "InstanceProfile": "EMR_EC2_DefaultRole",
    "SubnetId": "subnet-xxxxx",
    "EmrManagedMasterSecurityGroup": "sg-xxxxx",
    "EmrManagedSlaveSecurityGroup": "sg-xxxxx"
  }' \
  --instance-groups '[
    {
      "Name": "Master",
      "InstanceRole": "MASTER",
      "InstanceType": "r5.4xlarge",
      "InstanceCount": 1,
      "EbsConfiguration": {
        "EbsBlockDeviceConfigs": [{
          "VolumeSpecification": {
            "VolumeType": "gp3",
            "SizeInGB": 100
          },
          "VolumesPerInstance": 1
        }]
      }
    },
    {
      "Name": "Core",
      "InstanceRole": "CORE",
      "InstanceType": "r5.4xlarge",
      "InstanceCount": 4,
      "EbsConfiguration": {
        "EbsBlockDeviceConfigs": [{
          "VolumeSpecification": {
            "VolumeType": "gp3",
            "SizeInGB": 200
          },
          "VolumesPerInstance": 2
        }]
      },
      "AutoScalingPolicy": {
        "Constraints": {
          "MinCapacity": 2,
          "MaxCapacity": 10
        },
        "Rules": [{
          "Name": "ScaleOutOnYARNMemory",
          "Action": {
            "SimpleScalingPolicyConfiguration": {
              "AdjustmentType": "CHANGE_IN_CAPACITY",
              "ScalingAdjustment": 2,
              "CoolDown": 300
            }
          },
          "Trigger": {
            "CloudWatchAlarmDefinition": {
              "ComparisonOperator": "GREATER_THAN",
              "EvaluationPeriods": 1,
              "MetricName": "YARNMemoryAvailablePercentage",
              "Period": 300,
              "Threshold": 75.0,
              "Statistic": "AVERAGE",
              "Unit": "PERCENT"
            }
          }
        }]
      }
    }
  ]' \
  --configurations file://configs/spark-config.json \
  --bootstrap-actions Path=s3://$BUCKET_NAME/scripts/bootstrap.sh \
  --log-uri s3://$BUCKET_NAME/logs/ \
  --service-role EMR_DefaultRole \
  --enable-debugging \
  --auto-termination-policy IdleTimeout=3600

CLUSTER_ID=$(aws emr list-clusters --active --query 'Clusters[0].Id' --output text)
echo "✅ Cluster creado: $CLUSTER_ID"
```

---

## 📊 Ejecutar Casos de Migración

### 1. Generar Datos de Prueba

```bash
# Step para generar datos
aws emr add-steps \
  --cluster-id $CLUSTER_ID \
  --steps Type=Spark,Name="Generate Test Data",\
ActionOnFailure=CONTINUE,\
Args=[s3://$BUCKET_NAME/scripts/generate_all.py,\
--size,medium,\
--output,s3://$BUCKET_NAME/bronze,\
--format,parquet]

# Monitorear step
STEP_ID=$(aws emr list-steps --cluster-id $CLUSTER_ID \
  --query 'Steps[0].Id' --output text)

aws emr describe-step --cluster-id $CLUSTER_ID --step-id $STEP_ID \
  --query 'Step.Status.State' --output text
```

### 2. Ejecutar Caso 01 (PySpark)

```bash
aws emr add-steps \
  --cluster-id $CLUSTER_ID \
  --steps Type=Spark,Name="Case 01: Hints Parallel",\
ActionOnFailure=CONTINUE,\
Args=[s3://$BUCKET_NAME/scripts/01-hints-parallel/3_pyspark.py,\
--input-path,s3://$BUCKET_NAME/bronze,\
--output-path,s3://$BUCKET_NAME/gold/case01]
```

### 3. Ejecutar Caso 02 (PySpark)

```bash
aws emr add-steps \
  --cluster-id $CLUSTER_ID \
  --steps Type=Spark,Name="Case 02: Smart Scan",\
ActionOnFailure=CONTINUE,\
Args=[s3://$BUCKET_NAME/scripts/02-smart-scan-filter-pushdown/3_pyspark.py,\
--input-path,s3://$BUCKET_NAME/bronze,\
--output-path,s3://$BUCKET_NAME/gold/case02]
```

### 4. Ejecutar Caso Scala (después de compilar)

```bash
# Subir JAR compilado
aws s3 cp target/scala-2.12/spark-migration-cases.jar \
  s3://$BUCKET_NAME/jars/

# Ejecutar
aws emr add-steps \
  --cluster-id $CLUSTER_ID \
  --steps Type=Spark,Name="Case 01: Scala",\
ActionOnFailure=CONTINUE,\
Args=[--class,com.migration.cases.Case01HintsParallel,\
s3://$BUCKET_NAME/jars/spark-migration-cases.jar,\
s3://$BUCKET_NAME/bronze,\
s3://$BUCKET_NAME/gold/case01_scala]
```

---

## 💻 Acceso al Cluster

### 1. SSH al Master Node

```bash
# Obtener DNS del master
MASTER_DNS=$(aws emr describe-cluster --cluster-id $CLUSTER_ID \
  --query 'Cluster.MasterPublicDnsName' --output text)

# Conectar
ssh -i ~/.ssh/spark-migration-key.pem hadoop@$MASTER_DNS

# Una vez dentro
spark-submit --version
pyspark
```

### 2. Spark UI (Port Forwarding)

```bash
# Crear túnel SSH
ssh -i ~/.ssh/spark-migration-key.pem \
  -L 8088:localhost:8088 \
  -L 18080:localhost:18080 \
  hadoop@$MASTER_DNS

# Abrir en browser
open http://localhost:8088  # YARN ResourceManager
open http://localhost:18080 # Spark History Server
```

### 3. EMR Notebooks (Recomendado)

```bash
# Crear workspace de EMR Studio
aws emr create-studio \
  --name "Spark Migration Studio" \
  --auth-mode IAM \
  --vpc-id vpc-xxxxx \
  --subnet-ids subnet-xxxxx \
  --service-role EMRStudio_Service_Role \
  --user-role EMRStudio_User_Role \
  --workspace-security-group-id sg-xxxxx

# Attachar cluster al notebook
# Se hace via console: EMR Studio → Workspaces → Attach cluster
```

---

## 💰 Cost Optimization

### 1. Usar Spot Instances

```bash
aws emr create-cluster \
  --name "Spark-Migration-Spot" \
  --instance-fleets '[
    {
      "Name": "Master",
      "InstanceFleetType": "MASTER",
      "TargetOnDemandCapacity": 1,
      "InstanceTypeConfigs": [{
        "InstanceType": "r5.2xlarge"
      }]
    },
    {
      "Name": "Core",
      "InstanceFleetType": "CORE",
      "TargetOnDemandCapacity": 2,
      "TargetSpotCapacity": 8,
      "InstanceTypeConfigs": [
        {
          "InstanceType": "r5.4xlarge",
          "BidPriceAsPercentageOfOnDemandPrice": 100
        },
        {
          "InstanceType": "r5.2xlarge",
          "BidPriceAsPercentageOfOnDemandPrice": 100
        }
      ]
    }
  ]' \
  ...
```

**Ahorros**: 60-80% en core/task nodes

### 2. Auto-termination

```bash
# Cluster se termina después de 1 hora idle
--auto-termination-policy IdleTimeout=3600
```

### 3. S3 Lifecycle Policies

```bash
# Configurar lifecycle para logs
aws s3api put-bucket-lifecycle-configuration \
  --bucket $BUCKET_NAME \
  --lifecycle-configuration '{
    "Rules": [{
      "Id": "DeleteOldLogs",
      "Status": "Enabled",
      "Prefix": "logs/",
      "Expiration": {
        "Days": 30
      }
    }]
  }'
```

---

## 📊 Monitoreo y Troubleshooting

### CloudWatch Metrics

```bash
# Ver métricas del cluster
aws cloudwatch get-metric-statistics \
  --namespace AWS/ElasticMapReduce \
  --metric-name IsIdle \
  --dimensions Name=JobFlowId,Value=$CLUSTER_ID \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average
```

### Ver Logs de Step

```bash
# Listar steps
aws emr list-steps --cluster-id $CLUSTER_ID

# Ver logs de step específico
aws s3 ls s3://$BUCKET_NAME/logs/$CLUSTER_ID/steps/$STEP_ID/

# Descargar logs
aws s3 cp s3://$BUCKET_NAME/logs/$CLUSTER_ID/steps/$STEP_ID/stderr.gz - | gunzip
```

### Debugging Común

**Error: "Cluster terminado con error"**
```bash
# Ver reason
aws emr describe-cluster --cluster-id $CLUSTER_ID \
  --query 'Cluster.Status.StateChangeReason'
```

**Error: "Out of Memory"**
```bash
# Aumentar memoria executor
--conf spark.executor.memory=16g \
--conf spark.driver.memory=8g
```

---

## 🧹 Cleanup

```bash
# Terminar cluster
aws emr terminate-clusters --cluster-ids $CLUSTER_ID

# Eliminar datos de prueba (CUIDADO!)
aws s3 rm s3://$BUCKET_NAME/bronze --recursive
aws s3 rm s3://$BUCKET_NAME/silver --recursive
aws s3 rm s3://$BUCKET_NAME/gold --recursive

# Eliminar logs antiguos
aws s3 rm s3://$BUCKET_NAME/logs --recursive
```

---

## 📚 Recursos Adicionales

- [EMR Best Practices](https://docs.aws.amazon.com/emr/latest/ManagementGuide/emr-plan.html)
- [EMR Pricing Calculator](https://calculator.aws/#/addService/EMR)
- [Spark Configuration Guide](https://spark.apache.org/docs/latest/configuration.html)
- [AWS Glue Catalog](https://docs.aws.amazon.com/glue/latest/dg/populate-data-catalog.html)

---

## ✅ Checklist

- [ ] AWS CLI configurado
- [ ] Key pair creado
- [ ] S3 bucket creado
- [ ] Scripts subidos a S3
- [ ] Cluster EMR creado
- [ ] Datos de prueba generados
- [ ] Casos ejecutados exitosamente
- [ ] Resultados validados
- [ ] Cluster terminado (o auto-termination configurado)
