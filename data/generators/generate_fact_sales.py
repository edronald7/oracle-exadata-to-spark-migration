"""
Generador de datos para fact_sales
Genera registros sintéticos de ventas particionados por fecha.

Uso:
    python generate_fact_sales.py --rows 1000000 --output /tmp/fact_sales
    python generate_fact_sales.py --rows 100000000 --output s3://bucket/bronze/fact_sales --size large
"""

import argparse
from datetime import date, timedelta
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, expr, date_add, lit, rand, when,
    date_format, concat_ws
)
from pyspark.sql.types import (
    StructType, StructField, IntegerType, DateType, 
    DecimalType, StringType, TimestampType
)

def create_spark_session(app_name="Generate Fact Sales"):
    """Crea SparkSession con configuraciones optimizadas"""
    return SparkSession.builder \
        .appName(app_name) \
        .config("spark.sql.shuffle.partitions", "200") \
        .config("spark.sql.adaptive.enabled", "true") \
        .getOrCreate()

def generate_fact_sales(spark, num_rows, start_date="2024-01-01", days=730):
    """
    Genera fact_sales con distribución realista
    
    Args:
        spark: SparkSession
        num_rows: Número de filas a generar
        start_date: Fecha inicial (default: 2024-01-01)
        days: Días de datos (default: 730 = 2 años)
    
    Returns:
        DataFrame con fact_sales
    """
    print(f"📊 Generando {num_rows:,} registros de ventas...")
    print(f"📅 Período: {start_date} + {days} días")
    
    # Generar IDs base
    df = spark.range(0, num_rows)
    
    # Crear fact_sales con distribución realista
    df = df.selectExpr(
        "id as sale_id",
        
        # Fecha: distribución uniforme en el período
        f"date_add('{start_date}', cast(rand() * {days} as int)) as sale_date",
        
        # Timestamp con hora del día (weighted hacia horas laborales)
        f"""timestamp(concat(
            date_add('{start_date}', cast(rand() * {days} as int)),
            ' ',
            lpad(cast(case 
                when rand() < 0.7 then 8 + cast(rand() * 10 as int)
                else cast(rand() * 24 as int)
            end as string), 2, '0'),
            ':',
            lpad(cast(rand() * 60 as int) as string, 2, '0'),
            ':',
            lpad(cast(rand() * 60 as int) as string, 2, '0')
        )) as sale_timestamp""",
        
        # Amount: distribución log-normal (muchos valores bajos, pocos altos)
        """cast(
            case 
                when rand() < 0.6 then 10 + rand() * 90  
                when rand() < 0.9 then 100 + rand() * 900
                else 1000 + rand() * 9000
            end as decimal(10,2)
        ) as amount""",
        
        # Customer ID: 100K clientes (algunos más frecuentes)
        """cast(
            case 
                when rand() < 0.2 then cast(rand() * 1000 as int)
                else cast(rand() * 100000 as int)
            end as int
        ) as customer_id""",
        
        # Region ID: 10 regiones (distribución desigual)
        """cast(
            case 
                when rand() < 0.3 then 1
                when rand() < 0.5 then 2
                when rand() < 0.7 then 3
                else 4 + cast(rand() * 6 as int)
            end as int
        ) as region_id""",
        
        # Product ID: 1000 productos
        "cast(1 + rand() * 999 as int) as product_id",
        
        # Store ID: 100 tiendas
        "cast(1 + rand() * 99 as int) as store_id",
        
        # Status: mayormente ACTIVE, algunos PENDING/CANCELLED
        """case 
            when rand() < 0.85 then 'ACTIVE'
            when rand() < 0.95 then 'PENDING'
            else 'CANCELLED'
        end as status""",
        
        # Discount: 0-30% en algunos casos
        """cast(
            case 
                when rand() < 0.7 then 0
                when rand() < 0.9 then rand() * 10
                else rand() * 30
            end as decimal(5,2)
        ) as discount_percent""",
        
        # Payment method
        """case 
            when rand() < 0.4 then 'CREDIT_CARD'
            when rand() < 0.7 then 'DEBIT_CARD'
            when rand() < 0.9 then 'CASH'
            else 'WIRE_TRANSFER'
        end as payment_method"""
    )
    
    # Agregar columnas derivadas
    df = df.withColumn(
        "net_amount",
        (col("amount") * (lit(100) - col("discount_percent")) / lit(100)).cast(DecimalType(10,2))
    )
    
    return df

def write_fact_sales(df, output_path, partition_by="sale_date", format="parquet"):
    """
    Escribe fact_sales particionado
    
    Args:
        df: DataFrame a escribir
        output_path: Ruta de salida (local, s3://, gs://, abfss://)
        partition_by: Columna de partición (default: sale_date)
        format: Formato (parquet, delta, iceberg)
    """
    print(f"\n📝 Escribiendo datos a: {output_path}")
    print(f"🗂️  Particionado por: {partition_by}")
    print(f"📦 Formato: {format}")
    
    writer = df.write \
        .mode("overwrite") \
        .partitionBy(partition_by)
    
    if format == "delta":
        writer = writer.format("delta") \
            .option("overwriteSchema", "true")
    elif format == "iceberg":
        writer = writer.format("iceberg")
    else:
        # Parquet con compresión
        writer = writer.option("compression", "snappy")
    
    writer.save(output_path)
    print("✅ Escritura completada")

def show_statistics(df):
    """Muestra estadísticas del dataset generado"""
    print("\n" + "="*60)
    print("📊 ESTADÍSTICAS DEL DATASET")
    print("="*60)
    
    print(f"\n📏 Total rows: {df.count():,}")
    
    print("\n📅 Distribución por fecha (primeras 10):")
    df.groupBy("sale_date") \
        .count() \
        .orderBy("sale_date") \
        .show(10, truncate=False)
    
    print("\n🏪 Top 10 regiones por ventas:")
    df.groupBy("region_id") \
        .count() \
        .orderBy(col("count").desc()) \
        .show(10)
    
    print("\n💰 Estadísticas de amount:")
    df.select("amount", "net_amount").describe().show()
    
    print("\n📊 Distribución por status:")
    df.groupBy("status").count().show()
    
    print("\n💳 Distribución por payment_method:")
    df.groupBy("payment_method").count().show()

def main():
    parser = argparse.ArgumentParser(
        description="Genera datos sintéticos para fact_sales"
    )
    parser.add_argument(
        "--rows",
        type=int,
        default=1000000,
        help="Número de filas a generar (default: 1,000,000)"
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Ruta de salida (local, s3://, gs://, abfss://)"
    )
    parser.add_argument(
        "--format",
        type=str,
        default="parquet",
        choices=["parquet", "delta", "iceberg"],
        help="Formato de salida (default: parquet)"
    )
    parser.add_argument(
        "--start-date",
        type=str,
        default="2024-01-01",
        help="Fecha inicial (default: 2024-01-01)"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=730,
        help="Días de datos (default: 730 = 2 años)"
    )
    parser.add_argument(
        "--size",
        type=str,
        default="medium",
        choices=["small", "medium", "large", "xlarge"],
        help="Preset de tamaño (overrides --rows)"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Mostrar estadísticas después de generar"
    )
    
    args = parser.parse_args()
    
    # Presets de tamaño
    size_presets = {
        "small": 10_000,
        "medium": 1_000_000,
        "large": 100_000_000,
        "xlarge": 1_000_000_000
    }
    
    if args.size:
        args.rows = size_presets.get(args.size, args.rows)
    
    # Crear Spark session
    spark = create_spark_session()
    
    try:
        # Generar datos
        df = generate_fact_sales(
            spark,
            args.rows,
            args.start_date,
            args.days
        )
        
        # Mostrar muestra
        print("\n📋 Muestra de datos:")
        df.show(10, truncate=False)
        
        # Estadísticas
        if args.stats:
            show_statistics(df)
        
        # Escribir
        write_fact_sales(df, args.output, format=args.format)
        
        print(f"\n✅ Generación completada exitosamente")
        print(f"📁 Datos disponibles en: {args.output}")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        raise
    finally:
        spark.stop()

if __name__ == "__main__":
    main()
