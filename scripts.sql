-- 1. CREACIÓN DEL KEYSPACE (BASE DE DATOS)
-- Usamos SimpleStrategy con factor de replicación 1 para un entorno de desarrollo local.
CREATE KEYSPACE IF NOT EXISTS mi_primera_bd 
WITH replication = {
    'class': 'SimpleStrategy', 
    'replication_factor': 1
};

USE mi_primera_bd;

-- ==============================================================================
-- PATRÓN DE ACCESO 1: Historial clínico completo ordenado cronológicamente
-- ==============================================================================
CREATE TABLE IF NOT EXISTS mi_primera_bd.historial_clinico_por_paciente (
    paciente_id uuid,
    fecha_hora timestamp,
    medico_id uuid,
    notas_medicas text,
    tipo_evento text,
    PRIMARY KEY (paciente_id, fecha_hora)
) WITH CLUSTERING ORDER BY (fecha_hora DESC);


-- ==============================================================================
-- PATRÓN DE ACCESO 2: Búsqueda de lecturas de sensores por rango de fechas
-- Aplicamos la técnica de "Bucketing Temporal" usando 'mes_anio' para evitar Wide Rows.
-- ==============================================================================
CREATE TABLE IF NOT EXISTS mi_primera_bd.telemetria_por_paciente_sensor (
    paciente_id uuid,
    tipo_sensor text,
    mes_anio text,
    fecha_hora timestamp,
    valor double,
    PRIMARY KEY (paciente_id, tipo_sensor, mes_anio, fecha_hora)
) WITH CLUSTERING ORDER BY (tipo_sensor ASC, mes_anio ASC, fecha_hora DESC);


-- ==============================================================================
-- PATRÓN DE ACCESO 3: Mapa de alertas activas (eventos críticos sin resolver)
-- Incluimos 'resuelta' en la clave de agregación para poder filtrar alertas activas velozmente.
-- ==============================================================================
CREATE TABLE IF NOT EXISTS mi_primera_bd.alertas_por_paciente (
    paciente_id uuid,
    resuelta boolean,
    fecha_hora timestamp,
    medico_id uuid,
    tipo_sensor text,
    valor_critico double,
    PRIMARY KEY (paciente_id, resuelta, fecha_hora)
) WITH CLUSTERING ORDER BY (resuelta ASC, fecha_hora DESC);


-- ==============================================================================
-- PATRÓN DE ACCESO 4: Red de referidos de un paciente desde médico general a especialistas
-- ==============================================================================
CREATE TABLE IF NOT EXISTS mi_primera_bd.referidos_por_paciente (
    paciente_id uuid,
    fecha_referencia timestamp,
    especialidad_destino text,
    medico_destino_id uuid,
    medico_origen_id uuid,
    motivo text,
    PRIMARY KEY (paciente_id, fecha_referencia)
) WITH CLUSTERING ORDER BY (fecha_referencia DESC);


-- ==============================================================================
-- PATRÓN DE ACCESO 5: Dashboard operativo del médico (Pacientes ordenados por riesgo)
-- Tabla altamente DESNORMALIZADA para evitar JOINs y servir la información en tiempo real.
-- ==============================================================================
CREATE TABLE IF NOT EXISTS mi_primera_bd.ultimo_estado_paciente_por_medico (
    medico_id uuid,
    paciente_id uuid,
    nivel_riesgo text,
    nombre_paciente text,
    ultima_fecha_hora timestamp,
    ultimo_tipo_sensor text,
    ultimo_valor double,
    PRIMARY KEY (medico_id, paciente_id)
);