import os
import time
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, jsonify, request

app = Flask(__name__)


def get_db_connection(retries: int = 10, delay: int = 2):
    host = os.environ.get("POSTGRES_HOST", "db")
    port = int(os.environ.get("POSTGRES_PORT", "5432"))
    dbname = os.environ.get("POSTGRES_DB")
    user = os.environ.get("POSTGRES_USER")
    password = os.environ.get("POSTGRES_PASSWORD")

    last_err = None
    for _ in range(retries):
        try:
            conn = psycopg2.connect(
                host=host,
                port=port,
                dbname=dbname,
                user=user,
                password=password,
                cursor_factory=RealDictCursor,
            )
            return conn
        except psycopg2.OperationalError as err:
            last_err = err
            time.sleep(delay)
    raise last_err


def init_db():
    conn = get_db_connection()
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
    conn.close()


def serialize_row(row: dict) -> dict:
    return {
        "id": row["id"],
        "categoria": row["categoria"],
        "mes": row["mes"],
        "ingreso_total": float(row["ingreso_total"]),
    }


@app.route("/", methods=["GET"])
def index():
    return jsonify(
        {
            "servicio": "API DataMart - Resultados MapReduce",
            "matricula": os.environ.get("MATRICULA", "125054061"),
            "pregunta": "Ingreso total (cantidad x precio_unitario) por categoría y mes",
            "endpoints": {
                "GET /resultados": "Obtiene todos los registros",
                "GET /resultados/<clave>": "Filtra por categoría (ej. Electronica), mes (ej. 2025-01) o clave compuesta (ej. Electronica_2025-01)",
                "POST /resultados": "Inserta o actualiza un registro (categoria, mes, ingreso_total)",
                "PUT /resultados/<id>": "Actualiza un registro existente por su ID o clave",
                "DELETE /resultados/<id>": "Elimina un registro por su ID o clave",
            },
        }
    )


@app.route("/resultados", methods=["GET"])
def obtener_todos():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, categoria, mes, ingreso_total
                FROM resultados_ventas
                ORDER BY categoria ASC, mes ASC;
                """
            )
            rows = cur.fetchall()
        return jsonify(
            {
                "total_registros": len(rows),
                "resultados": [serialize_row(r) for r in rows],
            }
        ), 200
    finally:
        conn.close()


@app.route("/resultados/<clave>", methods=["GET"])
def obtener_por_clave(clave: str):
    id_val = int(clave) if clave.isdigit() else -1
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Permite filtrar por categoría (ej. Electronica), por mes (ej. 2025-01),
            # por clave compuesta (ej. Electronica_2025-01 o Electronica-2025-01) o por ID numérico
            cur.execute(
                """
                SELECT id, categoria, mes, ingreso_total
                FROM resultados_ventas
                WHERE LOWER(categoria) = LOWER(%s)
                   OR mes = %s
                   OR LOWER(categoria || '_' || mes) = LOWER(%s)
                   OR LOWER(categoria || '-' || mes) = LOWER(%s)
                   OR id = %s
                ORDER BY categoria ASC, mes ASC;
                """,
                (clave, clave, clave, clave, id_val),
            )
            rows = cur.fetchall()

        if not rows:
            return jsonify({"error": f"No se encontraron resultados para la clave '{clave}'"}), 404

        return jsonify(
            {
                "clave_buscada": clave,
                "total_registros": len(rows),
                "resultados": [serialize_row(r) for r in rows],
            }
        ), 200
    finally:
        conn.close()


@app.route("/resultados", methods=["POST"])
def crear_resultado():
    data = request.get_json(silent=True) or {}
    categoria = data.get("categoria")
    mes = data.get("mes")
    ingreso_total = data.get("ingreso_total")

    if not categoria or not mes or ingreso_total is None:
        return jsonify({"error": "Se requieren los campos 'categoria', 'mes' e 'ingreso_total'"}), 400

    try:
        ingreso_val = round(float(ingreso_total), 2)
    except ValueError:
        return jsonify({"error": "'ingreso_total' debe ser un número válido"}), 400

    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO resultados_ventas (categoria, mes, ingreso_total)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (categoria, mes)
                    DO UPDATE SET ingreso_total = EXCLUDED.ingreso_total
                    RETURNING id, categoria, mes, ingreso_total;
                    """,
                    (str(categoria).strip(), str(mes).strip(), ingreso_val),
                )
                row = cur.fetchone()
        return jsonify({"mensaje": "Registro guardado correctamente", "resultado": serialize_row(row)}), 201
    finally:
        conn.close()


@app.route("/resultados/<identificador>", methods=["PUT"])
def actualizar_resultado(identificador: str):
    data = request.get_json(silent=True) or {}
    if "ingreso_total" not in data:
        return jsonify({"error": "Se requiere el campo 'ingreso_total' para actualizar"}), 400

    try:
        ingreso_val = round(float(data["ingreso_total"]), 2)
    except ValueError:
        return jsonify({"error": "'ingreso_total' debe ser un número válido"}), 400

    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                if identificador.isdigit():
                    cur.execute(
                        """
                        UPDATE resultados_ventas
                        SET ingreso_total = %s
                        WHERE id = %s
                        RETURNING id, categoria, mes, ingreso_total;
                        """,
                        (ingreso_val, int(identificador)),
                    )
                else:
                    cur.execute(
                        """
                        UPDATE resultados_ventas
                        SET ingreso_total = %s
                        WHERE LOWER(categoria || '_' || mes) = LOWER(%s)
                           OR LOWER(categoria) = LOWER(%s)
                        RETURNING id, categoria, mes, ingreso_total;
                        """,
                        (ingreso_val, identificador, identificador),
                    )
                rows = cur.fetchall()

        if not rows:
            return jsonify({"error": f"No se encontró registro para '{identificador}'"}), 404

        return jsonify(
            {
                "mensaje": "Registro(s) actualizado(s) correctamente",
                "actualizados": [serialize_row(r) for r in rows],
            }
        ), 200
    finally:
        conn.close()


@app.route("/resultados/<identificador>", methods=["DELETE"])
def eliminar_resultado(identificador: str):
    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                if identificador.isdigit():
                    cur.execute(
                        """
                        DELETE FROM resultados_ventas
                        WHERE id = %s
                        RETURNING id, categoria, mes, ingreso_total;
                        """,
                        (int(identificador),),
                    )
                else:
                    cur.execute(
                        """
                        DELETE FROM resultados_ventas
                        WHERE LOWER(categoria || '_' || mes) = LOWER(%s)
                           OR LOWER(categoria) = LOWER(%s)
                        RETURNING id, categoria, mes, ingreso_total;
                        """,
                        (identificador, identificador),
                    )
                rows = cur.fetchall()

        if not rows:
            return jsonify({"error": f"No se encontró registro para eliminar con '{identificador}'"}), 404

        return jsonify(
            {
                "mensaje": "Registro(s) eliminado(s) correctamente",
                "eliminados": [serialize_row(r) for r in rows],
            }
        ), 200
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("API_PORT", "5000"))
    app.run(host="0.0.0.0", port=port)

