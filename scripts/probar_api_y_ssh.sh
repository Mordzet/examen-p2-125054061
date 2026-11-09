#!/usr/bin/env bash
set -e

mkdir -p /data/output/evidencias

echo "=== Prueba SSH desde contenedor API hacia contenedor Hadoop ===" | tee /data/output/evidencias/02_ssh_desde_api.txt
ssh root@hadoop "echo 'Conexion SSH exitosa desde API -> usuario:' \$(whoami) '| host:' \$(hostname)" | tee -a /data/output/evidencias/02_ssh_desde_api.txt
ssh hadoop@hadoop "echo 'Conexion SSH exitosa desde API -> usuario:' \$(whoami) '| host:' \$(hostname)" | tee -a /data/output/evidencias/02_ssh_desde_api.txt

echo ""
echo "=== GET /resultados/Electronica ==="
curl -s http://localhost:5050/resultados/Electronica | tee /data/output/evidencias/07_api_get_clave_categoria.json

echo ""
echo "=== GET /resultados/2025-01 ==="
curl -s http://localhost:5050/resultados/2025-01 | tee /data/output/evidencias/08_api_get_clave_mes.json
echo ""

