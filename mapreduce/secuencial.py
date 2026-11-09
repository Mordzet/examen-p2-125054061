#!/usr/bin/env python3
"""
Procesamiento secuencial - Matrícula 125054061 (terminación 1)
Pregunta de negocio (0 o 1):
  Ingreso total (cantidad * precio_unitario) por categoría y mes.

Uso:
  python3 secuencial.py /data/input/ventas_125054061.csv [/data/output/secuencial.txt]
"""
import sys
import time
from collections import defaultdict


def procesar_secuencial(csv_path: str, output_path: str = None):
    inicio = time.perf_counter()
    totales = defaultdict(float)

    with open(csv_path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("id,"):
                continue

            parts = line.split(",")
            if len(parts) != 8:
                continue

            try:
                fecha_hora = parts[1].strip()
                categoria = parts[3].strip()
                cantidad = int(parts[5].strip())
                precio_unitario = float(parts[6].strip())

                if len(fecha_hora) < 7 or not categoria:
                    continue
                mes = fecha_hora[:7]

                ingreso = round(cantidad * precio_unitario, 2)
                clave = (categoria, mes)
                totales[clave] = round(totales[clave] + ingreso, 2)
            except (ValueError, IndexError):
                continue

    lineas_salida = []
    for (categoria, mes) in sorted(totales.keys()):
        lineas_salida.append(f"{categoria}\t{mes}\t{totales[(categoria, mes)]:.2f}")

    if output_path:
        with open(output_path, "w", encoding="utf-8") as out:
            out.write("\n".join(lineas_salida) + "\n")
    else:
        for linea in lineas_salida:
            print(linea)

    duracion = time.perf_counter() - inicio
    print(f"\n[Secuencial] Registros agrupados: {len(lineas_salida)} | Tiempo: {duracion:.4f} segundos", file=sys.stderr)


if __name__ == "__main__":
    input_csv = sys.argv[1] if len(sys.argv) > 1 else "/data/input/ventas_125054061.csv"
    out_file = sys.argv[2] if len(sys.argv) > 2 else None
    procesar_secuencial(input_csv, out_file)

