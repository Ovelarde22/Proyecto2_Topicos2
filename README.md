# Guía de configuración e Ingesta del sistema VitalCore

## 1. Requisitos del sistema y versiones:
* **Java 8 (JDK 8):** Descargar esta versión de Java para poder ejecutar Apache Cassandra 3.11.16 ([Descargar Zulu JDK 8](https://www.azul.com/downloads/?version=java-8-lts&os=windows&architecture=x86-64-bit&package=jdk#zulu)).
* **Python 2.7:** De uso exclusivo para habilitar el comando `cqlsh` en la consola de Cassandra. *Importante:* Marcar la casilla "Add python.exe to Path" durante su instalación.
* **Apache Cassandra 3.11.16:** Motor de base de datos NoSQL. Descargar el archivo `apache-cassandra-3.11.16-bin.tar.gz` ([Descargar aquí](https://archive.apache.org/dist/cassandra/3.11.16/)).
* **DBeaver:** Interfaz gráfica para interactuar fácilmente con Cassandra ([Descargar aquí](https://dbeaver.io/download/)).
* **Python 3.13 / 3.14:** Entorno principal para la codificación del script de ingesta de datos y el dashboard interactivo de VitalCore ([Descargar aquí](https://www.python.org/downloads/windows/)).

## 2. Comandos de Ejecución
Para iniciar el servicio de la BD NoSQL Apache Cassandra:
1. Abra la terminal de comandos (CMD o terminal de VSCode).
2. Navegue hasta la carpeta `bin` dentro del directorio de instalación de Cassandra.
3. Ejecute el comando:

   ```cmd
   cassandra.bat -f

## 3. Ejecución y Conexión en DBeaver

Para establecer la comunicación entre DBeaver y Cassandra 3.x, se debe instalar un wrapper JDBC específico:
1. Descargar el archivo cassandra-jdbc-wrapper-5.0.1-bundle.jar desde GitHub.
2. En DBeaver, ir a Database -> Driver Manager (Gestor de Drivers) -> New.
3. En la pestaña Settings, configurar:
* Driver Name: Cassandra ING Driver
* Class Name: com.ing.data.cassandra.jdbc.CassandraDriver
4. En la pestaña Libraries, hacer clic en Add File y seleccionar el archivo .jar descargado.
5. Para crear la conexión: Ir a Database -> New Database Connection -> Seleccionar Cassandra ING Driver -> Next.
6. En el campo JDBC URL introducir: jdbc:cassandra://127.0.0.1:9042/system?localdatacenter=datacenter1 (**Nota**: Se puede cambiar system por mi_primera_bd posteriormente para que DBeaver reconozca directamente nuestra base de datos).
7. Clic en Test Connection (Probar conexión) y luego en Finalizar.

* **Creación del Keyspace**:
El primer paso es crear la "base de datos" (KEYSPACE) abriendo un editor SQL y ejecutando:

**CREATE KEYSPACE mi_primera_bd WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};**

_Tip de DBeaver_: Para visualizar el nuevo Keyspace o las tablas recién creadas en el explorador, se recomienda desconectar la conexión "Cassandra ING Driver", refrescar y volver a conectar.

## 4. Creación de las tablas y llenado de Datos

Copie y ejecute el script CQL provisto en el repositorio para la creación de las tablas.
Antes de ejecutar la ingesta de datos y el dashboard, configure su entorno de Python:

### A. Configuración de variables de entorno (Opcional si hay errores SSL de certificados al usar pip):

        set CURL_CA_BUNDLE=

        set REQUEST_CA_BUNDLE=

### B. Instalación de dependencias del Driver de Cassandra: 
Para versiones recientes de Python (3.12+), es obligatorio instalar _pyasyncore_ para que el driver de Cassandra funcione correctamente: 

        python -m pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org pyasyncore faker cassandra-driver

### C. Ejecución de la Ingesta:
Ejecute el script generador. Este proceso simula el ecosistema médico y tomará entre 15 y 30 minutos: 

        python ingesta_vitalcore.py

### D. Ejecución del Dashboard (Interfaz Gráfica):
Instale las librerías necesarias para el panel interactivo: 

        python -m pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org streamlit pandas

Y finalmente, levante el servidor web del dashboard con el siguiente comando: 

        streamlit run dashboard_vitalcore.py
