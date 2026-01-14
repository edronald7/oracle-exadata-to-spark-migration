# Caso 16: Orquestación con Airflow

**Criticidad**: ⭐⭐⭐⭐⭐ (CRÍTICA)  
**Frecuencia**: Setup + mantenimiento continuo  

Nadie ejecuta Spark manualmente en producción. Necesitas orquestación.

---

## 🎯 Opciones de Orquestación

| Tool | Pros | Contras | Cuándo Usar |
|------|------|---------|-------------|
| **Airflow** | Open source, flexible, gran comunidad | Requiere infraestructura | AWS/GCP/on-prem |
| **Databricks Workflows** | Integrado, simple | Vendor lock-in | Azure Databricks |
| **AWS Step Functions** | Serverless, AWS-native | Limited para Spark | AWS serverless |
| **Prefect** | Moderno, Pythonic | Menos maduro | Equipos Python |

---

## 💻 Ejemplo: Airflow DAG

```python
from airflow import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.providers.amazon.aws.sensors.s3 import S3KeySensor
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'data-team',
    'depends_on_past': False,
    'start_date': datetime(2026, 1, 1),
    'email': ['alerts@company.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5)
}

with DAG(
    'daily_customer_etl',
    default_args=default_args,
    schedule_interval='0 2 * * *',  # 2 AM daily
    catchup=False,
    tags=['production', 'customers']
) as dag:
    
    # 1. Sensor: esperar datos nuevos
    wait_for_data = S3KeySensor(
        task_id='wait_for_oracle_export',
        bucket_name='data-lake',
        bucket_key='bronze/customers/date={{ ds }}/*',
        timeout=3600,
        poke_interval=60
    )
    
    # 2. CDC Ingestion
    ingest_cdc = SparkSubmitOperator(
        task_id='ingest_cdc',
        application='s3://scripts/cases/13-cdc-incremental/3_pyspark.py',
        conf={
            'spark.sql.adaptive.enabled': 'true',
            'spark.sql.shuffle.partitions': '400'
        },
        application_args=[
            '--date', '{{ ds }}',
            '--source', 's3://data-lake/bronze/customers',
            '--target', 's3://data-lake/silver/customers'
        ]
    )
    
    # 3. Data Quality
    validate_data = SparkSubmitOperator(
        task_id='validate_data_quality',
        application='s3://scripts/cases/14-data-quality/3_pyspark.py',
        application_args=['--input', 's3://data-lake/silver/customers']
    )
    
    # 4. Aggregations
    compute_aggregates = SparkSubmitOperator(
        task_id='compute_aggregates',
        application='s3://scripts/aggregations/customer_summary.py',
        application_args=[
            '--input', 's3://data-lake/silver/customers',
            '--output', 's3://data-lake/gold/customer_summary'
        ]
    )
    
    # 5. Alert on success
    def send_success_notification(**context):
        print(f'✅ Pipeline completed for {context['ds']}')
        # Slack/Email notification
    
    notify_success = PythonOperator(
        task_id='notify_success',
        python_callable=send_success_notification
    )
    
    # Dependencies
    wait_for_data >> ingest_cdc >> validate_data >> compute_aggregates >> notify_success
```

---

## ✅ Best Practices

1. **Idempotencia**: DAGs deben ser re-ejecutables
2. **Sensors**: Esperar data en vez de schedule fijo
3. **Retries**: Configurar retries con backoff
4. **Alerting**: Email/Slack en failures
5. **Monitoring**: Dashboards de DAG runs

---

## 📚 Recursos

- [Airflow Docs](https://airflow.apache.org/)
- [Databricks Workflows](https://docs.databricks.com/workflows/)
