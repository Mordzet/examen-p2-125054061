#!/usr/bin/env python3
"""
Reducer para Hadoop Streaming - Matrícula 125054061 (terminación 1)
Pregunta de negocio (0 o 1):
  Ingreso total (cantidad * precio_unitario) por categoría y mes.

Recibe desde stdin líneas ordenadas por clave:
  <categoria>,<mes>\t<ingreso>
Emite hacia stdout (part-00000):
  <categoria>\t<mes>\t<ingreso_total>
"""
import sys


def main():
    current_key = None
    current_total = 0.0

    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue

        parts = line.split("\t", 1)
        if len(parts) != 2:
            continue

        key, val_str = parts
        try:
            val = float(val_str)
        except ValueError:
            continue

        if key == current_key:
            current_total = round(current_total + val, 2)
        else:
            if current_key is not None:
                 emit_result(current_key, current_total)
            current_key = key
            current_total = round(val, 2)

    if current_key is not None:
        emit_result(current_key, current_total)


def emit_result(key: str, total: float):
    if "," in key:
        categoria, mes = key.split(",", 1)
        print(f"{categoria}\t{mes}\t{total:.2f}")
    else:
        print(f"{key}\t{total:.2f}")


if __name__ == "__main__":
    main()

