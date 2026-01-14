"""
Caso 01: Hints y Paralelismo - Implementación PySpark

Demuestra cómo eliminar hints de Oracle y usar capacidades de Spark:
- AQE (Adaptive Query Execution) reemplaza hints de paralelismo
- Broadcast join reemplaza USE_HASH con dimensiones pequeñas
- Configuraciones de Spark en lugar de PARALLEL hints

Ejecutar:
    spark-submit 3_pyspark.py
    spark-submit 3_pyspark.py --input-path /custom/path --output-path /output
"""

import argparse
import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import sum as _sum, broadcast, col
from datetime import datetime

def create_spark_session(app_name="Case01_Hints_Parallel"):
    """
    Crea SparkSession con configuraciones óptimas.
    
    Estas configs reemplazan los hints Oracle:
    - adaptive.enabled: equivalente a paralelismo adaptativo
    - shuffle.partitions: control de paralelismo
    - autoBroadcastJoinThreshold: auto-broadcast para small dims
    """
    return SparkSession.builder \
        .appName(app_name) \
        .config("spark.sql.adaptive.enabled", "true") \
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
        .config("spark.sql.adaptive.skewJoin.enabled", "true") \
        .config("spark.sql.shuffle.partitions", "200") \
        .config("spark.sql.autoBroadcastJoinThreshold", "10485760") \
        .getOrCreate()

def read_data(spark, base_path):
    """Lee fact_sales y dim_region"""
    print("📖 Leyendo datos...")
    
    fact_sales = spark.read.parquet(f"{base_path}/fact_sales")
    dim_region = spark.read.parquet(f"{base_path}/dim_region")
    
    print(f"   fact_sales: {fact_sales.count():,} rows")
    print(f"   dim_region: {dim_region.count():,} rows")
    
    return fact_sales, dim_region

def run_query_approach_1_sql(spark, fact_sales, dim_region):
    """
    Approach 1: Spark SQL (más cercano a Oracle original)
    """
    print("\n📊 Approach 1: Spark SQL")
    
    # Registrar como temp views
    fact_sales.createOrReplaceTempView("fact_sales")
    dim_region.createOrReplaceTempView("dim_region")
    
    # Query con hint de broadcast (equivalente a USE_HASH para dim pequeña)
    result = spark.sql("""
        SELECT /*+ BROADCAST(d) */
            d.region_name,
            SUM(f.amount) AS total
        FROM fact_sales f
        JOIN dim_region d ON d.region_id = f.region_id
        WHERE f.sale_date >= DATE '2025-01-01'
        GROUP BY d.region_name
        ORDER BY total DESC
    """)
    
    return result

def run_query_approach_2_dataframe(fact_sales, dim_region):
    """
    Approach 2: DataFrame API (production-grade)
    
    Ventajas:
    - Type hints (IDE autocomplete)
    - Fácil testing
    - Composición modular
    """
    print("\n📊 Approach 2: DataFrame API")
    
    # Filtrar antes del join (pushdown)
    filtered_sales = fact_sales.filter(col("sale_date") >= "2025-01-01")
    
    # Join con broadcast explícito
    # broadcast() garantiza que dim pequeña se distribuya a todos los workers
    joined = filtered_sales.join(
        broadcast(dim_region),
        "region_id"  # Join key
    )
    
    # Agregar
    result = joined.groupBy("region_name") \
        .agg(_sum("amount").alias("total")) \
        .orderBy(col("total").desc())
    
    return result

def analyze_query(result, name):
    """Analiza plan de ejecución y muestra métricas"""
    print(f"\n🔍 Análisis: {name}")
    print("="*60)
    
    # Mostrar plan de ejecución
    print("\n📋 Physical Plan:")
    result.explain(mode="formatted")
    
    # Contar particiones
    num_partitions = result.rdd.getNumPartitions()
    print(f"\n📦 Output partitions: {num_partitions}")
    
    # Ejecutar y medir tiempo
    print("\n⏱️  Ejecutando query...")
    start_time = datetime.now()
    
    result_count = result.count()
    result.show(10, truncate=False)
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print(f"\n✅ Completado en {duration:.2f}s")
    print(f"📊 Resultados: {result_count} rows")

def compare_with_oracle(result):
    """
    En migración real, comparar con resultados Oracle exportados.
    Ver templates/reconciliation_full_outer_join.sql
    """
    print("\n🔄 Validación (comparar con Oracle):")
    print("   1. Exportar resultado Oracle a CSV/Parquet")
    print("   2. Leer con: oracle_result = spark.read.csv('oracle_export.csv')")
    print("   3. Comparar: result.exceptAll(oracle_result)")
    print("   Ver: ../../templates/reconciliation_full_outer_join.sql")

def main():
    parser = argparse.ArgumentParser(description="Case 01: Hints & Parallel - PySpark")
    parser.add_argument(
        "--input-path",
        default="../../data/output",  # Ajustar según dónde generaste datos
        help="Ruta base de datos de entrada"
    )
    parser.add_argument(
        "--output-path",
        default="./output",
        help="Ruta para guardar resultados"
    )
    parser.add_argument(
        "--approach",
        choices=["sql", "dataframe", "both"],
        default="both",
        help="Qué approach ejecutar"
    )
    
    args = parser.parse_args()
    
    # Crear Spark session
    spark = create_spark_session()
    
    try:
        print("\n" + "="*60)
        print("🚀 CASO 01: HINTS Y PARALELISMO")
        print("="*60)
        print(f"\n📂 Input: {args.input_path}")
        print(f"📁 Output: {args.output_path}")
        
        # Leer datos
        fact_sales, dim_region = read_data(spark, args.input_path)
        
        # Ejecutar approaches solicitados
        if args.approach in ["sql", "both"]:
            result_sql = run_query_approach_1_sql(spark, fact_sales, dim_region)
            analyze_query(result_sql, "Spark SQL with Broadcast Hint")
            
            # Guardar resultado
            result_sql.write.mode("overwrite").parquet(f"{args.output_path}/result_sql")
        
        if args.approach in ["dataframe", "both"]:
            result_df = run_query_approach_2_dataframe(fact_sales, dim_region)
            analyze_query(result_df, "DataFrame API with Broadcast")
            
            # Guardar resultado
            result_df.write.mode("overwrite").parquet(f"{args.output_path}/result_dataframe")
        
        # Guía de validación
        compare_with_oracle(result_df if args.approach == "dataframe" else result_sql)
        
        print("\n✅ CASO 01 COMPLETADO")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        spark.stop()

if __name__ == "__main__":
    main()
