# Generadores de Datos de Prueba

Generadores de datos sintéticos para ejecutar todos los casos de migración.

---

## 🎯 Quick Start

### Opción 1: Generar Todo (Recomendado)

```bash
cd data/generators

# Dataset pequeño para testing local
python generate_all.py --size small --output /tmp/testdata

# Dataset mediano para desarrollo
python generate_all.py --size medium --output /tmp/testdata

# Dataset grande para testing de performance (cloud)
python generate_all.py --size large --output s3://bucket/bronze
```

### Opción 2: Generar Individualmente

```bash
# Solo fact_sales
python generate_fact_sales.py --rows 1000000 --output /tmp/fact_sales

# Solo dimensiones
python generate_dimensions.py --output /tmp/dimensions
```

---

## 📊 Datasets Generados

### fact_sales (Tabla de Hechos)

**Schema**:
```
sale_id          INT          - ID único de venta
sale_date        DATE         - Fecha de venta (columna de partición)
sale_timestamp   TIMESTAMP    - Timestamp exacto
amount           DECIMAL(10,2)- Monto de venta
customer_id      INT          - FK a dim_customer
region_id        INT          - FK a dim_region
product_id       INT          - FK a dim_product
store_id         INT          - FK a dim_store
status           STRING       - ACTIVE, PENDING, CANCELLED
discount_percent DECIMAL(5,2) - Porcentaje de descuento (0-30%)
payment_method   STRING       - CREDIT_CARD, DEBIT_CARD, CASH, WIRE_TRANSFER
net_amount       DECIMAL(10,2)- Monto neto después de descuento
```

**Características**:
- Particionado por `sale_date`
- Distribución log-normal de amounts (realista)
- Algunos customers son más frecuentes (power users)
- 85% ACTIVE, 10% PENDING, 5% CANCELLED
- Período: 2 años de datos (configurable)

**Tamaños**:
- **Small**: 10K rows (~1 MB)
- **Medium**: 1M rows (~100 MB)
- **Large**: 100M rows (~10 GB)
- **XLarge**: 1B rows (~100 GB)

---

### dim_region (Dimensión de Regiones)

**Schema**:
```
region_id     INT    - ID de región
region_name   STRING - Nombre de región
region_code   STRING - Código (NA, EU-W, APAC, etc.)
currency      STRING - Moneda (USD, EUR, AUD, INR)
country       STRING - País principal
is_active     BOOLEAN- Activo
created_date  DATE   - Fecha de creación
```

**Registros**: 10 regiones fijas

---

### dim_product (Dimensión de Productos)

**Schema**:
```
product_id      INT          - ID de producto
product_code    STRING       - Código (PROD-000001)
product_name    STRING       - Nombre descriptivo
category        STRING       - Categoría principal (10 categorías)
subcategory     STRING       - Subcategoría
unit_price      DECIMAL(10,2)- Precio unitario
stock_status    STRING       - IN_STOCK, LOW_STOCK, OUT_OF_STOCK
stock_quantity  INT          - Cantidad en stock
is_active       BOOLEAN      - Activo
created_date    DATE         - Fecha de creación
```

**Tamaños**:
- **Small**: 100 productos
- **Medium**: 1,000 productos
- **Large**: 5,000 productos
- **XLarge**: 10,000 productos

---

### dim_store (Dimensión de Tiendas)

**Schema**:
```
store_id       INT          - ID de tienda
store_code     STRING       - Código (STORE-0001)
store_name     STRING       - Nombre
store_type     STRING       - Flagship, Standard, Express, Online
region_id      INT          - FK a dim_region
address        STRING       - Dirección
city           STRING       - Ciudad
zipcode        STRING       - Código postal
square_feet    DECIMAL(10,2)- Superficie en pies cuadrados
employee_count INT          - Número de empleados
is_active      BOOLEAN      - Activo
opened_date    DATE         - Fecha de apertura
```

**Tamaños**:
- **Small**: 10 tiendas
- **Medium**: 100 tiendas
- **Large**: 500 tiendas
- **XLarge**: 1,000 tiendas

---

### dim_customer (Dimensión de Clientes)

**Schema**:
```
customer_id       INT    - ID de cliente
customer_code     STRING - Código (CUST-00000001)
first_name        STRING - Nombre
last_name         STRING - Apellido
full_name         STRING - Nombre completo
email             STRING - Email
phone             STRING - Teléfono
region_id         INT    - FK a dim_region
loyalty_tier      STRING - PLATINUM, GOLD, SILVER, BRONZE
loyalty_years     INT    - Años en programa de lealtad
status            STRING - ACTIVE, INACTIVE, SUSPENDED
registration_date DATE   - Fecha de registro
```

**Tamaños**:
- **Small**: 1,000 clientes
- **Medium**: 100,000 clientes
- **Large**: 1,000,000 clientes
- **XLarge**: 10,000,000 clientes

---

## 🔧 Configuración Avanzada

### Generar con Delta Lake

```bash
python generate_all.py \
  --size medium \
  --output /tmp/testdata \
  --format delta
```

### Generar solo fact_sales con período personalizado

```bash
python generate_fact_sales.py \
  --rows 5000000 \
  --output s3://bucket/fact_sales \
  --start-date 2023-01-01 \
  --days 1095 \
  --stats
```

### Generar dimensiones con tamaños específicos

```bash
python generate_dimensions.py \
  --output /tmp/dimensions \
  --products 5000 \
  --stores 200 \
  --customers 500000
```

---

## 📁 Estructura de Salida

```
output_path/
├── fact_sales/
│   ├── sale_date=2024-01-01/
│   │   ├── part-00000-xxx.snappy.parquet
│   │   └── part-00001-xxx.snappy.parquet
│   ├── sale_date=2024-01-02/
│   └── ...
├── dim_region/
│   └── part-00000-xxx.snappy.parquet
├── dim_product/
│   └── part-00000-xxx.snappy.parquet
├── dim_store/
│   └── part-00000-xxx.snappy.parquet
└── dim_customer/
    └── part-00000-xxx.snappy.parquet
```

---

## 🧪 Verificar Datos Generados

### Con PySpark

```python
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("Verify").getOrCreate()

# Leer fact_sales
sales = spark.read.parquet("/tmp/testdata/fact_sales")
print(f"Total sales: {sales.count():,}")
sales.show(10)

# Verificar particiones
sales.groupBy("sale_date").count().orderBy("sale_date").show()

# Leer dimensiones
regions = spark.read.parquet("/tmp/testdata/dim_region")
products = spark.read.parquet("/tmp/testdata/dim_product")
stores = spark.read.parquet("/tmp/testdata/dim_store")
customers = spark.read.parquet("/tmp/testdata/dim_customer")

print(f"Regions: {regions.count()}")
print(f"Products: {products.count()}")
print(f"Stores: {stores.count()}")
print(f"Customers: {customers.count()}")
```

### Con Spark SQL

```bash
pyspark --master local[*]
```

```sql
-- Crear tablas
CREATE TABLE fact_sales USING parquet LOCATION '/tmp/testdata/fact_sales';
CREATE TABLE dim_region USING parquet LOCATION '/tmp/testdata/dim_region';
CREATE TABLE dim_product USING parquet LOCATION '/tmp/testdata/dim_product';
CREATE TABLE dim_store USING parquet LOCATION '/tmp/testdata/dim_store';
CREATE TABLE dim_customer USING parquet LOCATION '/tmp/testdata/dim_customer';

-- Verificar
SELECT COUNT(*) FROM fact_sales;
SELECT * FROM dim_region;

-- Join de prueba
SELECT 
  r.region_name,
  COUNT(*) as sales_count,
  SUM(s.amount) as total_amount
FROM fact_sales s
JOIN dim_region r ON s.region_id = r.region_id
WHERE s.sale_date >= '2024-01-01'
GROUP BY r.region_name;
```

---

## 🚀 Ejecutar Casos con Datos Generados

Una vez generados los datos, puedes ejecutar cualquier caso:

```bash
# Configurar path de datos
export DATA_PATH=/tmp/testdata

# Ejecutar caso 01 (PySpark)
cd cases/01-hints-parallel
spark-submit 3_pyspark.py

# Ejecutar caso 02 (Scala)
cd cases/02-smart-scan-filter-pushdown
spark-submit --class Case02SmartScan --master local[*] 4_scala.jar
```

---

## 💾 Requisitos

```bash
# Python 3.8+
pip install pyspark==3.5.0

# Opcional: Delta Lake
pip install delta-spark==2.4.0

# Para cloud
# AWS: credenciales configuradas (AWS CLI)
# Azure: storage account key
# GCP: service account configurado
```

---

## 📊 Performance Tips

### Generar datos grandes en cloud

```bash
# Usar cluster Spark en lugar de local
spark-submit \
  --master yarn \
  --deploy-mode cluster \
  --num-executors 20 \
  --executor-memory 8g \
  generate_fact_sales.py \
  --size xlarge \
  --output s3://bucket/bronze/fact_sales
```

### Particionar apropiadamente

Para datasets muy grandes (>100GB), considera:
- Múltiples columnas de partición: `sale_date`, `region_id`
- Bucketing adicional por `customer_id`

---

## 🐛 Troubleshooting

### Error: "Out of Memory"

```bash
# Aumentar memoria del driver
export SPARK_DRIVER_MEMORY=8g
python generate_fact_sales.py ...
```

### Error: Permisos en S3/GCS/ADLS

```bash
# Verificar credenciales
aws s3 ls s3://bucket/  # AWS
gsutil ls gs://bucket/  # GCP
az storage blob list ...  # Azure
```

### Datos generados muy lentos

- Usa cluster con más workers
- Aumenta `spark.sql.shuffle.partitions`
- Para XLarge, considera generar en batches

---

## 📚 Schemas para Referencia

Ver `/data/schemas/` para definiciones JSON de esquemas que puedes usar en tus scripts.
