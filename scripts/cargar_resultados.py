#!/usr/bin/env python3
"""
Script de integración: lee la salida del job de Hadoop MapReduce (part-00000)
e inserta los registros en la tabla resultados_ventas de PostgreSQL.

Uso:
  python3 scripts/cargar_resultados.py [/data/output/resultado/part-00000]
"""
import os
import sys
import psycopg2


def get_connection():
    return psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "db"),
        port=int(os.environ.get("POSTGRES_PORT", "5432")),
        dbname=os.environ.get("POSTGRES_DB", "datamart_db"),
        user=os.environ.get("POSTGRES_USER", "datamart_user"),
        password=os.environ.get("POSTGRES_PASSWORD", "datamart_secret_pass"),
    )


def cargar_archivo(filepath: str):
    if not os.path.exists(filepath):
        print(f"Error: No se encontró el archivo de resultados en '{filepath}'", file=sys.stderr)
        sys.exit(1)

    registros = []
    with open(filepath, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line:
                continue

            # Soportar formato "<categoria>\t<mes>\t<ingreso>" o "<categoria>,<mes>\t<ingreso>"
            parts = line.split("\t")
            if len(parts) == 3:
                categoria, mes, ingreso_str = parts[0].strip(), parts[1].strip(), parts[2].strip()
            elif len(parts) == 2 and "," in parts[0]:
                cat_mes, ingreso_str = parts[0].strip(), parts[1].strip()
                categoria, mes = cat_mes.split(",", 1)
            else:
                continue

            try:
                ingreso_total = round(float(ingreso_str), 2)
                registros.append((categoria, mes, ingreso_total))
            except ValueError:
                continue

    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS resultados_ventas (
                        id SERIAL PRIMARY KEY,
                        categoria VARCHAR(100) NOT NULL,
                        mes VARCHAR(20) NOT NULL,
                        ingreso_total NUMERIC(15, 2) NOT NULL,
                        UNIQUE (categoria, mes)
                    );
                    """
                )
                for categoria, mes, ingreso_total in registros:
                    cur.execute(
                        """
                        INSERT INTO resultados_ventas (categoria, mes, ingreso_total)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (categoria, mes)
                        DO UPDATE SET ingreso_total = EXCLUDED.ingreso_total;
                        """,
                        (categoria, mes, ingreso_total),
                    )
        print(f"Se cargaron exitosamente {len(registros)} registros desde '{filepath}' hacia PostgreSQL.")
    finally:
        conn.close()


if __name__ == "__main__":
    ruta_part = sys.argv[1] if len(sys.argv) > 1 else "/data/output/resultado/part-00000"
    cargar_archivo(ruta_part)

