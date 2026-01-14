# Learning Paths: Oracle Exadata → Apache Spark

Rutas de aprendizaje estructuradas según tu rol y experiencia.

---

## 🎯 Elige tu Perfil

| Perfil | Experiencia | Objetivo | Duración Estimada |
|--------|-------------|----------|-------------------|
| [**Analista SQL**](#ruta-1-analista-sql) | SQL avanzado, poco código | Traducir queries Oracle a Spark SQL | 2-4 semanas |
| [**Data Engineer Python**](#ruta-2-data-engineer-python) | Python, algo de SQL | Construir pipelines PySpark | 4-6 semanas |
| [**Data Engineer Scala**](#ruta-3-data-engineer-scala) | Scala/Java, programación | Pipelines Spark production-grade | 6-8 semanas |
| [**Arquitecto/DBA**](#ruta-4-arquitectodba) | Arquitectura Oracle, performance | Diseñar arquitectura Spark en cloud | 4-6 semanas |
| [**Team Lead**](#ruta-5-team-lead) | Liderazgo técnico | Planificar y ejecutar migración | 8-12 semanas |

---

## 📘 Ruta 1: Analista SQL

**Perfil**: Analista con experiencia en SQL Oracle, poca o nula experiencia en programación.

**Objetivo**: Ser capaz de traducir queries Oracle a Spark SQL y ejecutarlos en notebooks cloud.

### Semana 1: Fundamentos Spark SQL

**📚 Lectura** (4 horas):
- [ ] [Mapa de features Exadata → Spark](exadata-feature-map.md)
- [ ] [SQL vs DataFrame API](sql-vs-dataframe-api.md) (enfoque SQL)
- [ ] [Documentación oficial Spark SQL](https://spark.apache.org/docs/latest/sql-ref.html)

**💻 Práctica** (6 horas):
1. [ ] Setup de environment:
   - Opción A: Docker local con Jupyter
   - Opción B: Databricks Community Edition (gratis)
   - Opción C: Google Colab con PySpark

2. [ ] Ejecutar casos básicos:
   - [ ] [Caso 02: Smart Scan](../cases/02-smart-scan-filter-pushdown/)
   - [ ] [Caso 03: Partition Pruning](../cases/03-partition-pruning/)

3. [ ] Ejercicio: Traducir 5 queries propias de Oracle a Spark SQL

**✅ Checkpoint**: Ejecutaste exitosamente queries Spark SQL y entiendes diferencias con Oracle.

---

### Semana 2: Queries Complejas

**📚 Lectura** (3 horas):
- [ ] [Performance & Tuning](spark-performance-tuning.md)
- [ ] [Validation Strategy](validation-strategy.md)

**💻 Práctica** (7 horas):
1. [ ] Casos intermedios:
   - [ ] [Caso 05: Star Joins](../cases/05-star-joins-bloom/)
   - [ ] [Caso 09: Window Analytics](../cases/09-window-analytics/)
   - [ ] [Caso 11: Datatypes & NLS](../cases/11-datatypes-nls/)

2. [ ] Ejercicio: Migrar un reporte Oracle completo
   - Identificar queries del reporte
   - Traducir a Spark SQL
   - Validar resultados con templates

**✅ Checkpoint**: Migraste un reporte completo con joins y window functions.

---

### Semana 3-4: Cloud y Producción

**📚 Lectura** (4 horas):
- [ ] [Cloud Deployment Guide](cloud-deployment-guide.md)
- [ ] Guía específica de tu cloud:
  - [AWS EMR](../cloud/aws/emr-setup.md)
  - [Azure Databricks](../cloud/azure/databricks-setup.md)
  - [GCP Dataproc](../cloud/gcp/dataproc-setup.md)

**💻 Práctica** (10 horas):
1. [ ] Setup en cloud (Databricks recomendado para analistas)
2. [ ] Crear notebook con:
   - Conexión a datos
   - Queries traducidos
   - Visualizaciones
3. [ ] Schedule job automático
4. [ ] Compartir notebook con equipo

**🎓 Graduación**: 
- ✅ Puedes traducir cualquier query Oracle a Spark SQL
- ✅ Ejecutas queries en notebooks cloud
- ✅ Entiendes conceptos de partitioning y performance

---

## 💻 Ruta 2: Data Engineer (Python)

**Perfil**: Engineer con experiencia en Python, ETL, y algo de SQL.

**Objetivo**: Construir pipelines PySpark production-grade, testing, CI/CD.

### Semana 1-2: PySpark Fundamentals

**📚 Lectura** (6 horas):
- [ ] [PySpark Best Practices](pyspark-best-practices.md)
- [ ] [SQL vs DataFrame API](sql-vs-dataframe-api.md) (enfoque PySpark)
- [ ] [Exadata Feature Map](exadata-feature-map.md)

**💻 Práctica** (12 horas):
1. [ ] Setup local:
   ```bash
   pip install pyspark==3.5.0 pytest
   ```

2. [ ] Estudiar implementaciones PySpark:
   - [ ] [Caso 01: Hints](../cases/01-hints-parallel/3_pyspark.py)
   - [ ] [Caso 02: Smart Scan](../cases/02-smart-scan-filter-pushdown/3_pyspark.py)
   - [ ] [Caso 05: Star Joins](../cases/05-star-joins-bloom/3_pyspark.py)

3. [ ] Ejercicio: Re-implementar usando patterns aprendidos
   - Builder pattern para transformaciones
   - Validación de esquemas
   - Logging estructurado

**✅ Checkpoint**: Escribes transformaciones PySpark modulares y testeables.

---

### Semana 3-4: Testing y Calidad

**📚 Lectura** (4 horas):
- [ ] [Validation Strategy](validation-strategy.md)
- [ ] [pytest documentation](https://docs.pytest.org/)
- [ ] [Great Expectations](https://docs.greatexpectations.io/) (opcional)

**💻 Práctica** (12 horas):
1. [ ] Crear suite de tests:
   ```python
   # tests/test_transformers.py
   def test_filter_by_date()
   def test_aggregate_by_region()
   def test_data_quality()
   ```

2. [ ] Implementar data quality checks:
   - Row counts
   - Schema validation
   - Null checks
   - Business rules

3. [ ] Estudiar templates:
   - [ ] [Validación PySpark](../templates/pyspark/validation.py)
   - [ ] [Reconciliation](../templates/reconciliation_full_outer_join.sql)

**✅ Checkpoint**: Todos tus pipelines tienen tests unitarios y data quality checks.

---

### Semana 5-6: Cloud Deployment y CI/CD

**📚 Lectura** (4 horas):
- [ ] [Cloud Deployment Guide](cloud-deployment-guide.md)
- [ ] [GitHub Actions docs](https://docs.github.com/en/actions)

**💻 Práctica** (14 horas):
1. [ ] Setup en cloud (EMR o Dataproc para control)
2. [ ] Crear pipeline completo:
   - Extract (Oracle export)
   - Transform (PySpark jobs)
   - Load (Parquet/Delta)
   - Validate (reconciliation)

3. [ ] CI/CD:
   ```yaml
   # .github/workflows/test.yml
   - Run pytest
   - Lint with flake8
   - Deploy to DEV
   - Integration tests
   ```

4. [ ] Monitoreo:
   - Spark UI analysis
   - CloudWatch/Monitor logs
   - Alertas en failures

**🎓 Graduación**:
- ✅ Pipelines PySpark con testing completo
- ✅ Deployments automatizados con CI/CD
- ✅ Monitoreo y alertas configurados

---

## ⚡ Ruta 3: Data Engineer (Scala)

**Perfil**: Engineer con experiencia en Scala/Java, programación funcional.

**Objetivo**: Pipelines Spark ultra-optimizados, type-safe, production-grade.

### Semana 1-3: Scala Spark & Datasets

**📚 Lectura** (8 horas):
- [ ] [Scala Spark Patterns](scala-spark-patterns.md)
- [ ] [PySpark Best Practices](pyspark-best-practices.md) (para comparar)
- [ ] [Learning Spark (O'Reilly)](https://www.oreilly.com/library/view/learning-spark-2nd/9781492050032/)

**💻 Práctica** (18 horas):
1. [ ] Setup con sbt:
   ```scala
   // build.sbt
   libraryDependencies += "org.apache.spark" %% "spark-sql" % "3.5.0"
   ```

2. [ ] Estudiar implementaciones Scala:
   - [ ] Todos los casos `/4_scala.scala`
   - Enfócate en:
     - Case classes y Datasets
     - Type-safe transformations
     - Custom aggregators (UDAF)

3. [ ] Proyecto: Migrar pipeline completo a Scala
   - Define case classes para todas las entidades
   - Implementa transformers con type safety
   - Custom aggregations

**✅ Checkpoint**: Pipeline completamente type-safe con Datasets.

---

### Semana 4-6: Performance Optimization

**📚 Lectura** (6 horas):
- [ ] [Spark Performance Tuning](spark-performance-tuning.md)
- [ ] [High Performance Spark (Book)](https://www.oreilly.com/library/view/high-performance-spark/9781491943199/)
- [ ] [Tungsten Execution Engine](https://databricks.com/glossary/tungsten)

**💻 Práctica** (16 horas):
1. [ ] Performance profiling:
   - Analyze Spark UI
   - Identify bottlenecks (shuffle, skew, spill)
   - Fix con técnicas avanzadas

2. [ ] Optimizations:
   - Custom partitioning strategies
   - Broadcast optimization
   - Skew join handling
   - Adaptive query execution tuning

3. [ ] Benchmarking:
   - Comparar Scala vs PySpark
   - Medir impact de optimizaciones
   - Documentar findings

**✅ Checkpoint**: Pipeline optimizado con métricas de performance documentadas.

---

### Semana 7-8: Production Deployment

**📚 Lectura** (4 horas):
- [ ] [Cloud Deployment Guide](cloud-deployment-guide.md)
- [ ] [Scala Testing Best Practices](https://www.scalatest.org/user_guide)

**💻 Práctica** (14 horas):
1. [ ] Testing completo:
   ```scala
   // ScalaTest suite
   class PipelineSpec extends AnyFlatSpec
   ```

2. [ ] Build fat JAR:
   ```bash
   sbt assembly
   ```

3. [ ] Deploy a cluster:
   ```bash
   spark-submit --class com.company.Pipeline \
     --master yarn --deploy-mode cluster \
     pipeline.jar
   ```

4. [ ] Monitoring avanzado:
   - Custom QueryExecutionListener
   - Metrics a Prometheus
   - Grafana dashboards

**🎓 Graduación**:
- ✅ Pipeline Scala production-grade
- ✅ Performance optimizado (comparado con baseline)
- ✅ Monitoreo custom con métricas

---

## 🏗️ Ruta 4: Arquitecto/DBA

**Perfil**: Arquitecto o DBA con profundo conocimiento de Oracle Exadata.

**Objetivo**: Diseñar arquitectura completa de data lake en Spark/cloud.

### Semana 1-2: Assessment y Strategy

**📚 Lectura** (10 horas):
- [ ] [Exadata Feature Map](exadata-feature-map.md)
- [ ] [Migration Checklist](migration-checklist.md)
- [ ] [Cloud Deployment Guide](cloud-deployment-guide.md)
- [ ] [Validation Strategy](validation-strategy.md)

**💻 Actividades** (8 horas):
1. [ ] Inventario de workloads Oracle:
   - Top queries por costo/tiempo
   - Clasificar por patrón (ver casos)
   - Identificar complejidades (PL/SQL, hierarchical queries)

2. [ ] Sizing y cost estimation:
   - Volumetría actual
   - Proyección crecimiento
   - Comparativa cloud providers

3. [ ] POC scope definition:
   - 3-5 casos representativos
   - Métricas de éxito
   - Timeline

**✅ Checkpoint**: Assessment completo con recomendaciones documentadas.

---

### Semana 3-4: Diseño de Arquitectura

**📚 Lectura** (6 horas):
- [ ] Delta Lake / Iceberg / Hudi comparisons
- [ ] Data governance frameworks
- [ ] Cloud-specific guides (tu provider)

**💻 Actividades** (12 horas):
1. [ ] Diseño de data lake:
   ```
   Bronze (raw) → Silver (cleansed) → Gold (aggregated)
   ```

2. [ ] Estrategia de particionamiento:
   - Claves de partición por tabla
   - Bucketing strategy
   - Compaction policies

3. [ ] Governance:
   - Catálogo (Glue/Hive/Unity)
   - Data lineage
   - Access control (RBAC)
   - Encryption (at-rest, in-transit)

4. [ ] Disaster recovery:
   - Backup strategy
   - Cross-region replication
   - RTO/RPO targets

**✅ Checkpoint**: Arquitectura documentada con diagramas y decisiones clave.

---

### Semana 5-6: POC y Validación

**💻 Actividades** (18 horas):
1. [ ] Implementar POC:
   - Setup infrastructure (IaC)
   - Migrar casos seleccionados
   - Ejecutar validaciones

2. [ ] Performance testing:
   - Establecer baseline Oracle
   - Comparar con Spark
   - Identificar gaps

3. [ ] Presentación a stakeholders:
   - Resultados POC
   - Cost-benefit analysis
   - Roadmap de migración

**🎓 Graduación**:
- ✅ Arquitectura validada con POC exitoso
- ✅ Business case aprobado
- ✅ Roadmap detallado para full migration

---

## 👔 Ruta 5: Team Lead

**Perfil**: Líder técnico responsable de migración completa.

**Objetivo**: Planificar, ejecutar y operar migración de Oracle Exadata a Spark en cloud.

### Fase 1: Planning (2-3 semanas)

**📚 Lectura** (12 horas):
- [ ] Todas las guías del repositorio
- [ ] Case studies de migraciones similares
- [ ] [Databricks Migration Guides](https://www.databricks.com/solutions/migrating-to-databricks)

**💻 Actividades** (20 horas):
1. [ ] Team assessment:
   - Habilidades actuales
   - Gaps de conocimiento
   - Plan de capacitación

2. [ ] Workload analysis:
   - Inventario completo (ver arquitecto)
   - Priorización por impacto/esfuerzo
   - Dependency mapping

3. [ ] Migration strategy:
   - Big bang vs phased
   - Parallel run period
   - Rollback plan

4. [ ] Resource planning:
   - Team size y roles
   - Budget (compute + storage + licenses)
   - Timeline con milestones

**✅ Deliverable**: Migration plan aprobado por steering committee.

---

### Fase 2: Execution (6-8 semanas)

**💻 Actividades** (ongoing):
1. [ ] **Semana 1-2: Foundation**
   - Setup cloud accounts
   - Deploy infrastructure
   - Team training (según rutas individuales)

2. [ ] **Semana 3-4: Wave 1**
   - Migrar primeros 10-20% de workloads
   - Casos más simples (queries select, filtros, agregaciones)
   - Establecer patrones de migración

3. [ ] **Semana 5-6: Wave 2**
   - Workloads intermedios (joins, window functions)
   - Implementar pipelines ETL
   - Validaciones automatizadas

4. [ ] **Semana 7-8: Wave 3**
   - Workloads complejos (MVs, stored procedures)
   - Fine-tuning de performance
   - Cutover planning

**💡 Best Practices**:
- Daily standups con equipo
- Weekly status a stakeholders
- Risk log actualizado
- Celebrate wins

---

### Fase 3: Operations (ongoing)

**💻 Actividades**:
1. [ ] **Monitoring & Alerting**
   - Dashboards de performance
   - Cost tracking
   - Data quality monitoring
   - SLA compliance

2. [ ] **Optimization**
   - Performance tuning continuo
   - Cost optimization (spot instances, autoscaling)
   - Compaction schedules

3. [ ] **Knowledge Transfer**
   - Documentación de pipelines
   - Runbooks operacionales
   - Training para operaciones

4. [ ] **Continuous Improvement**
   - Retrospectivas mensuales
   - Roadmap de mejoras
   - Adopción de nuevas features Spark

**🎓 Graduación**:
- ✅ Migración completada en tiempo y presupuesto
- ✅ Operaciones estables con SLA >99%
- ✅ Team autónomo y capacitado

---

## 📊 Matriz de Skills

| Skill | Analista | Eng Python | Eng Scala | Arquitecto | Lead |
|-------|----------|------------|-----------|------------|------|
| **Spark SQL** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| **PySpark** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| **Scala Spark** | ⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| **Performance Tuning** | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Testing** | ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| **Cloud (AWS/Azure/GCP)** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Architecture** | ⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Project Management** | ⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## 📚 Recursos de Aprendizaje

### Libros Recomendados
1. **Learning Spark, 2nd Edition** (O'Reilly) - Todos
2. **High Performance Spark** (O'Reilly) - Engineers
3. **Spark: The Definitive Guide** (O'Reilly) - Arquitectos

### Cursos Online
- [Databricks Academy](https://academy.databricks.com/) - FREE
- [AWS Spark on EMR](https://aws.amazon.com/training/)
- [Coursera Big Data Specialization](https://www.coursera.org/specializations/big-data)

### Certificaciones
- Databricks Certified Associate Developer
- AWS Certified Data Analytics - Specialty
- Google Professional Data Engineer

---

## ✅ Tracking de Progreso

Usa esta checklist para hacer tracking de tu progreso:

```markdown
## Mi Progreso

**Perfil elegido**: [Analista/Eng Python/Eng Scala/Arquitecto/Lead]

**Semana actual**: X

### Completados
- [ ] Lectura semana 1
- [ ] Práctica semana 1
- [ ] Checkpoint semana 1
- [ ] ...

### Próximos pasos
1. ...
2. ...

### Dudas/Blockers
- ...
```

---

## 🤝 Comunidad y Soporte

- **Stack Overflow**: Tag `apache-spark`
- **Databricks Community**: [community.databricks.com](https://community.databricks.com/)
- **Spark User Mailing List**: [user@spark.apache.org](mailto:user@spark.apache.org)
- **Issues de este repo**: Para preguntas específicas de migración Oracle

---

¡Buena suerte en tu journey de Oracle Exadata a Apache Spark! 🚀
