"""
Generador de datos para dimensiones (region, product, store, customer)
Genera dimensiones pequeñas para joins en los ejemplos.

Uso:
    python generate_dimensions.py --output /tmp/dimensions
    python generate_dimensions.py --output s3://bucket/bronze/dimensions
"""

import argparse
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, expr, lit, concat, when
from pyspark.sql.types import StructType, StructField, IntegerType, StringType, DateType

def create_spark_session(app_name="Generate Dimensions"):
    """Crea SparkSession"""
    return SparkSession.builder \
        .appName(app_name) \
        .config("spark.sql.shuffle.partitions", "10") \
        .getOrCreate()

def generate_dim_region(spark):
    """Genera dimensión de regiones (10 regiones)"""
    print("📍 Generando dim_region...")
    
    data = [
        (1, "North America", "NA", "USD", "United States"),
        (2, "South America", "SA", "USD", "Brazil"),
        (3, "Europe West", "EU-W", "EUR", "Germany"),
        (4, "Europe East", "EU-E", "EUR", "Poland"),
        (5, "Asia Pacific", "APAC", "USD", "Singapore"),
        (6, "Middle East", "ME", "USD", "UAE"),
        (7, "Africa", "AF", "USD", "South Africa"),
        (8, "Central America", "CA", "USD", "Mexico"),
        (9, "Oceania", "OCE", "AUD", "Australia"),
        (10, "India", "IN", "INR", "India")
    ]
    
    schema = StructType([
        StructField("region_id", IntegerType(), False),
        StructField("region_name", StringType(), False),
        StructField("region_code", StringType(), False),
        StructField("currency", StringType(), False),
        StructField("country", StringType(), False)
    ])
    
    df = spark.createDataFrame(data, schema)
    
    # Agregar metadata columns
    df = df.withColumn("is_active", lit(True)) \
           .withColumn("created_date", lit("2024-01-01").cast(DateType()))
    
    print(f"   ✅ {df.count()} regiones generadas")
    return df

def generate_dim_product(spark, num_products=1000):
    """Genera dimensión de productos"""
    print(f"📦 Generando dim_product ({num_products} productos)...")
    
    categories = [
        "Electronics", "Clothing", "Home & Garden", "Sports",
        "Books", "Toys", "Food & Beverage", "Health & Beauty",
        "Automotive", "Office Supplies"
    ]
    
    subcategories = {
        "Electronics": ["Phones", "Laptops", "Tablets", "Accessories"],
        "Clothing": ["Men", "Women", "Kids", "Accessories"],
        "Home & Garden": ["Furniture", "Decor", "Kitchen", "Garden"],
        "Sports": ["Equipment", "Apparel", "Footwear", "Accessories"],
        "Books": ["Fiction", "Non-Fiction", "Educational", "Children"],
        "Toys": ["Action Figures", "Board Games", "Educational", "Outdoor"],
        "Food & Beverage": ["Groceries", "Beverages", "Snacks", "Fresh"],
        "Health & Beauty": ["Skincare", "Makeup", "Health", "Accessories"],
        "Automotive": ["Parts", "Accessories", "Tools", "Care"],
        "Office Supplies": ["Paper", "Writing", "Organization", "Electronics"]
    }
    
    df = spark.range(1, num_products + 1) \
        .selectExpr(
            "id as product_id",
            f"array({','.join([f\"'{c}'\" for c in categories])})[cast(rand() * {len(categories)} as int)] as category",
            "concat('PROD-', lpad(id, 6, '0')) as product_code",
            "concat('Product ', id) as product_name",
            "cast(9.99 + rand() * 990 as decimal(10,2)) as unit_price",
            """case 
                when rand() < 0.8 then 'IN_STOCK'
                when rand() < 0.95 then 'LOW_STOCK'
                else 'OUT_OF_STOCK'
            end as stock_status""",
            "cast(rand() * 1000 as int) as stock_quantity"
        )
    
    # Agregar subcategories basadas en category
    # (Simplificado - en realidad necesitaría UDF)
    df = df.withColumn("subcategory", 
        when(col("category") == "Electronics", "Phones")
        .when(col("category") == "Clothing", "Men")
        .otherwise("General")
    )
    
    df = df.withColumn("is_active", lit(True)) \
           .withColumn("created_date", lit("2024-01-01").cast(DateType()))
    
    print(f"   ✅ {df.count()} productos generados")
    return df

def generate_dim_store(spark, num_stores=100):
    """Genera dimensión de tiendas"""
    print(f"🏪 Generando dim_store ({num_stores} tiendas)...")
    
    store_types = ["Flagship", "Standard", "Express", "Online"]
    
    df = spark.range(1, num_stores + 1) \
        .selectExpr(
            "id as store_id",
            "concat('STORE-', lpad(id, 4, '0')) as store_code",
            "concat('Store ', id) as store_name",
            f"array({','.join([f\"'{t}'\" for t in store_types])})[cast(rand() * {len(store_types)} as int)] as store_type",
            "cast(1 + rand() * 9 as int) as region_id",
            """concat(
                cast(100 + rand() * 900 as int), ' ',
                array('Main', 'Oak', 'Maple', 'Pine', 'Elm')[cast(rand() * 5 as int)], ' ',
                array('St', 'Ave', 'Blvd', 'Dr', 'Way')[cast(rand() * 5 as int)]
            ) as address""",
            """array('New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 
                    'Philadelphia', 'San Antonio', 'San Diego', 'Dallas', 'San Jose'
            )[cast(rand() * 10 as int)] as city""",
            "concat(cast(10000 + rand() * 89999 as int)) as zipcode",
            "cast(500 + rand() * 9500 as decimal(10,2)) as square_feet",
            "cast(5 + rand() * 95 as int) as employee_count"
        )
    
    df = df.withColumn("is_active", 
        when(col("store_type") == "Online", lit(True))
        .otherwise(expr("rand() > 0.05"))
    )
    
    df = df.withColumn("opened_date", 
        expr("date_add('2010-01-01', cast(rand() * 5000 as int))")
    )
    
    print(f"   ✅ {df.count()} tiendas generadas")
    return df

def generate_dim_customer(spark, num_customers=100000):
    """Genera dimensión de clientes"""
    print(f"👤 Generando dim_customer ({num_customers} clientes)...")
    
    first_names = ["John", "Jane", "Michael", "Sarah", "David", "Maria", 
                   "James", "Lisa", "Robert", "Jennifer"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", 
                  "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]
    
    df = spark.range(1, num_customers + 1) \
        .selectExpr(
            "id as customer_id",
            "concat('CUST-', lpad(id, 8, '0')) as customer_code",
            f"array({','.join([f\"'{n}'\" for n in first_names])})[cast(rand() * {len(first_names)} as int)] as first_name",
            f"array({','.join([f\"'{n}'\" for n in last_names])})[cast(rand() * {len(last_names)} as int)] as last_name",
            """lower(concat(
                array('john', 'jane', 'michael', 'sarah', 'david')[cast(rand() * 5 as int)],
                '.',
                array('smith', 'johnson', 'brown', 'jones')[cast(rand() * 4 as int)],
                '@',
                array('gmail.com', 'yahoo.com', 'hotmail.com', 'company.com')[cast(rand() * 4 as int)]
            )) as email""",
            """concat(
                '+1-',
                cast(200 + rand() * 799 as int), '-',
                cast(100 + rand() * 899 as int), '-',
                cast(1000 + rand() * 8999 as int)
            ) as phone""",
            "cast(1 + rand() * 9 as int) as region_id",
            """case 
                when rand() < 0.05 then 'PLATINUM'
                when rand() < 0.20 then 'GOLD'
                when rand() < 0.50 then 'SILVER'
                else 'BRONZE'
            end as loyalty_tier""",
            "cast(rand() * 15 as int) as loyalty_years",
            """case 
                when rand() < 0.95 then 'ACTIVE'
                when rand() < 0.98 then 'INACTIVE'
                else 'SUSPENDED'
            end as status"""
        )
    
    df = df.withColumn("full_name", concat(col("first_name"), lit(" "), col("last_name")))
    df = df.withColumn("registration_date", 
        expr("date_add('2010-01-01', cast(rand() * 5000 as int))")
    )
    
    print(f"   ✅ {df.count()} clientes generados")
    return df

def write_dimension(df, output_path, dim_name, format="parquet"):
    """Escribe dimensión"""
    full_path = f"{output_path}/{dim_name}"
    print(f"   📝 Escribiendo a: {full_path}")
    
    writer = df.write.mode("overwrite")
    
    if format == "delta":
        writer = writer.format("delta")
    elif format == "iceberg":
        writer = writer.format("iceberg")
    else:
        writer = writer.option("compression", "snappy")
    
    writer.save(full_path)
    print(f"   ✅ {dim_name} escrito")

def main():
    parser = argparse.ArgumentParser(
        description="Genera dimensiones para ejemplos"
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Ruta base de salida (local, s3://, gs://, abfss://)"
    )
    parser.add_argument(
        "--format",
        type=str,
        default="parquet",
        choices=["parquet", "delta", "iceberg"],
        help="Formato de salida (default: parquet)"
    )
    parser.add_argument(
        "--products",
        type=int,
        default=1000,
        help="Número de productos (default: 1000)"
    )
    parser.add_argument(
        "--stores",
        type=int,
        default=100,
        help="Número de tiendas (default: 100)"
    )
    parser.add_argument(
        "--customers",
        type=int,
        default=100000,
        help="Número de clientes (default: 100,000)"
    )
    
    args = parser.parse_args()
    
    spark = create_spark_session()
    
    try:
        print("\n" + "="*60)
        print("🏗️  GENERANDO DIMENSIONES")
        print("="*60 + "\n")
        
        # Generar y escribir cada dimensión
        dims = [
            ("dim_region", generate_dim_region(spark)),
            ("dim_product", generate_dim_product(spark, args.products)),
            ("dim_store", generate_dim_store(spark, args.stores)),
            ("dim_customer", generate_dim_customer(spark, args.customers))
        ]
        
        for dim_name, df in dims:
            # Mostrar muestra
            print(f"\n📋 Muestra de {dim_name}:")
            df.show(5, truncate=False)
            
            # Escribir
            write_dimension(df, args.output, dim_name, args.format)
        
        print("\n" + "="*60)
        print("✅ TODAS LAS DIMENSIONES GENERADAS EXITOSAMENTE")
        print("="*60)
        print(f"\n📁 Dimensiones disponibles en: {args.output}/")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        raise
    finally:
        spark.stop()

if __name__ == "__main__":
    main()
