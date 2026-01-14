"""
Script maestro para generar todos los datasets necesarios.
Ejecuta todos los generadores en secuencia.

Uso:
    python generate_all.py --size small --output /tmp/testdata
    python generate_all.py --size large --output s3://bucket/bronze --format delta
"""

import argparse
import subprocess
import sys
from datetime import datetime

def run_command(cmd, description):
    """Ejecuta comando y muestra progreso"""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"{'='*60}")
    print(f"📝 Comando: {' '.join(cmd)}\n")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"✅ {description} - COMPLETADO")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FALLÓ")
        print(f"Error: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Genera todos los datasets de prueba"
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Ruta base de salida (local, s3://, gs://, abfss://)"
    )
    parser.add_argument(
        "--size",
        type=str,
        default="medium",
        choices=["small", "medium", "large", "xlarge"],
        help="Tamaño del dataset (default: medium)"
    )
    parser.add_argument(
        "--format",
        type=str,
        default="parquet",
        choices=["parquet", "delta", "iceberg"],
        help="Formato de salida (default: parquet)"
    )
    parser.add_argument(
        "--skip-fact-sales",
        action="store_true",
        help="Saltar generación de fact_sales (útil si ya existe)"
    )
    parser.add_argument(
        "--skip-dimensions",
        action="store_true",
        help="Saltar generación de dimensiones"
    )
    
    args = parser.parse_args()
    
    # Presets de configuración
    size_configs = {
        "small": {
            "fact_sales_rows": 10000,
            "products": 100,
            "stores": 10,
            "customers": 1000
        },
        "medium": {
            "fact_sales_rows": 1000000,
            "products": 1000,
            "stores": 100,
            "customers": 100000
        },
        "large": {
            "fact_sales_rows": 100000000,
            "products": 5000,
            "stores": 500,
            "customers": 1000000
        },
        "xlarge": {
            "fact_sales_rows": 1000000000,
            "products": 10000,
            "stores": 1000,
            "customers": 10000000
        }
    }
    
    config = size_configs[args.size]
    
    print("\n" + "="*60)
    print("🏗️  GENERACIÓN MASIVA DE DATOS")
    print("="*60)
    print(f"\n📊 Configuración:")
    print(f"   Size preset: {args.size}")
    print(f"   Output: {args.output}")
    print(f"   Format: {args.format}")
    print(f"   Fact sales rows: {config['fact_sales_rows']:,}")
    print(f"   Products: {config['products']:,}")
    print(f"   Stores: {config['stores']:,}")
    print(f"   Customers: {config['customers']:,}")
    
    start_time = datetime.now()
    success_count = 0
    total_steps = 2
    
    # 1. Generar fact_sales
    if not args.skip_fact_sales:
        cmd_fact_sales = [
            "python", "generate_fact_sales.py",
            "--rows", str(config["fact_sales_rows"]),
            "--output", f"{args.output}/fact_sales",
            "--format", args.format,
            "--size", args.size,
            "--stats"
        ]
        
        if run_command(cmd_fact_sales, "Generando fact_sales"):
            success_count += 1
    else:
        print("\n⏭️  Saltando fact_sales")
        success_count += 1
    
    # 2. Generar dimensiones
    if not args.skip_dimensions:
        cmd_dimensions = [
            "python", "generate_dimensions.py",
            "--output", args.output,
            "--format", args.format,
            "--products", str(config["products"]),
            "--stores", str(config["stores"]),
            "--customers", str(config["customers"])
        ]
        
        if run_command(cmd_dimensions, "Generando dimensiones"):
            success_count += 1
    else:
        print("\n⏭️  Saltando dimensiones")
        success_count += 1
    
    # Resumen final
    end_time = datetime.now()
    duration = end_time - start_time
    
    print("\n" + "="*60)
    print("📊 RESUMEN DE GENERACIÓN")
    print("="*60)
    print(f"\n✅ Completados: {success_count}/{total_steps}")
    print(f"⏱️  Duración total: {duration}")
    print(f"📁 Datos generados en: {args.output}/")
    
    print("\n📋 Estructura de archivos:")
    print(f"""
    {args.output}/
    ├── fact_sales/              # {config['fact_sales_rows']:,} registros
    │   └── sale_date=YYYY-MM-DD/
    ├── dim_region/              # 10 regiones
    ├── dim_product/             # {config['products']:,} productos
    ├── dim_store/               # {config['stores']:,} tiendas
    └── dim_customer/            # {config['customers']:,} clientes
    """)
    
    print("\n🚀 Próximos pasos:")
    print("   1. Verificar datos:")
    print(f"      pyspark --master local[*]")
    print(f"      spark.read.parquet('{args.output}/fact_sales').show()")
    print("\n   2. Ejecutar casos de migración:")
    print("      cd cases/01-hints-parallel")
    print("      spark-submit 3_pyspark.py")
    print("\n   3. Crear tablas en Spark SQL:")
    print(f"      CREATE TABLE fact_sales USING {args.format} LOCATION '{args.output}/fact_sales'")
    
    if success_count == total_steps:
        print("\n✅ GENERACIÓN COMPLETADA CON ÉXITO")
        return 0
    else:
        print("\n⚠️  GENERACIÓN COMPLETADA CON ERRORES")
        return 1

if __name__ == "__main__":
    sys.exit(main())
