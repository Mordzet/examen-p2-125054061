#!/usr/bin/env python3
"""
Mapper para Hadoop Streaming - Matrícula 125054061 (terminación 1)
Pregunta de negocio (0 o 1):
  Ingreso total (cantidad * precio_unitario) por categoría y mes.

Formato de entrada CSV:
  id,fecha_hora,tienda,categoria,producto,cantidad,precio_unitario,metodo_pago
Formato de salida hacia Reducer:
  <categoria>,<mes>\t<ingreso>
"""
import sys


def main():
    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue

        # Ignorar el encabezado del CSV
        if line.startswith("id,"):
            continue

        parts = line.split(",")
        if len(parts) != 8:
            # Línea mal formada: se ignora sin truncar el job
            continue

        try:
            fecha_hora = parts[1].strip()
            categoria = parts[3].strip()
            cantidad = int(parts[5].strip())
            precio_unitario = float(parts[6].strip())

            # Extraer año-mes (YYYY-MM) de fecha_hora ("YYYY-MM-DD HH:MM:SS")
            if len(fecha_hora) < 7 or not categoria:
                continue
            mes = fecha_hora[:7]

            ingreso = round(cantidad * precio_unitario, 2)
            print(f"{categoria},{mes}\t{ingreso:.2f}")
        except (ValueError, IndexError):
            # Ignorar registros con datos numéricos inválidos sin detener el job
            continue


if __name__ == "__main__":
    main()

