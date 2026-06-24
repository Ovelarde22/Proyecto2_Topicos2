-- 1. CREACIÓN DEL KEYSPACE (Base de Datos)
CREATE KEYSPACE IF NOT EXISTS mi_primera_bd
WITH replication = {
    'class': 'SimpleStrategy',
    'replication_factor': 1
};

USE mi_primera_bd;

-- 2. CREACIÓN DE TABLAS (Diseñadas por Patrones de Acceso)

-- Patrón de acceso 1: Ingesta de Telemetría de pacientes
CREATE TABLE IF NOT EXISTS telemetria_por_paciente_sensor (
    paciente_id uuid,
    tipo_sensor text,
    mes_anio text,         -- Formato: 'YYYY-MM'
    fecha_hora timestamp,
    valor double,
    PRIMARY KEY ((paciente_id, tipo_sensor, mes_anio), fecha_hora)
) WITH CLUSTERING ORDER BY (fecha_hora DESC);

-- Patrón de acceso 2: Último estado del paciente por médico
CREATE TABLE IF NOT EXISTS ultimo_estado_paciente_por_medico (
    medico_id uuid,
    paciente_id uuid,
    nombre_medico text,
    nombre_paciente text,
    nivel_riesgo text,     -- Normal, Medio, Alto
    ultima_fecha_hora timestamp,
    ultimo_tipo_sensor text,
    ultimo_valor double,
    PRIMARY KEY (medico_id, paciente_id)
);

-- Patrón de acceso 3: Historial clínico del paciente
CREATE TABLE IF NOT EXISTS historial_clinico_por_paciente (
    paciente_id uuid,
    fecha_hora timestamp,
    medico_id uuid,
    tipo_evento text,      -- Consulta, Examen, Urgencias, etc.
    notas_medicas text,
    PRIMARY KEY (paciente_id, fecha_hora)
) WITH CLUSTERING ORDER BY (fecha_hora DESC);

-- Patrón de acceso 4: Alertas críticas por paciente
CREATE TABLE IF NOT EXISTS alertas_por_paciente (
    paciente_id uuid,
    resuelta boolean,      -- True = Resuelta, False = Activa
    fecha_hora timestamp,
    medico_id uuid,
    tipo_sensor text,
    valor_critico double,
    PRIMARY KEY (paciente_id, resuelta, fecha_hora)
) WITH CLUSTERING ORDER BY (resuelta ASC, fecha_hora DESC);

-- Patrón de acceso 5: Referidos a especialistas
CREATE TABLE IF NOT EXISTS referidos_por_paciente (
    paciente_id uuid,
    fecha_referencia timestamp,
    especialidad_destino text,
    medico_destino_id uuid,
    medico_origen_id uuid,
    motivo text,
    PRIMARY KEY (paciente_id, fecha_referencia)
) WITH CLUSTERING ORDER BY (fecha_referencia DESC);