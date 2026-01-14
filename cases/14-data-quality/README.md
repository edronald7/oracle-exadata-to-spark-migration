# Caso 14: Data Quality y Error Handling

**Criticidad**: ⭐⭐⭐⭐⭐ (MÁXIMA)  
**Frecuencia**: DIARIA - SIEMPRE hay datos corruptos  
**Complejidad**: Media-Alta

Aprende cómo manejar bad data, validar calidad, y configurar alertas.

---

## 🎯 Objetivo

**Realidad**: En producción, SIEMPRE hay:
- Registros corruptos (malformed JSON/CSV)
- Nulls inesperados
- Datos fuera de rango
- Duplicados
- Schema mismatches

**Necesitas**:
1. Detectar bad records automáticamente
2. Quarantine data mala
3. Validaciones de negocio
4. Alertas automáticas
5. Recovery procedures

---

## 📊 Comparativa de Enfoques

### 🔷 Oracle (Baseline)

```sql
-- Oracle: Validaciones con CASE/NVL
SELECT 
    customer_id,
    CASE 
        WHEN email IS NULL THEN 'INVALID_EMAIL'
        WHEN email NOT LIKE '%@%' THEN 'INVALID_EMAIL'
        ELSE 'VALID'
    END as validation_status,
    NVL(phone, 'UNKNOWN') as phone
FROM customers
WHERE validation_status = 'INVALID_EMAIL';

-- Limitación: Debe codificar todas las reglas en SQL
```

---

### ⚡ Spark SQL

**Archivo**: `2_sparksql.sql`

```sql
-- 1. Leer con manejo de bad records
CREATE OR REPLACE TEMP VIEW raw_data AS
SELECT *, _corrupt_record
FROM json.`s3://bucket/input/customers.json`
OPTIONS (
    mode = 'PERMISSIVE',
    columnNameOfCorruptRecord = '_corrupt_record'
);

-- 2. Separar buenos y malos registros
CREATE OR REPLACE TEMP VIEW good_records AS
SELECT * FROM raw_data WHERE _corrupt_record IS NULL;

CREATE OR REPLACE TEMP VIEW bad_records AS
SELECT * FROM raw_data WHERE _corrupt_record IS NOT NULL;

-- 3. Validaciones de negocio
CREATE OR REPLACE TEMP VIEW validated_records AS
SELECT 
    *,
    CASE 
        WHEN customer_id IS NULL THEN 'NULL_ID'
        WHEN email IS NULL OR email NOT LIKE '%@%' THEN 'INVALID_EMAIL'
        WHEN age < 0 OR age > 120 THEN 'INVALID_AGE'
        ELSE 'VALID'
    END as quality_status
FROM good_records;

-- 4. Insertar registros válidos
INSERT INTO customers_clean
SELECT * FROM validated_records WHERE quality_status = 'VALID';

-- 5. Quarantine registros inválidos
INSERT INTO quarantine_table
SELECT *, current_timestamp() as quarantined_at
FROM validated_records WHERE quality_status != 'VALID';

-- 6. Estadísticas
SELECT 
    COUNT(*) as total_records,
    SUM(CASE WHEN quality_status = 'VALID' THEN 1 ELSE 0 END) as valid,
    SUM(CASE WHEN quality_status != 'VALID' THEN 1 ELSE 0 END) as invalid,
    COUNT(DISTINCT quality_status) as validation_types
FROM validated_records;
```

---

### 💻 PySpark (Production-Grade con Great Expectations)

**Archivo**: `3_pyspark.py`

```python
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, count, lit, current_timestamp
from pyspark.sql.types import StringType
import great_expectations as ge
from typing import Dict, List

class DataQualityPipeline:
    '''
    Pipeline completo de data quality con:
    - Bad records handling
    - Business validations
    - Great Expectations
    - Quarantine tables
    - Alerting
    '''
    
    def __init__(self, spark: SparkSession):
        self.spark = spark
        self.quality_metrics = {}
    
    def read_with_bad_records_handling(
        self,
        path: str,
        format: str = 'json'
    ):
        '''Lee datos con manejo de registros corruptos'''
        print(f'📖 Reading {format} from {path}')
        
        # badRecordsPath guarda registros corruptos
        df = self.spark.read \\
            .format(format) \\
            .option('mode', 'PERMISSIVE') \\
            .option('columnNameOfCorruptRecord', '_corrupt_record') \\
            .option('badRecordsPath', '/quarantine/bad_records') \\
            .load(path)
        
        # Separar buenos y malos
        good_records = df.filter(col('_corrupt_record').isNull()) \\
            .drop('_corrupt_record')
        
        bad_records = df.filter(col('_corrupt_record').isNotNull())
        
        total = df.count()
        good_count = good_records.count()
        bad_count = bad_records.count()
        
        print(f'   Total: {total:,}')
        print(f'   Good: {good_count:,} ({good_count/total*100:.1f}%)')
        print(f'   Bad: {bad_count:,} ({bad_count/total*100:.1f}%)')
        
        self.quality_metrics['corrupt_records'] = bad_count
        
        if bad_count > 0:
            print(f'   ⚠️  {bad_count} corrupt records saved to /quarantine/bad_records')
            self.send_alert(f'Corrupt records detected: {bad_count}')
        
        return good_records, bad_records
    
    def apply_business_validations(
        self,
        df,
        rules: Dict[str, str]
    ):
        '''
        Aplica reglas de validación de negocio.
        
        Args:
            rules: Dict con nombre_regla: condición SQL
        
        Example:
            rules = {
                'valid_email': 'email IS NOT NULL AND email LIKE '%@%'',
                'valid_age': 'age >= 0 AND age <= 120',
                'valid_id': 'customer_id IS NOT NULL'
            }
        '''
        print(f'\\n✅ Applying {len(rules)} business rules...')
        
        # Crear columnas de validación
        for rule_name, condition in rules.items():
            df = df.withColumn(
                f'is_{rule_name}',
                when(expr(condition), lit(True)).otherwise(lit(False))
            )
        
        # Crear columna agregada de quality
        validation_cols = [f'is_{rule}' for rule in rules.keys()]
        
        # Record es válido si TODAS las reglas pasan
        all_valid_expr = ' AND '.join(validation_cols)
        df = df.withColumn('is_valid', expr(all_valid_expr))
        
        # Estadísticas
        valid_count = df.filter(col('is_valid')).count()
        invalid_count = df.filter(~col('is_valid')).count()
        
        print(f'   Valid: {valid_count:,}')
        print(f'   Invalid: {invalid_count:,}')
        
        # Por cada regla que falló
        for rule_name in rules.keys():
            failed = df.filter(~col(f'is_{rule_name}')).count()
            if failed > 0:
                print(f'   ⚠️  Rule '{rule_name}' failed: {failed:,} records')
        
        self.quality_metrics['validation_rules_failed'] = invalid_count
        
        return df
    
    def quarantine_invalid_records(
        self,
        df,
        quarantine_path: str
    ):
        '''Mueve registros inválidos a quarantine'''
        invalid_records = df.filter(~col('is_valid')) \\
            .withColumn('quarantined_at', current_timestamp()) \\
            .withColumn('reason', lit('business_validation_failed'))
        
        invalid_count = invalid_records.count()
        
        if invalid_count > 0:
            print(f'\\n📦 Quarantining {invalid_count:,} invalid records...')
            
            invalid_records.write \\
                .mode('append') \\
                .partitionBy('quarantined_at') \\
                .parquet(quarantine_path)
            
            print(f'   ✅ Saved to {quarantine_path}')
            
            self.send_alert(f'{invalid_count} records quarantined')
        
        return invalid_count
    
    def validate_with_great_expectations(
        self,
        df,
        expectations: List[Dict]
    ):
        '''
        Validar con Great Expectations.
        
        Example:
            expectations = [
                {'column': 'customer_id', 'expectation': 'expect_column_values_to_be_unique'},
                {'column': 'email', 'expectation': 'expect_column_values_to_not_be_null'},
                {'column': 'age', 'expectation': 'expect_column_values_to_be_between', 'min': 0, 'max': 120}
            ]
        '''
        print(f'\\n🔍 Running Great Expectations validations...')
        
        # Convert to Pandas for GE (or use GE Spark backend)
        ge_df = ge.dataset.SparkDFDataset(df)
        
        results = []
        for exp in expectations:
            column = exp['column']
            expectation_type = exp['expectation']
            
            if expectation_type == 'expect_column_values_to_be_unique':
                result = ge_df.expect_column_values_to_be_unique(column)
            elif expectation_type == 'expect_column_values_to_not_be_null':
                result = ge_df.expect_column_values_to_not_be_null(column)
            elif expectation_type == 'expect_column_values_to_be_between':
                result = ge_df.expect_column_values_to_be_between(
                    column, 
                    min_value=exp['min'], 
                    max_value=exp['max']
                )
            
            results.append(result)
            
            if result.success:
                print(f'   ✅ {expectation_type} on {column}: PASSED')
            else:
                print(f'   ❌ {expectation_type} on {column}: FAILED')
                self.send_alert(f'GE validation failed: {expectation_type} on {column}')
        
        return results
    
    def send_alert(self, message: str):
        '''Envía alerta (Slack, PagerDuty, Email, etc.)'''
        # En producción: integrar con Slack, PagerDuty, SNS, etc.
        print(f'\\n🚨 ALERT: {message}')
        
        # Ejemplo: Slack webhook
        # import requests
        # webhook_url = 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
        # payload = {'text': f'Data Quality Alert: {message}'}
        # requests.post(webhook_url, json=payload)
    
    def generate_quality_report(self):
        '''Genera reporte de calidad'''
        print('\\n' + '='*60)
        print('📊 DATA QUALITY REPORT')
        print('='*60)
        
        for metric, value in self.quality_metrics.items():
            print(f'   {metric}: {value:,}')
        
        # Calcular score
        total_issues = sum(self.quality_metrics.values())
        if total_issues == 0:
            print('\\n   ✅ ALL QUALITY CHECKS PASSED')
        else:
            print(f'\\n   ⚠️  {total_issues:,} total quality issues')


def main():
    spark = SparkSession.builder \\
        .appName('Data Quality Pipeline') \\
        .getOrCreate()
    
    pipeline = DataQualityPipeline(spark)
    
    # 1. Leer con bad records handling
    good_df, bad_df = pipeline.read_with_bad_records_handling(
        's3://bucket/input/customers.json',
        format='json'
    )
    
    # 2. Aplicar validaciones de negocio
    validation_rules = {
        'valid_email': 'email IS NOT NULL AND email LIKE '%@%'',
        'valid_age': 'age >= 0 AND age <= 120',
        'valid_id': 'customer_id IS NOT NULL',
        'valid_phone': 'phone IS NOT NULL AND length(phone) >= 10'
    }
    
    validated_df = pipeline.apply_business_validations(good_df, validation_rules)
    
    # 3. Quarantine invalid
    pipeline.quarantine_invalid_records(
        validated_df,
        's3://bucket/quarantine/customers'
    )
    
    # 4. Great Expectations
    expectations = [
        {'column': 'customer_id', 'expectation': 'expect_column_values_to_be_unique'},
        {'column': 'email', 'expectation': 'expect_column_values_to_not_be_null'},
        {'column': 'age', 'expectation': 'expect_column_values_to_be_between', 'min': 0, 'max': 120}
    ]
    
    pipeline.validate_with_great_expectations(validated_df, expectations)
    
    # 5. Escribir registros limpios
    clean_df = validated_df.filter(col('is_valid')).drop('is_valid')
    
    clean_df.write \\
        .mode('overwrite') \\
        .parquet('s3://bucket/clean/customers')
    
    # 6. Reporte
    pipeline.generate_quality_report()
    
    spark.stop()


if __name__ == '__main__':
    main()
```

---

## 💡 Best Practices

### ✅ DO's

1. **Siempre usar badRecordsPath**: Nunca perder datos
2. **Quarantine tables**: Separate bad data para análisis
3. **Alertas automáticas**: Notificar cuando calidad baja
4. **Métricas**: Track data quality over time
5. **Idempotencia**: Pipeline debe ser re-ejecutable

### ❌ DON'Ts

1. ❌ Fallar pipeline por un bad record
2. ❌ Ignorar corrupt records
3. ❌ No alertar sobre quality issues
4. ❌ Validar después de procesar (validar temprano)
5. ❌ No documentar reglas de validación

---

## 📊 Monitoring Dashboard

```sql
-- Query para dashboard de data quality
SELECT 
    DATE(processing_date) as date,
    source_system,
    COUNT(*) as total_records,
    SUM(CASE WHEN is_valid THEN 1 ELSE 0 END) as valid_records,
    SUM(CASE WHEN NOT is_valid THEN 1 ELSE 0 END) as invalid_records,
    ROUND(SUM(CASE WHEN is_valid THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as quality_percentage
FROM data_quality_log
GROUP BY DATE(processing_date), source_system
ORDER BY date DESC, source_system;
```

---

## 🔗 Ver También

- **Caso 13**: CDC - Validar CDC data
- **Caso 16**: Orchestration - Alerting integration
- **templates/pyspark/validation.py**: Validation utilities

---

**Próximo**: Caso 15 - Spark Structured Streaming
