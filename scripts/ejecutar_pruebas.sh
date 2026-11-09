#!/usr/bin/env bash
set -e

mkdir -p /data/output/evidencias

echo "=========================================="
echo "1. Verificando Variables de Entorno y Hadoop Version"
echo "=========================================="
echo "JAVA_HOME=$JAVA_HOME"
echo "HADOOP_HOME=$HADOOP_HOME"
echo "PATH=$PATH"
hadoop version | tee /data/output/evidencias/01_hadoop_version.txt

echo ""
echo "=========================================="
echo "2. Verificando SSH sin contraseña (localhost)"
echo "=========================================="
ssh localhost "echo 'SSH localhost exitoso en host:' \$(hostname) '- Usuario:' \$(whoami) && hadoop version | head -n 1" | tee /data/output/evidencias/02_ssh_localhost.txt

echo ""
echo "=========================================="
echo "3. Ejecutando Job MapReduce (Hadoop Streaming)"
echo "=========================================="
rm -rf /data/output/resultado
/usr/bin/time -p hadoop jar $HADOOP_HOME/share/hadoop/tools/lib/hadoop-streaming-*.jar \
  -input /data/input/ventas_125054061.csv \
  -output /data/output/resultado \
  -mapper "python3 /mapreduce/mapper.py" \
  -reducer "python3 /mapreduce/reducer.py" 2>&1 | tee /data/output/evidencias/03_mapreduce_job.txt

echo ""
echo "--- Primeras 20 líneas de part-00000 ---"
head -n 20 /data/output/resultado/part-00000
echo "Total de registros en part-00000: $(wc -l < /data/output/resultado/part-00000)"
cp /data/output/resultado/part-00000 /data/output/evidencias/03_part-00000.txt

echo ""
echo "=========================================="
echo "4. Ejecutando Script Secuencial y Comparando"
echo "=========================================="
/usr/bin/time -p python3 /mapreduce/secuencial.py /data/input/ventas_125054061.csv /data/output/secuencial.txt 2>&1 | tee /data/output/evidencias/04_secuencial_tiempo.txt

echo ""
echo "--- Comparando resultados (diff part-00000 vs secuencial.txt) ---"
if diff -u /data/output/resultado/part-00000 /data/output/secuencial.txt > /data/output/evidencias/04_diff_comparativa.txt; then
    echo "EXITO: Los resultados de MapReduce (part-00000) y Secuencial (secuencial.txt) son 100% IDENTICOS." | tee -a /data/output/evidencias/04_diff_comparativa.txt
else
    echo "DIFERENCIAS ENCONTRADAS"
fi

echo ""
echo "=========================================="
echo "5. Cargando resultados en PostgreSQL"
echo "=========================================="
python3 /scripts/cargar_resultados.py /data/output/resultado/part-00000 | tee /data/output/evidencias/05_carga_bd.txt

echo ""
echo "=========================================="
echo "6. Probando Endpoints de la API REST"
echo "=========================================="
echo "--- GET /resultados (primeros 40 líneas) ---"
curl -s http://api:5050/resultados | tee /data/output/evidencias/06_api_get_todos.json | head -n 40

echo ""
echo "--- GET /resultados/Electronica ---"
curl -s http://api:5050/resultados/Electronica | tee /data/output/evidencias/07_api_get_clave_categoria.json

echo ""
echo "--- GET /resultados/2025-01 ---"
curl -s http://api:5050/resultados/2025-01 | tee /data/output/evidencias/08_api_get_clave_mes.json

echo ""
echo "--- POST /resultados (Escritura CRUD) ---"
curl -s -X POST http://api:5050/resultados \
  -H "Content-Type: application/json" \
  -d '{"categoria": "PruebaCRUD", "mes": "2025-12", "ingreso_total": 12345.67}' | tee /data/output/evidencias/09_api_post.json

echo ""
echo "--- PUT /resultados/PruebaCRUD_2025-12 (Actualización CRUD) ---"
curl -s -X PUT http://api:5050/resultados/PruebaCRUD_2025-12 \
  -H "Content-Type: application/json" \
  -d '{"ingreso_total": 54321.99}' | tee /data/output/evidencias/10_api_put.json

echo ""
echo "--- DELETE /resultados/PruebaCRUD_2025-12 (Eliminación CRUD) ---"
curl -s -X DELETE http://api:5050/resultados/PruebaCRUD_2025-12 | tee /data/output/evidencias/11_api_delete.json
echo ""
echo "PIPELINE COMPLETADO EXITOSAMENTE"
