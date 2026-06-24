import streamlit as st
import pandas as pd
from cassandra.cluster import Cluster
import time

# 1. Configuración de la página web
st.set_page_config(page_title="VitalCore - Dashboard", layout="wide")
st.title("🩺 VitalCore: Centro de Monitoreo Médico")

# 2. Conexión a Cassandra (Cacheada para no reconectar cada vez que interactúas)
@st.cache_resource
def get_cassandra_session():
    cluster = Cluster(['127.0.0.1'])
    return cluster.connect('mi_primera_bd')

session = get_cassandra_session()

# 3. Función auxiliar para obtener un ID de médico al azar y no tener que tipear UUIDs
@st.cache_data
def obtener_lista_medicos():
    filas = session.execute("SELECT DISTINCT medico_id FROM ultimo_estado_paciente_por_medico")
    return [fila.medico_id for fila in filas]

lista_medicos = obtener_lista_medicos()

# --- INTERFAZ DE USUARIO ---
st.sidebar.header("Panel de Control")
medico_input = st.sidebar.selectbox("ID del Médico (UUID):", options=lista_medicos)

if medico_input:
    st.header("Pacientes Activos y Nivel de Riesgo")
    
    # --- KPI 1: Dashboard del Médico ---
    inicio_query_1 = time.time()
    
    # La consulta ultrarrápida gracias a la desnormalización
    query_pacientes = f"SELECT paciente_id, nombre_paciente, ultimo_tipo_sensor, ultimo_valor, nivel_riesgo FROM ultimo_estado_paciente_por_medico WHERE medico_id = {medico_input}"
    filas_pacientes = session.execute(query_pacientes)
    df_pacientes = pd.DataFrame(list(filas_pacientes))

    df_pacientes['paciente_id'] = df_pacientes['paciente_id'].astype(str) 
    df_pacientes['ultimo_valor'] = df_pacientes['ultimo_valor'].astype(float).round(2)

    fin_query_1 = time.time()
    latencia_ms = (fin_query_1 - inicio_query_1) * 1000
    
    # Mostramos el KPI de Latencia que exige la rúbrica
    st.metric(label="⏱️ Tiempo de Respuesta (Latencia de Cassandra)", value=f"{latencia_ms:.2f} ms")
    
    if not df_pacientes.empty:
        # Mostramos la tabla interactiva
        st.dataframe(df_pacientes, use_container_width=True)
        
        # --- KPI 2: Telemetría de un Paciente ---
        # --- KPI 2: Telemetría de un Paciente ---
        st.markdown("---")
        st.subheader("📈 Curva de Glucosa Histórica")
        
        # 1. Seleccionar el paciente
        paciente_seleccionado = st.selectbox("Seleccione un paciente para ver su telemetría:", df_pacientes['paciente_id'])
        
        # 2. NUEVO: Calcular dinámicamente los últimos 6 meses para el menú desplegable
        meses_disponibles = [(pd.Timestamp.now() - pd.DateOffset(months=i)).strftime('%Y-%m') for i in range(6)]
        mes_seleccionado = st.selectbox("Seleccione el mes a visualizar:", meses_disponibles)
        
        if paciente_seleccionado and mes_seleccionado:
            inicio_query_2 = time.time()
            
            # Consultamos usando la partición exacta: paciente_id + mes_seleccionado
            query_telemetria = f"SELECT fecha_hora, valor FROM telemetria_por_paciente_sensor WHERE paciente_id = {paciente_seleccionado} AND tipo_sensor = 'glucosa' AND mes_anio = '{mes_seleccionado}'"
            
            filas_telemetria = session.execute(query_telemetria)
            df_telemetria = pd.DataFrame(list(filas_telemetria))
            
            fin_query_2 = time.time()
            st.metric(label="⏱️ Tiempo de Respuesta (Serie de Tiempo)", value=f"{(fin_query_2 - inicio_query_2) * 1000:.2f} ms")
            
            if not df_telemetria.empty:
                # Limpiamos los decimales del punto flotante para la gráfica
                df_telemetria['valor'] = df_telemetria['valor'].astype(float).round(1)
                
                # Graficamos
                df_telemetria = df_telemetria.set_index('fecha_hora')
                st.line_chart(df_telemetria['valor'], color="#FF4B4B")
            else:
                st.info(f"El paciente no registra lecturas de glucosa en la partición temporal de {mes_seleccionado}.")
    else:
        st.warning("No se encontraron pacientes para este médico.")