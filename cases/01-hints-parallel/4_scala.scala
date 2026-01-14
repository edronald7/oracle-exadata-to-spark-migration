package com.migration.cases

import org.apache.spark.sql.{DataFrame, SparkSession, functions => F}
import java.time.LocalDateTime
import java.time.Duration

/**
 * Caso 01: Hints y Paralelismo - Implementación Scala
 * 
 * Demuestra cómo eliminar hints de Oracle y usar capacidades de Spark:
 * - AQE (Adaptive Query Execution) reemplaza hints de paralelismo
 * - Broadcast join reemplaza USE_HASH con dimensiones pequeñas
 * - Type-safe Dataset API para mejor mantenibilidad
 * 
 * Compilar:
 *   sbt package
 * 
 * Ejecutar:
 *   spark-submit --class com.migration.cases.Case01HintsParallel \
 *     target/scala-2.12/spark-migration-cases_2.12-1.0.jar
 */
object Case01HintsParallel {
  
  // Case classes para type-safety (opcional pero recomendado)
  case class Sale(
    sale_id: Int,
    sale_date: java.sql.Date,
    amount: BigDecimal,
    region_id: Int
  )
  
  case class Region(
    region_id: Int,
    region_name: String,
    region_code: String
  )
  
  case class SalesByRegion(
    region_name: String,
    total: BigDecimal
  )
  
  def createSparkSession(): SparkSession = {
    SparkSession.builder()
      .appName("Case01_Hints_Parallel")
      .config("spark.sql.adaptive.enabled", "true")
      .config("spark.sql.adaptive.coalescePartitions.enabled", "true")
      .config("spark.sql.adaptive.skewJoin.enabled", "true")
      .config("spark.sql.shuffle.partitions", "200")
      .config("spark.sql.autoBroadcastJoinThreshold", "10485760")
      .getOrCreate()
  }
  
  def readData(spark: SparkSession, basePath: String): (DataFrame, DataFrame) = {
    println("📖 Leyendo datos...")
    
    val factSales = spark.read.parquet(s"$basePath/fact_sales")
    val dimRegion = spark.read.parquet(s"$basePath/dim_region")
    
    println(s"   fact_sales: ${factSales.count()} rows")
    println(s"   dim_region: ${dimRegion.count()} rows")
    
    (factSales, dimRegion)
  }
  
  def runQueryApproach1SQL(
    spark: SparkSession,
    factSales: DataFrame,
    dimRegion: DataFrame
  ): DataFrame = {
    println("\n📊 Approach 1: Spark SQL")
    
    import spark.implicits._
    
    // Registrar temp views
    factSales.createOrReplaceTempView("fact_sales")
    dimRegion.createOrReplaceTempView("dim_region")
    
    // Query con hint de broadcast
    spark.sql("""
      SELECT /*+ BROADCAST(d) */
        d.region_name,
        SUM(f.amount) AS total
      FROM fact_sales f
      JOIN dim_region d ON d.region_id = f.region_id
      WHERE f.sale_date >= DATE '2025-01-01'
      GROUP BY d.region_name
      ORDER BY total DESC
    """)
  }
  
  def runQueryApproach2DataFrame(
    factSales: DataFrame,
    dimRegion: DataFrame
  ): DataFrame = {
    println("\n📊 Approach 2: DataFrame API")
    
    // Filtrar antes del join
    val filteredSales = factSales.filter(F.col("sale_date") >= "2025-01-01")
    
    // Join con broadcast
    val joined = filteredSales.join(
      F.broadcast(dimRegion),
      Seq("region_id")
    )
    
    // Agregar
    joined
      .groupBy("region_name")
      .agg(F.sum("amount").as("total"))
      .orderBy(F.desc("total"))
  }
  
  def runQueryApproach3TypeSafe(
    spark: SparkSession,
    factSales: DataFrame,
    dimRegion: DataFrame
  ): DataFrame = {
    println("\n📊 Approach 3: Type-Safe Dataset API (Scala unique)")
    
    import spark.implicits._
    
    // Convertir a Datasets type-safe
    // Nota: requiere que columnas coincidan exactamente con case classes
    // En este ejemplo, usamos DataFrame por simplicidad
    
    val filteredSales = factSales.filter($"sale_date" >= "2025-01-01")
    
    val result = filteredSales
      .join(F.broadcast(dimRegion), Seq("region_id"))
      .groupBy("region_name")
      .agg(F.sum("amount").as("total"))
      .orderBy(F.desc("total"))
    
    // Type-safe alternative (si schema coincide):
    // val salesDS = factSales.as[Sale].filter(_.sale_date >= ...)
    // val regionsDS = dimRegion.as[Region]
    // salesDS.joinWith(regionsDS, ...).groupByKey(...)
    
    result
  }
  
  def analyzeQuery(result: DataFrame, name: String): Unit = {
    println(s"\n🔍 Análisis: $name")
    println("=" * 60)
    
    // Plan de ejecución
    println("\n📋 Physical Plan:")
    result.explain(extended = true)
    
    // Particiones
    val numPartitions = result.rdd.getNumPartitions
    println(f"\n📦 Output partitions: $numPartitions")
    
    // Ejecutar y medir tiempo
    println("\n⏱️  Ejecutando query...")
    val startTime = LocalDateTime.now()
    
    val resultCount = result.count()
    result.show(10, truncate = false)
    
    val endTime = LocalDateTime.now()
    val duration = Duration.between(startTime, endTime).toMillis / 1000.0
    
    println(f"\n✅ Completado en $duration%.2fs")
    println(s"📊 Resultados: $resultCount rows")
  }
  
  def compareWithOracle(): Unit = {
    println("\n🔄 Validación (comparar con Oracle):")
    println("   1. Exportar resultado Oracle a CSV/Parquet")
    println("   2. Leer con: val oracleResult = spark.read.csv(\"oracle_export.csv\")")
    println("   3. Comparar: result.exceptAll(oracleResult)")
    println("   Ver: ../../templates/reconciliation_full_outer_join.sql")
  }
  
  def main(args: Array[String]): Unit = {
    // Parse arguments (simplificado)
    val inputPath = if (args.length > 0) args(0) else "../../data/output"
    val outputPath = if (args.length > 1) args(1) else "./output"
    val approach = if (args.length > 2) args(2) else "both"
    
    val spark = createSparkSession()
    
    try {
      println("\n" + "=" * 60)
      println("🚀 CASO 01: HINTS Y PARALELISMO (Scala)")
      println("=" * 60)
      println(s"\n📂 Input: $inputPath")
      println(s"📁 Output: $outputPath")
      
      // Leer datos
      val (factSales, dimRegion) = readData(spark, inputPath)
      
      // Ejecutar approaches
      approach match {
        case "sql" | "both" =>
          val resultSQL = runQueryApproach1SQL(spark, factSales, dimRegion)
          analyzeQuery(resultSQL, "Spark SQL with Broadcast Hint")
          resultSQL.write.mode("overwrite").parquet(s"$outputPath/result_sql")
        
        case "dataframe" | "both" =>
          val resultDF = runQueryApproach2DataFrame(factSales, dimRegion)
          analyzeQuery(resultDF, "DataFrame API with Broadcast")
          resultDF.write.mode("overwrite").parquet(s"$outputPath/result_dataframe")
        
        case "typesafe" =>
          val resultTS = runQueryApproach3TypeSafe(spark, factSales, dimRegion)
          analyzeQuery(resultTS, "Type-Safe Dataset API")
          resultTS.write.mode("overwrite").parquet(s"$outputPath/result_typesafe")
        
        case _ =>
          println(s"⚠️  Approach desconocido: $approach")
      }
      
      // Guía de validación
      compareWithOracle()
      
      println("\n✅ CASO 01 COMPLETADO")
      println("=" * 60)
      
    } catch {
      case e: Exception =>
        println(s"\n❌ Error: ${e.getMessage}")
        e.printStackTrace()
        System.exit(1)
    } finally {
      spark.stop()
    }
  }
}
