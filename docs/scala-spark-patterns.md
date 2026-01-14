# Scala Spark Patterns

Guía de patrones y mejores prácticas para Spark con Scala.

---

## 🎯 Por qué Scala para Spark

### Ventajas sobre PySpark

| Aspecto | Scala | PySpark |
|---------|-------|---------|
| **Performance** | Sin overhead de serialización | Serialización Python ↔ JVM |
| **Type Safety** | Compilación type-safe | Runtime errors |
| **API Coverage** | API completa (RDD, DataFrame, Dataset) | Solo DataFrame |
| **Memoria** | Objetos JVM nativos | Objetos Python + JVM |
| **Debugging** | Stack traces claros | Mezcla Python/JVM |
| **Ecosystem** | Acceso a librerías JVM/Scala | Solo Python libs |

### Cuándo usar Scala

✅ **Usa Scala cuando**:
- Performance crítico (procesamiento de billones de registros)
- Type safety es requerido (compliance, finance)
- Necesitas Datasets type-safe
- Pipelines de producción de alto throughput
- Integración con librerías JVM (Kafka, Cassandra, etc.)

⚠️ **Usa PySpark cuando**:
- Prototipado rápido
- Equipo con experiencia Python
- Integración con ML libraries (scikit-learn, TensorFlow)
- Análisis exploratorio

---

## 🏗️ Dataset API (Type-Safe)

### Case Classes y Datasets

```scala
import org.apache.spark.sql.{Dataset, SparkSession}
import java.sql.Date

// 1. Definir case class (equivalente a schema)
case class Sale(
  saleId: Int,
  saleDate: Date,
  amount: BigDecimal,
  regionId: Int,
  status: String
)

case class Region(
  regionId: Int,
  regionName: String,
  country: String
)

object TypeSafeExample {
  def main(args: Array[String]): Unit = {
    val spark = SparkSession.builder()
      .appName("Type-Safe Spark")
      .getOrCreate()
    
    import spark.implicits._
    
    // 2. Leer como Dataset[Sale] (type-safe)
    val sales: Dataset[Sale] = spark.read
      .parquet("s3://bucket/fact_sales")
      .as[Sale]
    
    val regions: Dataset[Region] = spark.read
      .parquet("s3://bucket/dim_region")
      .as[Region]
    
    // 3. Transformaciones type-safe
    val activeSales: Dataset[Sale] = sales.filter(_.status == "ACTIVE")
    
    // 4. Map operations (como colecciones Scala)
    val highValueSales: Dataset[Sale] = sales.filter(_.amount > 1000)
    
    // 5. Join type-safe
    val joined: Dataset[(Sale, Region)] = sales
      .joinWith(regions, sales("regionId") === regions("regionId"))
    
    // 6. Aggregations
    val summary = sales
      .groupByKey(_.regionId)
      .mapGroups { (regionId, salesIter) =>
        val salesList = salesIter.toList
        (regionId, salesList.size, salesList.map(_.amount).sum)
      }
    
    summary.show()
  }
}
```

### Ventajas de Datasets

```scala
// ✅ Compilador detecta errores
val sales: Dataset[Sale] = ...
sales.filter(_.amont > 100)  // ❌ Compile error: value amont is not a member of Sale

// ✅ IDE autocomplete
sales.filter(s => s. )  // IDE muestra: saleId, saleDate, amount, regionId, status

// ✅ Refactoring seguro
// Si cambias case class, compilador te indica todos los lugares a actualizar
```

---

## 🚀 Performance Patterns

### 1. Broadcast Join con Datasets

```scala
import org.apache.spark.sql.functions.broadcast

val sales: Dataset[Sale] = spark.read.parquet("sales").as[Sale]
val regions: Dataset[Region] = spark.read.parquet("regions").as[Region]

// Broadcast pequeña dimensión
val result = sales.join(
  broadcast(regions),
  sales("regionId") === regions("regionId")
)
```

### 2. Custom Aggregations (UDAF)

```scala
import org.apache.spark.sql.expressions.Aggregator
import org.apache.spark.sql.{Encoder, Encoders}

// Aggregator type-safe personalizado
case class Average(var sum: Double, var count: Long)

object TypedAverage extends Aggregator[Double, Average, Double] {
  def zero: Average = Average(0.0, 0L)
  
  def reduce(buffer: Average, data: Double): Average = {
    buffer.sum += data
    buffer.count += 1
    buffer
  }
  
  def merge(b1: Average, b2: Average): Average = {
    b1.sum += b2.sum
    b1.count += b2.count
    b1
  }
  
  def finish(reduction: Average): Double = {
    reduction.sum / reduction.count
  }
  
  def bufferEncoder: Encoder[Average] = Encoders.product
  def outputEncoder: Encoder[Double] = Encoders.scalaDouble
}

// Uso
val ds: Dataset[Sale] = spark.read.parquet("sales").as[Sale]
val avgAmount = ds
  .select(TypedAverage.toColumn.name("avg_amount"))
  .as[Double]
```

### 3. Partitioning Estratégico

```scala
// Repartition antes de joins grandes
val salesRepartitioned = sales.repartition($"regionId")
val regionsRepartitioned = regions.repartition($"regionId")

val joined = salesRepartitioned.join(
  regionsRepartitioned,
  Seq("regionId")
)

// Coalesce antes de escribir
joined
  .coalesce(100)
  .write
  .partitionBy("saleDate")
  .parquet("output/")
```

---

## 🏛️ Architectural Patterns

### Pattern 1: Pipeline Builder

```scala
trait Transformer[T] {
  def transform(ds: Dataset[T]): Dataset[T]
}

class DateRangeFilter(start: String, end: String) extends Transformer[Sale] {
  override def transform(ds: Dataset[Sale]): Dataset[Sale] = {
    ds.filter(s => s.saleDate.toString >= start && s.saleDate.toString < end)
  }
}

class StatusFilter(status: String) extends Transformer[Sale] {
  override def transform(ds: Dataset[Sale]): Dataset[Sale] = {
    ds.filter(_.status == status)
  }
}

class HighValueFilter(threshold: BigDecimal) extends Transformer[Sale] {
  override def transform(ds: Dataset[Sale]): Dataset[Sale] = {
    ds.filter(_.amount > threshold)
  }
}

// Composición funcional
object PipelineBuilder {
  def apply(transformers: Transformer[Sale]*)(ds: Dataset[Sale]): Dataset[Sale] = {
    transformers.foldLeft(ds) { (acc, transformer) =>
      transformer.transform(acc)
    }
  }
}

// Uso
val pipeline = PipelineBuilder(
  new DateRangeFilter("2025-01-01", "2025-12-31"),
  new StatusFilter("ACTIVE"),
  new HighValueFilter(1000)
)

val result = pipeline(sales)
```

### Pattern 2: Reader/Writer Abstraction

```scala
trait DataReader[T] {
  def read(spark: SparkSession, path: String): Dataset[T]
}

trait DataWriter[T] {
  def write(ds: Dataset[T], path: String, mode: String = "overwrite"): Unit
}

class ParquetSaleReader extends DataReader[Sale] {
  override def read(spark: SparkSession, path: String): Dataset[Sale] = {
    import spark.implicits._
    spark.read.parquet(path).as[Sale]
  }
}

class ParquetSaleWriter extends DataWriter[Sale] {
  override def write(ds: Dataset[Sale], path: String, mode: String): Unit = {
    ds.write
      .mode(mode)
      .partitionBy("saleDate")
      .parquet(path)
  }
}

// Uso
val reader = new ParquetSaleReader()
val writer = new ParquetSaleWriter()

val sales = reader.read(spark, "input/sales")
val processed = sales.filter(_.status == "ACTIVE")
writer.write(processed, "output/active_sales")
```

### Pattern 3: Configuration con Type Safety

```scala
case class SparkConfig(
  appName: String,
  master: String = "local[*]",
  shufflePartitions: Int = 200,
  adaptiveEnabled: Boolean = true,
  broadcastThreshold: Long = 10 * 1024 * 1024  // 10MB
)

object SparkSessionBuilder {
  def build(config: SparkConfig): SparkSession = {
    val builder = SparkSession.builder()
      .appName(config.appName)
      .master(config.master)
      .config("spark.sql.shuffle.partitions", config.shufflePartitions.toString)
      .config("spark.sql.adaptive.enabled", config.adaptiveEnabled.toString)
      .config("spark.sql.autoBroadcastJoinThreshold", config.broadcastThreshold.toString)
    
    builder.getOrCreate()
  }
}

// Uso
val config = SparkConfig(
  appName = "Sales Pipeline",
  shufflePartitions = 400,
  adaptiveEnabled = true
)

val spark = SparkSessionBuilder.build(config)
```

---

## 🧪 Testing con ScalaTest

### Setup de Tests

```scala
// build.sbt
libraryDependencies ++= Seq(
  "org.apache.spark" %% "spark-sql" % "3.5.0" % Test,
  "org.scalatest" %% "scalatest" % "3.2.17" % Test
)
```

### Test Suite

```scala
import org.apache.spark.sql.{Dataset, SparkSession}
import org.scalatest.BeforeAndAfterAll
import org.scalatest.flatspec.AnyFlatSpec
import org.scalatest.matchers.should.Matchers
import java.sql.Date

class SalesTransformerSpec extends AnyFlatSpec with Matchers with BeforeAndAfterAll {
  
  var spark: SparkSession = _
  
  override def beforeAll(): Unit = {
    spark = SparkSession.builder()
      .master("local[2]")
      .appName("test")
      .config("spark.sql.shuffle.partitions", "2")
      .getOrCreate()
  }
  
  override def afterAll(): Unit = {
    spark.stop()
  }
  
  "DateRangeFilter" should "filter sales by date range" in {
    import spark.implicits._
    
    // Given
    val testData = Seq(
      Sale(1, Date.valueOf("2025-01-15"), 100.0, 1, "ACTIVE"),
      Sale(2, Date.valueOf("2025-02-10"), 200.0, 2, "ACTIVE"),
      Sale(3, Date.valueOf("2025-03-05"), 300.0, 1, "PENDING")
    )
    val sales: Dataset[Sale] = spark.createDataset(testData)
    
    // When
    val filter = new DateRangeFilter("2025-01-01", "2025-02-01")
    val result = filter.transform(sales)
    
    // Then
    result.count() should be (1)
    result.first().saleId should be (1)
  }
  
  "StatusFilter" should "filter by status" in {
    import spark.implicits._
    
    val testData = Seq(
      Sale(1, Date.valueOf("2025-01-15"), 100.0, 1, "ACTIVE"),
      Sale(2, Date.valueOf("2025-02-10"), 200.0, 2, "PENDING")
    )
    val sales: Dataset[Sale] = spark.createDataset(testData)
    
    val filter = new StatusFilter("ACTIVE")
    val result = filter.transform(sales)
    
    result.count() should be (1)
    result.first().status should be ("ACTIVE")
  }
  
  "Pipeline" should "compose multiple transformers" in {
    import spark.implicits._
    
    val testData = Seq(
      Sale(1, Date.valueOf("2025-01-15"), 1500.0, 1, "ACTIVE"),
      Sale(2, Date.valueOf("2025-01-20"), 500.0, 2, "ACTIVE"),
      Sale(3, Date.valueOf("2025-02-10"), 2000.0, 1, "PENDING")
    )
    val sales: Dataset[Sale] = spark.createDataset(testData)
    
    val pipeline = PipelineBuilder(
      new DateRangeFilter("2025-01-01", "2025-02-01"),
      new StatusFilter("ACTIVE"),
      new HighValueFilter(1000)
    )
    
    val result = pipeline(sales)
    
    result.count() should be (1)
    result.first().saleId should be (1)
  }
}
```

### Ejecutar Tests

```bash
# Con sbt
sbt test

# Test específico
sbt "testOnly *SalesTransformerSpec"

# Con coverage
sbt clean coverage test coverageReport
```

---

## 🔍 Debugging y Profiling

### 1. Explain Plans

```scala
// Diferentes niveles de explain
df.explain()                    // Simple
df.explain(extended = true)     // Extended
df.explain(mode = "formatted")  // Formatted (Spark 3.0+)
df.explain(mode = "cost")       // Con cost estimates
```

### 2. Logging con Typesafe Config

```scala
import com.typesafe.scalalogging.LazyLogging

class SalesProcessor extends LazyLogging {
  
  def process(spark: SparkSession, inputPath: String, outputPath: String): Unit = {
    logger.info(s"Iniciando procesamiento: $inputPath -> $outputPath")
    
    try {
      import spark.implicits._
      
      logger.debug("Leyendo datos...")
      val sales: Dataset[Sale] = spark.read.parquet(inputPath).as[Sale]
      val count = sales.count()
      logger.info(s"Leídas $count filas")
      
      logger.debug("Aplicando transformaciones...")
      val result = sales.filter(_.status == "ACTIVE")
      
      logger.debug("Escribiendo resultado...")
      result.write.mode("overwrite").parquet(outputPath)
      
      logger.info(s"✅ Procesamiento completado")
      
    } catch {
      case e: Exception =>
        logger.error(s"❌ Error en procesamiento: ${e.getMessage}", e)
        throw e
    }
  }
}
```

### 3. Performance Monitoring

```scala
import org.apache.spark.sql.execution.QueryExecution
import org.apache.spark.sql.util.QueryExecutionListener

class PerformanceListener extends QueryExecutionListener {
  override def onSuccess(funcName: String, qe: QueryExecution, durationNs: Long): Unit = {
    val durationMs = durationNs / 1000000
    println(s"✅ Query '$funcName' completado en ${durationMs}ms")
    println(s"   Particiones: ${qe.sparkPlan.outputPartitioning}")
  }
  
  override def onFailure(funcName: String, qe: QueryExecution, exception: Exception): Unit = {
    println(s"❌ Query '$funcName' falló: ${exception.getMessage}")
  }
}

// Registrar listener
spark.listenerManager.register(new PerformanceListener())
```

---

## 📦 Build y Deployment

### build.sbt

```scala
name := "spark-migration-cases"

version := "1.0.0"

scalaVersion := "2.12.18"

libraryDependencies ++= Seq(
  "org.apache.spark" %% "spark-sql" % "3.5.0" % Provided,
  "org.apache.spark" %% "spark-core" % "3.5.0" % Provided,
  
  // Logging
  "com.typesafe.scala-logging" %% "scala-logging" % "3.9.5",
  "ch.qos.logback" % "logback-classic" % "1.4.11",
  
  // Testing
  "org.scalatest" %% "scalatest" % "3.2.17" % Test
)

// Assembly settings para fat JAR
assembly / assemblyMergeStrategy := {
  case PathList("META-INF", xs @ _*) => MergeStrategy.discard
  case x => MergeStrategy.first
}

assembly / assemblyJarName := s"${name.value}-${version.value}.jar"
```

### Compilar y Empaquetar

```bash
# Compilar
sbt compile

# Tests
sbt test

# Crear fat JAR
sbt assembly

# JAR resultante en target/scala-2.12/
```

### Ejecutar en Cluster

```bash
# Local
spark-submit \
  --class com.migration.cases.Case01Hints \
  --master local[*] \
  target/scala-2.12/spark-migration-cases-1.0.0.jar

# EMR
spark-submit \
  --class com.migration.cases.Case01Hints \
  --master yarn \
  --deploy-mode cluster \
  --driver-memory 4g \
  --executor-memory 8g \
  --executor-cores 4 \
  --num-executors 10 \
  s3://bucket/jars/spark-migration-cases-1.0.0.jar

# Databricks
databricks jobs create --json '{
  "name": "Sales Pipeline",
  "spark_jar_task": {
    "main_class_name": "com.migration.cases.Case01Hints"
  },
  "libraries": [{
    "jar": "dbfs:/jars/spark-migration-cases-1.0.0.jar"
  }]
}'
```

---

## ✅ Best Practices Checklist

- [ ] **Type Safety**: Usar Datasets con case classes en lugar de DataFrames
- [ ] **Immutability**: Preferir transformaciones inmutables
- [ ] **Lazy Evaluation**: Entender que transformations son lazy, actions son eager
- [ ] **Broadcast**: Usar para dimensiones <10MB
- [ ] **Partitioning**: Repartition por claves de join
- [ ] **Coalesce**: Antes de write para evitar small files
- [ ] **Schema Explicit**: Definir schemas con case classes
- [ ] **Testing**: Unit tests para todas las transformaciones
- [ ] **Logging**: Logging estructurado con niveles apropiados
- [ ] **Error Handling**: Try/catch con recuperación o fail fast
- [ ] **Configuration**: Externalizar configuración (Typesafe Config)
- [ ] **Assembly**: Fat JAR con dependencies shaded

---

## 📚 Recursos

- [Scala Spark API](https://spark.apache.org/docs/latest/api/scala/org/apache/spark/sql/index.html)
- [Dataset Guide](https://spark.apache.org/docs/latest/sql-getting-started.html)
- [Scala Style Guide](https://docs.scala-lang.org/style/)
- [High Performance Spark (Book)](https://www.oreilly.com/library/view/high-performance-spark/9781491943199/)
