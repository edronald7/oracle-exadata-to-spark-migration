-- Oracle: Integraciones del Ecosistema

-- Oracle se integra principalmente vía:
-- 1. Database Links (a otras bases Oracle/non-Oracle)
-- 2. External Tables (leer archivos CSV/JSON)
-- 3. SQL*Loader (bulk loading)
-- 4. Oracle GoldenGate (replicación/CDC)

-- =====================================================
-- Integración 1: Database Links (otra DB Oracle)
-- =====================================================

-- Crear database link
CREATE DATABASE LINK remote_db
CONNECT TO username IDENTIFIED BY password
USING '(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=remote-host)(PORT=1521))(CONNECT_DATA=(SERVICE_NAME=service)))';

-- Query a tabla remota
SELECT * FROM customers@remote_db WHERE region_id = 10;

-- Join entre local y remota
SELECT l.order_id, r.customer_name
FROM orders l
JOIN customers@remote_db r ON l.customer_id = r.customer_id;

-- ⚠️ Performance issue: Trae TODOS los datos de remote antes de join

-- =====================================================
-- Integración 2: External Tables (archivos CSV en S3)
-- =====================================================

-- Oracle 12c+ puede leer de S3 con DBMS_CLOUD
BEGIN
    DBMS_CLOUD.CREATE_CREDENTIAL(
        credential_name => 's3_cred',
        username => 'AWS_ACCESS_KEY',
        password => 'AWS_SECRET_KEY'
    );
END;
/

-- Crear external table
CREATE TABLE ext_customers (
    customer_id NUMBER,
    name VARCHAR2(100),
    email VARCHAR2(100)
)
ORGANIZATION EXTERNAL (
    TYPE ORACLE_LOADER
    DEFAULT DIRECTORY data_dir
    ACCESS PARAMETERS (
        RECORDS DELIMITED BY NEWLINE
        FIELDS TERMINATED BY ','
    )
    LOCATION ('s3://bucket/customers.csv')
)
REJECT LIMIT UNLIMITED;

-- Query como tabla normal
SELECT * FROM ext_customers;

-- =====================================================
-- Integración 3: SQL*Loader (bulk load)
-- =====================================================

-- Control file (customers.ctl):
/*
LOAD DATA
INFILE 'customers.csv'
INTO TABLE customers
FIELDS TERMINATED BY ','
(customer_id, name, email)
*/

-- Ejecutar desde shell:
-- sqlldr userid=user/pass control=customers.ctl

-- =====================================================
-- Integración 4: Oracle GoldenGate (CDC to Kafka)
-- =====================================================

-- GoldenGate captura cambios y publica a Kafka
-- Configuración (ggsci):
/*
ADD EXTRACT ext1, TRANLOG, BEGIN NOW
ADD EXTTRAIL /ogg/dirdat/et, EXTRACT ext1

EDIT PARAMS ext1
EXTRACT ext1
USERID gguser, PASSWORD ggpass
EXTTRAIL /ogg/dirdat/et
TABLE customers;
*/

-- Publish to Kafka:
/*
ADD REPLICAT rep1, EXTTRAIL /ogg/dirdat/et
EDIT PARAMS rep1
REPLICAT rep1
TARGETDB LIBFILE libggjava.so SET property=kafka.properties
MAP customers, TARGET customers_topic;
*/

-- =====================================================
-- Integración 5: REST API con ORDS
-- =====================================================

-- Oracle REST Data Services expone tablas como REST APIs
-- Configuración:
BEGIN
    ORDS.ENABLE_SCHEMA(
        p_enabled => TRUE,
        p_schema => 'MYSCHEMA'
    );
    
    ORDS.DEFINE_SERVICE(
        p_module_name => 'customers',
        p_base_path => '/customers/'
    );
    
    ORDS.DEFINE_TEMPLATE(
        p_module_name => 'customers',
        p_pattern => ':id'
    );
END;
/

-- Acceso vía HTTP:
-- GET http://oracle-host:8080/ords/myschema/customers/123

-- =====================================================
-- Integración 6: JDBC (desde aplicaciones)
-- =====================================================

-- Connection string típico:
-- jdbc:oracle:thin:@//hostname:1521/service_name

-- En Python:
/*
import cx_Oracle
conn = cx_Oracle.connect('user/pass@hostname:1521/service')
cursor = conn.cursor()
cursor.execute("SELECT * FROM customers")
*/

-- En Java:
/*
Class.forName("oracle.jdbc.OracleDriver");
Connection conn = DriverManager.getConnection(
    "jdbc:oracle:thin:@hostname:1521:orcl", "user", "pass"
);
*/

-- =====================================================
-- Limitaciones
-- =====================================================

-- 1. Database links son lentos para big data
-- 2. External tables limitadas en formatos (no Parquet nativo)
-- 3. No integración directa con Kafka/modern streaming
-- 4. GoldenGate requiere licencia cara
-- 5. No integración nativa con cloud data warehouses
