import uuid
import random
from datetime import datetime, timedelta
from faker import Faker
from cassandra.cluster import Cluster
from cassandra.concurrent import execute_concurrent_with_args

# 1. Inicializar Faker para generar nombres y textos realistas (en español)
fake = Faker('es_ES')

# 2. Conexión al clúster de Cassandra
print("Conectando al clúster de Cassandra...")
cluster = Cluster(['127.0.0.1'])
session = cluster.connect('mi_primera_bd') # Apuntamos a tu Keyspace

# 3. Preparación de Sentencias
print("Preparando sentencias CQL...")
insert_medico = session.prepare("""
    INSERT INTO ultimo_estado_paciente_por_medico 
    (medico_id, paciente_id, nombre_paciente, ultima_fecha_hora, ultimo_tipo_sensor, ultimo_valor, nivel_riesgo) 
    VALUES (?, ?, ?, ?, ?, ?, ?)
""")

insert_telemetria = session.prepare("""
    INSERT INTO telemetria_por_paciente_sensor 
    (paciente_id, tipo_sensor, mes_anio, fecha_hora, valor) 
    VALUES (?, ?, ?, ?, ?)
""")

insert_historial = session.prepare("""
    INSERT INTO historial_clinico_por_paciente 
    (paciente_id, fecha_hora, medico_id, tipo_evento, notas_medicas) 
    VALUES (?, ?, ?, ?, ?)
""")

# 4. Generación de Datos Sintéticos en Memoria
print("Generando datos sintéticos (Pacientes y Médicos)...")
SENSORES = ['glucosa', 'frecuencia_cardiaca', 'saturacion_oxigeno']

# Generar 50 IDs de Médicos
medicos_ids = [uuid.uuid4() for _ in range(50)]

# Generar 500 Pacientes asignados aleatoriamente a un médico
pacientes = [{'id': uuid.uuid4(), 'nombre': fake.name(), 'medico_id': random.choice(medicos_ids)} for _ in range(500)]

# Generar 200,000 lecturas de telemetría (aprox 400 por paciente en los últimos 6 meses)
print("Calculando 200,000 lecturas de telemetría...")
datos_telemetria = []
datos_estado_actual = [] 

fecha_inicio = datetime.now() - timedelta(days=180)

for paciente in pacientes:
    ultima_fecha = None
    ultimo_sensor = None
    ultimo_valor = None
    
    for _ in range(400):
        sensor = random.choice(SENSORES)
        fecha_lectura = fecha_inicio + timedelta(days=random.randint(0, 180), minutes=random.randint(0, 1440))
        mes_anio = fecha_lectura.strftime('%Y-%m')
        
        # Lógica para que los datos médicos tengan sentido (evaluado en la rúbrica)
        if sensor == 'glucosa':
            valor = round(random.uniform(70.0, 180.0), 1)
        elif sensor == 'frecuencia_cardiaca':
            valor = round(random.uniform(60.0, 120.0), 1)
        else: # saturacion_oxigeno
            valor = round(random.uniform(90.0, 100.0), 1)
            
        datos_telemetria.append((paciente['id'], sensor, mes_anio, fecha_lectura, valor))
        
        # Capturamos el dato más reciente para el dashboard del médico
        if not ultima_fecha or fecha_lectura > ultima_fecha:
            ultima_fecha = fecha_lectura
            ultimo_sensor = sensor
            ultimo_valor = valor

    # Determinar si el paciente está en riesgo (Ej: Glucosa alta)
    riesgo = 'ALTO' if ultimo_valor > 150 and ultimo_sensor == 'glucosa' else 'NORMAL'
    datos_estado_actual.append((paciente['medico_id'], paciente['id'], paciente['nombre'], ultima_fecha, ultimo_sensor, ultimo_valor, riesgo))

# Generar 1,000 notas de historial clínico
print("Redactando 1,000 notas de historial clínico...")
datos_historial = []
for _ in range(1000):
    pac = random.choice(pacientes)
    fecha = fecha_inicio + timedelta(days=random.randint(0, 180))
    nota = fake.text(max_nb_chars=200)
    datos_historial.append((pac['id'], fecha, pac['medico_id'], 'Consulta de Control', nota))

# 5. Ejecución Concurrente en Cassandra (La inyección real)
print("Iniciando inyección masiva en Cassandra (Esto tomará unos segundos/minutos)...")

# Insertar el estado actual de los pacientes
execute_concurrent_with_args(session, insert_medico, datos_estado_actual, concurrency=100)

# Insertar los historiales clínicos
execute_concurrent_with_args(session, insert_historial, datos_historial, concurrency=100)

# Insertar las 200,000 lecturas (Usamos alta concurrencia para no hacer cuello de botella)
execute_concurrent_with_args(session, insert_telemetria, datos_telemetria, concurrency=200)

print("¡Ingesta finalizada con éxito! Los datos ya están en tu base de datos.")
cluster.shutdown()