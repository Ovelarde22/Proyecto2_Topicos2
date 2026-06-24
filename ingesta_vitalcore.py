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
session = cluster.connect('mi_primera_bd')
session.default_timeout = 60 # Aumentar el tiempo de espera para operaciones masivas

# 3. Configuración del volumen de datos del demo
num_medicos = 50
num_pacientes = 500
lecturas_por_paciente = 400
print("Inciando la generación de entidades base....")

# 3.1 Generación del pool de Médicos (Diccionario ID -> Nombre del Doctor)
medicos_dict = {uuid.uuid4(): f"Dr. {fake.last_name()} {fake.first_name()}" for _ in range(num_medicos)}
medicos_ids = list(medicos_dict.keys())

# 3.2 Generación del pool de Pacientes adignadoos a un médico
pacientes_dict = {}
for _ in range(num_pacientes):
    paciente_id = uuid.uuid4()
    pacientes_dict[paciente_id] = {
        'nombre': fake.name(),
        'medico_id': random.choice(medicos_ids)
    }

# 4. Preparación de Sentencias
print("Preparando sentencias CQL...")
insert_telemetria = session.prepare("""
    INSERT INTO telemetria_por_paciente_sensor (paciente_id, tipo_sensor, mes_anio, fecha_hora, valor)
    VALUES (?, ?, ?, ?, ?)
""")

insert_historial = session.prepare("""
    INSERT INTO historial_clinico_por_paciente (paciente_id, fecha_hora, medico_id, notas_medicas, tipo_evento)
    VALUES (?, ?, ?, ?, ?)
""")

insert_alertas = session.prepare("""
    INSERT INTO alertas_por_paciente (paciente_id, resuelta, fecha_hora, medico_id, tipo_sensor, valor_critico)
    VALUES (?, ?, ?, ?, ?, ?)
""")

insert_referidos = session.prepare("""
    INSERT INTO referidos_por_paciente (paciente_id, fecha_referencia, especialidad_destino, medico_destino_id, medico_origen_id, motivo)
    VALUES (?, ?, ?, ?, ?, ?)
""")

insert_estado = session.prepare("""
    INSERT INTO ultimo_estado_paciente_por_medico 
    (medico_id, paciente_id, nombre_medico, nivel_riesgo, nombre_paciente, ultima_fecha_hora, ultimo_tipo_sensor, ultimo_valor)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
""")

# 5. Generación de Datos Sintéticos en Memoria
print("Generando datos sintéticos (Pacientes y Médicos)...")
sensores = {
    'glucosa': (70.0, 140.0), 
    'frecuencia_cardiaca': (60.0, 100.0), 
    'saturacion_oxigeno': (96.0, 100.0)
}
cont_pacientes = 0
now = datetime.now()

for paciente_id, paciente_info in pacientes_dict.items():
    cont_pacientes += 1
    print(f" [%] Procesando paciente {cont_pacientes}/{len(pacientes_dict)}: {paciente_info['nombre']}")

    medico_id = paciente_info['medico_id']
    nombre_medico = medicos_dict[medico_id]
    nombre_paciente = paciente_info['nombre']

    #Variables de control para identificar cronológicamente la lectura más reciente
    ultima_lectura_fecha = now - timedelta(days=185)
    ultimo_tipo_sensor = 'glucosa'
    ultimo_valor = 85.0

    # Patrón de acceso 1: Ingesta de Telemetría de pacientes
    for _ in range(lecturas_por_paciente):
        tipo_sensor = random.choice(list(sensores.keys()))
        min_val, max_val = sensores[tipo_sensor]

        # Generación de lecturas anormales para la activación del sistema de alertas (Equivale al 10% de las lecturas)
        if random.random() < 0.10:
            valor = random.choice([min_val - random.uniform(5,15), max_val + random.uniform(10,40)])
        else:
            valor = random.uniform(min_val, max_val)

        #Distribución aleatoria de la fecha en la ventana histórica de 6 meses
        dias_atras = random.uniform(0,180)
        fecha_hora = now - timedelta(days=dias_atras)
        mes_anio = fecha_hora.strftime('%Y-%m')

        # Inserción de la Telemetría
        session.execute(insert_telemetria, (paciente_id, tipo_sensor, mes_anio, fecha_hora, float(valor)))

        # Guardar sí el registro más reciente en la línea de tiempo del paciente
        if fecha_hora > ultima_lectura_fecha:
            ultima_lectura_fecha = fecha_hora
            ultimo_tipo_sensor = tipo_sensor
            ultimo_valor = valor

    # Evaluación del nivel de riesgo inteligente según el último valor de telemetría registrado
    nivel_riesgo = "Normal"
    if ultimo_tipo_sensor == 'glucosa' and ultimo_valor > 150:
        nivel_riesgo = "Alto"
    elif ultimo_tipo_sensor == 'frecuencia_cardiaca' and ultimo_valor > 110:
        nivel_riesgo = "Alto"
    elif ultimo_tipo_sensor == 'saturacion_oxigeno' and ultimo_valor < 92:
        nivel_riesgo = "Alto"
    elif random.random() < 0.15:
        nivel_riesgo = "Medio"

    # Patrón de acceso 2 Consolidación del último estado por el médico
    session.execute(insert_estado, (
        medico_id,
        paciente_id,
        nombre_medico,
        nivel_riesgo,
        nombre_paciente,
        ultima_lectura_fecha,
        ultimo_tipo_sensor,
        float(ultimo_valor)
    ))

    # Patrón de acceso 3: Historial clínico del paciente
    for _ in range(random.randint(2,4)):
        fecha_historial = now - timedelta(days=random.uniform(5,170))
        tipo_evento = random.choice(['Consulta presencial', 'Examen de laboratorio', 'Control mensual', 'Telemedicina', 'Urgencias'])
        notas = fake.sentence(nb_words=12)
        session.execute(insert_historial, (
            paciente_id,
            fecha_historial,
            medico_id,
            notas,
            tipo_evento
        ))

    # Patrón de acceso 4: Alertas criticas activas / resueltas
    if nivel_riesgo in ["Medio", "Alto"] or random.random() < 0.2:
        for _ in range(random.randint(1,2)):
            fehca_alerta = now - timedelta(days=random.uniform(0,45))
            resueltas = random.choice([True, False])
            sensor_alerta = random.choice(list(sensores.keys()))
            valor_critico = sensores[sensor_alerta][1] + random.uniform(5,25) if random.random() > 0.5 else sensores[sensor_alerta][0] - random.uniform(4,12)
            session.execute(insert_alertas, (
                paciente_id,
                resueltas,
                fehca_alerta,
                medico_id,
                sensor_alerta,
                float(valor_critico)
            ))

    # Patrón de acceso 5: Referidos a especialistas
    if random.random () < 0.35:
        fecha_referencia = now - timedelta(days=random.uniform(10,90))
        especialista = random.choice(['Cardiología', 'Endocrinología', 'Geriatría', 'Medicina Interna'])
        medico_destino = random.choice([m for m in medicos_ids if m != medico_id])
        motivo = f"Paciente derivado a {especialista} para seguimiento continuo por variaciones de {ultimo_tipo_sensor}."
        session.execute(insert_referidos, (
            paciente_id,
            fecha_referencia,
            especialista,
            medico_destino,
            medico_id,
            motivo
        ))

print("\n¡Proceso de inserción de datos fue completado con exito!")
print(f"-> Se crearon y guardaron {num_medicos} médicos con sus nombres reales.")
print(f"-> Se asignaron y simularon {num_pacientes} pacientes con sus respectivas historias clínicas, alertas y derivaciones.")

"""
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
cluster.shutdown()"""