# Examen Segundo Parcial — Pipeline de Datos Contenerizado (DataMart)

- **Alumno:** Said Giuliano Ayala Carrasco
- **Matrícula:** `125054061`
- **Último dígito de matrícula:** `1`
- **Pregunta de negocio asignada (`0` o `1`):**
  > **Ingreso total (`cantidad × precio_unitario`) por categoría y mes.**

---

## Estructura del Proyecto

```text
examen-p2-125054061/
├── README.md              # cómo levantar, evidencias, comparativa y teoría
├── .gitignore             # incluye *.csv y .env
├── .env.example           # plantilla de variables de entorno
├── generar_dataset.py     # script generador de ventas_125054061.csv
├── docker-compose.yml     # tres servicios (hadoop, db, api), red y volúmenes
├── hadoop/
│   └── Dockerfile         # Debian + OpenJDK 17 + Python 3 + Hadoop 3.3.6 + OpenSSH Server
├── mapreduce/
│   ├── mapper.py          # Mapper en Python (ignora encabezado y maneja errores)
│   ├── reducer.py         # Reducer en Python (agrupa y suma ingreso por categoría y mes)
│   └── secuencial.py      # Procesamiento secuencial en Python para comparativa
├── api/
│   ├── Dockerfile         # Python 3.11 + Flask + psycopg2 + OpenSSH Client
│   ├── requirements.txt   # Dependencias de la API
│   └── app.py             # API REST CRUD conectada a db por nombre de servicio
├── scripts/
│   ├── cargar_resultados.py # Lee part-00000 e inserta los registros en PostgreSQL
│   ├── ejecutar_pruebas.sh  # Script automatizado para correr el pipeline completo
│   └── probar_api_y_ssh.sh  # Script de verificación de SSH entre contenedores y API
└── evidencias/            # Logs y salidas reales de cada etapa
```

---

## Pasos para Reproducir el Ambiente Completo

### 1. Preparar el archivo `.env` y el dataset (`ventas_125054061.csv`)
```bash
cp .env.example .env
python3 generar_dataset.py 125054061
```
*(El dataset se genera en `data/input/ventas_125054061.csv` con 5,000,000 de registros, ~352 MB, y se monta como volumen de solo lectura en `/data/input`).*

### 2. Levantar todo el ambiente con un solo comando
```bash
docker compose up --build -d
```

---

## Evidencias y Salidas Reales

*(Todos los archivos completos se encuentran también en la carpeta [`evidencias/`](./evidencias)).*

### Parte A1 — `hadoop version` dentro del contenedor
Comando:
```bash
docker exec datamart_hadoop hadoop version
```
Salida ([`evidencias/01_hadoop_version.txt`](./evidencias/01_hadoop_version.txt)):
```text
Hadoop 3.3.6
Source code repository https://github.com/apache/hadoop.git -r 1be78238728da9266a4f88195058f08fd012bf9c
Compiled by ubuntu on 2023-06-18T08:22Z
Compiled on platform linux-x86_64
Compiled with protoc 3.7.1
From source with checksum 5652179ad55f76cb287d9c633bb53bbd
This command was run using /opt/hadoop/share/hadoop/common/hadoop-common-3.3.6.jar
```

---

### Parte B — Acceso SSH sin contraseña (llaves RSA)

1. **Dentro del contenedor `hadoop` (`ssh localhost`):**
   ```bash
   docker exec datamart_hadoop ssh localhost "hostname && whoami && hadoop version | head -n 1"
   ```
   Salida ([`evidencias/02_ssh_localhost.txt`](./evidencias/02_ssh_localhost.txt)):
   ```text
   SSH localhost exitoso en host: hadoop - Usuario: root
   Hadoop 3.3.6
   ```

2. **Desde el contenedor `api` hacia `hadoop` por nombre de servicio (`ssh root@hadoop` y `ssh hadoop@hadoop`):**
   ```bash
   docker exec datamart_api ssh root@hadoop "hostname && whoami"
   docker exec datamart_api ssh hadoop@hadoop "hostname && whoami"
   ```
   Salida ([`evidencias/02_ssh_desde_api.txt`](./evidencias/02_ssh_desde_api.txt)):
   ```text
   === Prueba SSH desde contenedor API hacia contenedor Hadoop ===
   Conexion SSH exitosa desde API -> usuario: root | host: hadoop
   Conexion SSH exitosa desde API -> usuario: hadoop | host: hadoop
   ```

---

### Parte C1 — Procesamiento con Hadoop Streaming MapReduce

Comando ejecutado:
```bash
hadoop jar $HADOOP_HOME/share/hadoop/tools/lib/hadoop-streaming-*.jar \
  -input /data/input/ventas_125054061.csv \
  -output /data/output/resultado \
  -mapper "python3 /mapreduce/mapper.py" \
  -reducer "python3 /mapreduce/reducer.py"
```

Primeros registros de la salida `/data/output/resultado/part-00000` ([`evidencias/03_part-00000.txt`](./evidencias/03_part-00000.txt), 121 registros en total):
```text
Abarrotes	2025-01	341315262.46
Abarrotes	2025-02	312293754.55
Abarrotes	2025-03	344677454.95
Abarrotes	2025-04	332897395.32
Abarrotes	2025-05	344373477.54
Abarrotes	2025-06	334086373.09
Abarrotes	2025-07	346661175.80
Abarrotes	2025-08	349154046.78
Abarrotes	2025-09	332820070.18
Abarrotes	2025-10	346306405.44
Abarrotes	2025-11	337181602.57
Abarrotes	2025-12	343318449.58
Bebidas	2025-01	347893591.10
Bebidas	2025-02	313669927.57
Bebidas	2025-03	346297348.83
Bebidas	2025-04	331525802.62
Bebidas	2025-05	343869849.99
Bebidas	2025-06	335164207.57
Bebidas	2025-07	342359073.53
Bebidas	2025-08	345986561.57
```

---

### Parte C2 — Comparativa de Rendimiento: MapReduce vs. Script Secuencial

| Método de Procesamiento | Tiempo Real (`real`) | Tiempo CPU Usuario (`user`) | Tiempo Sistema (`sys`) | Registros Agrupados | ¿Resultados Coinciden? |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Hadoop Streaming MapReduce** (`mapper.py` + `reducer.py`) | **109.53 s** | 45.44 s | 9.67 s | 121 | Sí (100% idénticos) |
| **Script Secuencial en Python** (`secuencial.py`) | **63.35 s** | 15.02 s | 2.45 s | 121 | Sí (`diff` = 0 diferencias) |

Verificación de igualdad ([`evidencias/04_diff_comparativa.txt`](./evidencias/04_diff_comparativa.txt)):
```text
EXITO: Los resultados de MapReduce (part-00000) y Secuencial (secuencial.txt) son 100% IDENTICOS.
```

#### Explicación de la Comparativa (1 párrafo)
En este escenario de prueba (un archivo CSV de ~352 MB con 5,000,000 de registros procesado en un único contenedor en modo *standalone*), el **script secuencial en Python (`63.35 s`) fue 1.73 veces más rápido que Hadoop MapReduce (`109.53 s`)**. Esto se debe a que Hadoop Streaming introduce una sobrecarga (*overhead*) importante al levantar la Máquina Virtual de Java (JVM), dividir el archivo en *splits* (11 splits locales), crear subprocesos externos de Python para `mapper.py` y `reducer.py`, serializar y transferir los 5 millones de registros como texto plano a través de tuberías estándar (`stdin`/`stdout`), y ejecutar la fase intermedia de ordenamiento y volcado en disco (*Sort & Shuffle*) antes de reducir. En cambio, el script secuencial realiza una única lectura lineal del archivo acumulando directamente los totales en una tabla hash en memoria RAM (`defaultdict`), evitando la escritura intermedia en disco y la comunicación entre procesos Java-Python. MapReduce resulta más rápido cuando el volumen de datos escala a decenas de gigabytes o terabytes y el trabajo se distribuye horizontalmente sobre un clúster real de múltiples nodos.

---

### Parte D — Integración con PostgreSQL y API REST

1. **Carga de `part-00000` en la base de datos ([`evidencias/05_carga_bd.txt`](./evidencias/05_carga_bd.txt)):**
   ```bash
   docker exec datamart_hadoop python3 /scripts/cargar_resultados.py /data/output/resultado/part-00000
   # Salida: Se cargaron exitosamente 121 registros desde '/data/output/resultado/part-00000' hacia PostgreSQL.
   ```

2. **Consulta de todos los registros (`GET /resultados`, [`evidencias/06_api_get_todos.json`](./evidencias/06_api_get_todos.json)):**
   ```bash
   curl http://localhost:5050/resultados
   ```

3. **Filtro por clave de negocio (`GET /resultados/<clave>`, [`evidencias/07_api_get_clave_categoria.json`](./evidencias/07_api_get_clave_categoria.json) y [`evidencias/08_api_get_clave_mes.json`](./evidencias/08_api_get_clave_mes.json)):**
   - Por categoría (`GET /resultados/Electronica`):
     ```json
     {
       "clave_buscada": "Electronica",
       "total_registros": 12,
       "resultados": [
         {"id": 37, "categoria": "Electronica", "mes": "2025-01", "ingreso_total": 350853006.57},
         {"id": 38, "categoria": "Electronica", "mes": "2025-02", "ingreso_total": 314257352.97}
       ]
     }
     ```
   - Por mes (`GET /resultados/2025-01`): devuelve las 10 categorías para enero de 2025.

4. **Endpoints de escritura CRUD (`POST`, `PUT`, `DELETE`):**
   - `POST /resultados` ([`evidencias/09_api_post.json`](./evidencias/09_api_post.json)):
     ```json
     {"mensaje":"Registro guardado correctamente","resultado":{"categoria":"PruebaCRUD","id":122,"ingreso_total":12345.67,"mes":"2025-12"}}
     ```
   - `PUT /resultados/PruebaCRUD_2025-12` ([`evidencias/10_api_put.json`](./evidencias/10_api_put.json)):
     ```json
     {"actualizados":[{"categoria":"PruebaCRUD","id":122,"ingreso_total":54321.99,"mes":"2025-12"}],"mensaje":"Registro(s) actualizado(s) correctamente"}
     ```
   - `DELETE /resultados/PruebaCRUD_2025-12` ([`evidencias/11_api_delete.json`](./evidencias/11_api_delete.json)):
     ```json
     {"eliminados":[{"categoria":"PruebaCRUD","id":122,"ingreso_total":54321.99,"mes":"2025-12"}],"mensaje":"Registro(s) eliminado(s) correctamente"}
     ```

5. **Persistencia de datos tras `docker compose down` y `docker compose up -d`:**
   ```bash
   docker compose down
   docker compose up -d
   curl http://localhost:5050/resultados/Electronica
   ```
   Los 121 registros permanecen en PostgreSQL gracias al volumen nombrado `pg_data`.

---

## Parte E — Teoría (15 pts)

### 1. Explica la diferencia entre los modos standalone, pseudo-distribuido y totalmente distribuido de Hadoop. ¿En cuál de ellos se usa HDFS?
En el modo **standalone (local)** no se ejecutan demonios y todo corre dentro de un solo proceso JVM usando el sistema de archivos local del sistema operativo, ideal para desarrollo y depuración. En el modo **pseudo-distribuido**, cada demonio de Hadoop (`NameNode`, `DataNode`, `ResourceManager`, `NodeManager`) corre en un proceso JVM separado pero dentro de una misma máquina, coordinándose por SSH local. En el modo **totalmente distribuido**, los demonios se despliegan repartidos en múltiples nodos reales (físicos o virtuales) conectados en red. **Se utiliza HDFS tanto en el modo pseudo-distribuido como en el modo totalmente distribuido** (en standalone se usa únicamente el sistema de archivos local).

### 2. ¿Por qué el dataset se monta como volumen y no se copia dentro de la imagen con `COPY`? Menciona al menos dos razones.
1. **Ligereza y eficiencia de la imagen:** Copiar un archivo CSV de ~400 MB con `COPY` dentro de la imagen aumentaría innecesariamente su tamaño en disco, haciendo mucho más lento el envío del contexto de construcción (`docker build`) y la subida/descarga de capas en el registro.
2. **Desacoplamiento entre código y datos:** Montar el dataset como volumen permite actualizar el archivo de entrada, cambiar de dataset según la matrícula o protegerlo en modo solo lectura (`:ro`) en tiempo de ejecución sin tener que reconstruir la imagen Docker cada vez que cambian los datos.

### 3. ¿Qué ocurre con los datos de la base de datos al ejecutar `docker compose down`? ¿Y con `docker compose down -v`?
Al ejecutar **`docker compose down`**, Docker detiene y elimina los contenedores y la red del proyecto, pero **conserva intactos los volúmenes nombrados** (como `pg_data`), por lo que al volver a ejecutar `docker compose up` los registros de PostgreSQL siguen persistidos. Por el contrario, al ejecutar **`docker compose down -v`**, la bandera `-v` (`--volumes`) elimina también los volúmenes nombrados asociados al compose, borrando permanentemente todos los datos de la base de datos.

### 4. ¿Por qué MapReduce no siempre es más rápido que un script secuencial con un archivo de 400 MB? ¿A partir de qué condiciones conviene?
Con un archivo de 400 MB en un solo nodo, MapReduce introduce una sobrecarga (*overhead*) considerable: inicialización de la JVM, creación de subprocesos en Hadoop Streaming, paso de datos por tuberías (`stdin`/`stdout`), escritura intermedia en disco y ordenamiento (*Sort & Shuffle*), mientras que un script secuencial en Python procesa el archivo directamente en memoria RAM en una sola pasada. **MapReduce conviene a partir de volúmenes masivos de datos** (decenas de GB, TB o PB) que superan la memoria o capacidad de una sola máquina y cuando se ejecuta sobre un **clúster distribuido de múltiples nodos**, donde el paralelismo real entre servidores supera ampliamente el costo de coordinación.

### 5. Diferencia entre `CMD` y `ENTRYPOINT`, y entre `COPY` y `ADD`.
- **`CMD` vs `ENTRYPOINT`:** `ENTRYPOINT` define el comando o ejecutable fijo principal que siempre ejecutará el contenedor al iniciar, mientras que `CMD` define el comando por defecto o los argumentos por defecto que se pasan al `ENTRYPOINT` y que pueden ser sobrescritos fácilmente al pasar argumentos al final de `docker run`.
- **`COPY` vs `ADD`:** Ambos copian archivos hacia la imagen, pero `COPY` realiza únicamente copias directas y explícitas de archivos locales del contexto de construcción (siendo la práctica recomendada), mientras que `ADD` además descomprime automáticamente archivos `.tar` locales y permite descargar archivos desde URLs remotas.

---

## Parte F — Guía Rápida para la Defensa Oral

1. **Cambiar el puerto expuesto de la API y volver a levantar el servicio:**
   - Cambiar `API_PORT=8080` en `.env` y ejecutar `docker compose up -d api`.
2. **Modificar el mapper/reducer para otra agregación (ej. de suma a promedio o agregar filtro por mes):**
   - *Filtro por mes en `mapper.py`*: añadir `if mes != "2025-01": continue` antes del `print`.
   - *De suma a promedio en `reducer.py`*: agregar un contador `conteo += 1` junto con `current_total += val` y emitir `current_total / conteo`.
3. **Borrar el volumen de la base de datos, levantar de nuevo y recargar los resultados:**
   ```bash
   docker compose down -v
   docker compose up -d
   docker exec datamart_hadoop python3 /scripts/cargar_resultados.py /data/output/resultado/part-00000
   ```
