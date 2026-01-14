"""
Templates de validación en PySpark

Funciones reutilizables para validar resultados de migración Oracle → Spark.
"""

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import (
    col, count, sum as _sum, avg, min as _min, max as _max,
    when, isnan, isnull, md5, concat_ws, lit
)
from typing import Dict, List, Tuple
import sys

def row_count_by_partition(
    df: DataFrame,
    partition_col: str,
    name: str = "table"
) -> DataFrame:
    """
    Conteo de filas por partición.
    
    Uso:
        counts = row_count_by_partition(sales_df, "sale_date", "fact_sales")
        counts.show()
    """
    print(f"\n📊 Row counts por partición: {name}")
    
    result = df.groupBy(partition_col) \
        .count() \
        .orderBy(partition_col)
    
    total = df.count()
    print(f"   Total rows: {total:,}")
    
    return result

def compare_row_counts(
    oracle_df: DataFrame,
    spark_df: DataFrame,
    partition_col: str = None
) -> Dict[str, int]:
    """
    Compara row counts entre Oracle export y Spark.
    
    Returns:
        dict con 'oracle', 'spark', 'diff'
    """
    print("\n🔍 Comparando row counts...")
    
    oracle_count = oracle_df.count()
    spark_count = spark_df.count()
    diff = spark_count - oracle_count
    
    result = {
        "oracle": oracle_count,
        "spark": spark_count,
        "diff": diff,
        "match": diff == 0
    }
    
    print(f"   Oracle: {oracle_count:,}")
    print(f"   Spark:  {spark_count:,}")
    print(f"   Diff:   {diff:+,}")
    
    if result["match"]:
        print("   ✅ Row counts coinciden")
    else:
        print("   ⚠️  Row counts NO coinciden")
    
    if partition_col:
        print(f"\n   Comparando por partición ({partition_col}):")
        oracle_by_part = oracle_df.groupBy(partition_col).count() \
            .withColumnRenamed("count", "oracle_count")
        spark_by_part = spark_df.groupBy(partition_col).count() \
            .withColumnRenamed("count", "spark_count")
        
        comparison = oracle_by_part.join(
            spark_by_part,
            partition_col,
            "full_outer"
        ).withColumn(
            "diff",
            col("spark_count") - col("oracle_count")
        ).orderBy(partition_col)
        
        comparison.show()
    
    return result

def compare_aggregations(
    oracle_df: DataFrame,
    spark_df: DataFrame,
    group_by_cols: List[str],
    agg_cols: List[str]
) -> DataFrame:
    """
    Compara agregaciones entre Oracle y Spark.
    
    Ejemplo:
        compare_aggregations(
            oracle_df, spark_df,
            group_by_cols=["region_id"],
            agg_cols=["amount"]
        )
    """
    print(f"\n📊 Comparando agregaciones...")
    print(f"   Group by: {group_by_cols}")
    print(f"   Aggregating: {agg_cols}")
    
    # Agregar Oracle
    oracle_agg = oracle_df.groupBy(*group_by_cols).agg(
        *[_sum(c).alias(f"oracle_{c}_sum") for c in agg_cols],
        *[count(c).alias(f"oracle_{c}_count") for c in agg_cols]
    )
    
    # Agregar Spark
    spark_agg = spark_df.groupBy(*group_by_cols).agg(
        *[_sum(c).alias(f"spark_{c}_sum") for c in agg_cols],
        *[count(c).alias(f"spark_{c}_count") for c in agg_cols]
    )
    
    # Full outer join para comparar
    comparison = oracle_agg.join(
        spark_agg,
        group_by_cols,
        "full_outer"
    )
    
    # Agregar columnas de diferencias
    for c in agg_cols:
        comparison = comparison.withColumn(
            f"{c}_sum_diff",
            col(f"spark_{c}_sum") - col(f"oracle_{c}_sum")
        )
    
    # Mostrar discrepancias
    discrepancies = comparison.filter(
        " OR ".join([f"{c}_sum_diff != 0" for c in agg_cols])
    )
    
    disc_count = discrepancies.count()
    if disc_count > 0:
        print(f"\n   ⚠️  {disc_count} discrepancias encontradas:")
        discrepancies.show(20)
    else:
        print("\n   ✅ Agregaciones coinciden")
    
    return comparison

def full_outer_join_reconciliation(
    oracle_df: DataFrame,
    spark_df: DataFrame,
    key_cols: List[str],
    compare_cols: List[str] = None
) -> Tuple[DataFrame, Dict]:
    """
    Reconciliación completa usando full outer join.
    
    Returns:
        (DataFrame con diffs, dict con estadísticas)
    """
    print(f"\n🔄 Reconciliación full outer join...")
    print(f"   Keys: {key_cols}")
    
    # Renombrar columnas para evitar colisiones
    oracle_renamed = oracle_df
    spark_renamed = spark_df
    
    for c in oracle_df.columns:
        if c not in key_cols:
            oracle_renamed = oracle_renamed.withColumnRenamed(c, f"oracle_{c}")
            spark_renamed = spark_renamed.withColumnRenamed(c, f"spark_{c}")
    
    # Full outer join
    joined = oracle_renamed.join(
        spark_renamed,
        key_cols,
        "full_outer"
    )
    
    # Clasificar registros
    joined = joined.withColumn(
        "presence",
        when(col(f"oracle_{oracle_df.columns[len(key_cols)]}").isNull(), lit("ONLY_IN_SPARK"))
        .when(col(f"spark_{spark_df.columns[len(key_cols)]}").isNull(), lit("ONLY_IN_ORACLE"))
        .otherwise(lit("IN_BOTH"))
    )
    
    # Contar por categoría
    stats = joined.groupBy("presence").count().collect()
    stats_dict = {row["presence"]: row["count"] for row in stats}
    
    print(f"\n   📊 Estadísticas:")
    print(f"      IN_BOTH:        {stats_dict.get('IN_BOTH', 0):,}")
    print(f"      ONLY_IN_ORACLE: {stats_dict.get('ONLY_IN_ORACLE', 0):,}")
    print(f"      ONLY_IN_SPARK:  {stats_dict.get('ONLY_IN_SPARK', 0):,}")
    
    # Identificar diferencias en valores (solo registros IN_BOTH)
    if compare_cols:
        diffs = joined.filter(col("presence") == "IN_BOTH")
        
        for c in compare_cols:
            diffs = diffs.withColumn(
                f"{c}_match",
                col(f"oracle_{c}") <=> col(f"spark_{c}")
            )
        
        # Registros con al menos una diferencia
        diff_filter = " OR ".join([f"NOT {c}_match" for c in compare_cols])
        value_diffs = diffs.filter(diff_filter)
        
        value_diff_count = value_diffs.count()
        stats_dict["VALUE_DIFFERENCES"] = value_diff_count
        
        if value_diff_count > 0:
            print(f"      VALUE_DIFFS:    {value_diff_count:,}")
            print("\n   ⚠️  Muestra de diferencias:")
            value_diffs.show(10, truncate=False)
        else:
            print("      ✅ Sin diferencias en valores")
    
    return joined, stats_dict

def data_quality_report(df: DataFrame, name: str = "table") -> Dict:
    """
    Genera reporte de calidad de datos.
    
    Returns:
        dict con métricas de calidad
    """
    print(f"\n📋 Data Quality Report: {name}")
    print("=" * 60)
    
    total_rows = df.count()
    print(f"\nTotal rows: {total_rows:,}")
    
    # Null counts por columna
    print("\n📊 Null/Empty counts por columna:")
    null_counts = df.select([
        count(when(col(c).isNull() | isnan(c), c)).alias(c)
        for c in df.columns
    ])
    null_counts.show(truncate=False)
    
    # Duplicados por todas las columnas
    print("\n📊 Duplicate check:")
    distinct_count = df.distinct().count()
    duplicates = total_rows - distinct_count
    print(f"   Distinct rows: {distinct_count:,}")
    print(f"   Duplicates:    {duplicates:,}")
    
    if duplicates > 0:
        print("   ⚠️  Hay duplicados")
    else:
        print("   ✅ Sin duplicados")
    
    # Estadísticas numéricas
    print("\n📊 Numeric statistics:")
    df.describe().show()
    
    # Métricas de calidad
    quality_metrics = {
        "total_rows": total_rows,
        "distinct_rows": distinct_count,
        "duplicates": duplicates,
        "duplicate_rate": duplicates / total_rows if total_rows > 0 else 0
    }
    
    return quality_metrics

def checksum_validation(
    oracle_df: DataFrame,
    spark_df: DataFrame,
    key_cols: List[str],
    value_cols: List[str]
) -> DataFrame:
    """
    Validación usando checksums (MD5).
    
    Útil para comparar datasets grandes de forma eficiente.
    """
    print("\n🔐 Checksum validation...")
    
    # Crear checksum Oracle
    oracle_with_hash = oracle_df.withColumn(
        "checksum",
        md5(concat_ws("|", *[col(c).cast("string") for c in value_cols]))
    )
    
    # Crear checksum Spark
    spark_with_hash = spark_df.withColumn(
        "checksum",
        md5(concat_ws("|", *[col(c).cast("string") for c in value_cols]))
    )
    
    # Comparar checksums
    oracle_checksums = oracle_with_hash.select(*key_cols, "checksum") \
        .withColumnRenamed("checksum", "oracle_checksum")
    
    spark_checksums = spark_with_hash.select(*key_cols, "checksum") \
        .withColumnRenamed("checksum", "spark_checksum")
    
    comparison = oracle_checksums.join(
        spark_checksums,
        key_cols,
        "full_outer"
    )
    
    # Identificar diferencias
    diffs = comparison.filter(
        col("oracle_checksum") != col("spark_checksum")
    )
    
    diff_count = diffs.count()
    total = comparison.count()
    
    print(f"   Total registros: {total:,}")
    print(f"   Diferencias:     {diff_count:,}")
    print(f"   Match rate:      {(1 - diff_count/total)*100:.2f}%")
    
    if diff_count > 0:
        print("\n   ⚠️  Muestra de diferencias:")
        diffs.show(10)
    else:
        print("   ✅ Checksums coinciden")
    
    return diffs

# Ejemplo de uso
if __name__ == "__main__":
    spark = SparkSession.builder.appName("Validation Example").getOrCreate()
    
    # Simular datos Oracle y Spark
    oracle_data = spark.range(1000).selectExpr(
        "id",
        "id % 10 as region_id",
        "cast(rand() * 1000 as decimal(10,2)) as amount"
    )
    
    # Spark data con pequeña diferencia
    spark_data = spark.range(1000).selectExpr(
        "id",
        "id % 10 as region_id",
        "cast(rand() * 1000 as decimal(10,2)) as amount"
    )
    
    # Ejecutar validaciones
    print("\n" + "="*60)
    print("EJEMPLO DE VALIDACIÓN")
    print("="*60)
    
    # 1. Row counts
    compare_row_counts(oracle_data, spark_data, "region_id")
    
    # 2. Agregaciones
    compare_aggregations(
        oracle_data, spark_data,
        group_by_cols=["region_id"],
        agg_cols=["amount"]
    )
    
    # 3. Data quality
    data_quality_report(spark_data, "spark_table")
    
    spark.stop()
