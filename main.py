

import streamlit as st
import pandas as pd
import plotly.express as px
import mysql.connector

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Portal Energético EPM", layout="wide")

# --- 2. FUNCIONES DE CONEXIÓN Y DISEÑO ---
def conectar_base_datos(consulta_sql):
    try:
        conexion = mysql.connector.connect(
            host=st.secrets["DB_HOST"],
            port=int(st.secrets["DB_PORT"]),
            user=st.secrets["DB_USER"],
            password=st.secrets["DB_PASSWORD"],
            database=st.secrets["DB_NAME"]
        )
        resultado = pd.read_sql(consulta_sql, conexion)
        conexion.close()
        return resultado
    except Exception as e:
        st.error(f"Error al conectar con la base de datos: {e}")
        return pd.DataFrame()

def validar_usuario(user, password):
    try:
        conexion = mysql.connector.connect(
            host=st.secrets["DB_HOST"],
            port=int(st.secrets["DB_PORT"]),
            user=st.secrets["DB_USER"],
            password=st.secrets["DB_PASSWORD"],
            database=st.secrets["DB_NAME"]
        )
        cursor = conexion.cursor()
        query = "SELECT * FROM usuarios WHERE nombre_usuario = %s AND clave = %s"
        cursor.execute(query, (user, password))
        resultado = cursor.fetchone()
        conexion.close()
        return resultado
    except:
        return None

def aplicar_diseno_login():
    # Imagen de fondo relacionada con energía/ingeniería
    img_url = "https://images.unsplash.com/photo-1473341304170-971dccb5ac1e?auto=format&fit=crop&w=1350&q=80"
    st.markdown(f"""
        <style>
        .stApp {{
            background-image: url("{img_url}");
            background-size: cover;
            background-position: center;
        }}
        .login-box {{
            background-color: rgba(255, 255, 255, 0.9);
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0px 10px 25px rgba(0,0,0,0.5);
        }}
        </style>
    """, unsafe_allow_html=True)

# --- 3. LÓGICA DE CONTROL DE SESIÓN ---
if 'logeado' not in st.session_state:
    st.session_state.logeado = False

# --- 4. INTERFAZ DE LOGIN ---
if not st.session_state.logeado:
    aplicar_diseno_login()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        st.title("⚡ Sistema EPM")
        st.subheader("Acceso Restringido")
        
        tab_login, tab_reg = st.tabs(["🔐 Entrar", "📝 Registro"])
        
        with tab_login:
            user = st.text_input("Usuario", key="user")
            pw = st.text_input("Contraseña", type="password", key="pw")
            if st.button("Ingresar al Portal"):
                if validar_usuario(user, pw):
                    st.session_state.logeado = True
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas")
        
        with tab_reg:
            st.info("Contacte al administrador para crear una nueva cuenta.")
        
        st.markdown('</div>', unsafe_allow_html=True)

# --- 5. DASHBOARD PRINCIPAL (SOLO SI ESTÁ LOGEADO) ---
else:
    # Botón de cerrar sesión en el sidebar
    if st.sidebar.button("Log Out / Salir"):
        st.session_state.logeado = False
        st.rerun()

    st.title("⚡ Panel Energético EPM")
    st.markdown("Bienvenido al sistema de visualización de proyectos.")

    # --- TODO TU CÓDIGO ORIGINAL DESDE AQUÍ ---
    st.header("Análisis de Inversiones")

    query_pie = """
    SELECT t.tipo, SUM(i.monto) as total 
    FROM inversiones i
    JOIN proyectos p ON i.proyecto_id = p.id_proyecto
    JOIN tipos_energia t ON p.tipo_energia = t.id_tipo
    GROUP BY t.tipo
    """
    df_inversion = conectar_base_datos(query_pie)

    if not df_inversion.empty:
        fig = px.pie(df_inversion, values='total', names='tipo', title="Distribución de Inversión por Tecnología")
        st.plotly_chart(fig)

    st.header("Listado de Proyectos Actuales")
    df_proyectos = conectar_base_datos("SELECT nombre, ubicacion, fecha_inicio FROM proyectos")
    st.table(df_proyectos)

    st.sidebar.header("Filtros")
    opciones_proyectos = conectar_base_datos("SELECT nombre FROM proyectos")
    if not opciones_proyectos.empty:
        proyecto_seleccionado = st.sidebar.selectbox("Selecciona un Proyecto", opciones_proyectos['nombre'])
        st.subheader(f"Detalle de: {proyecto_seleccionado}")

        # Explorador detallado de equipo
        st.markdown("---")
        st.header("👥 Equipo y Aliados por Proyecto")
        query_equipo = f"""
            SELECT i.nombre AS Investigador, i.apellido, i.especialidad, e.nombre AS Empresa, e.industria
            FROM proyectos p
            LEFT JOIN investigadores i ON p.id_proyecto = i.proyecto_id
            LEFT JOIN empresas e ON p.id_proyecto = e.proyecto_id
            WHERE p.nombre = '{proyecto_seleccionado}'
        """
        df_equipo = conectar_base_datos(query_equipo)

        if not df_equipo.empty and pd.notnull(df_equipo['Investigador'][0]):
            col_inv, col_emp = st.columns(2)
            with col_inv:
                st.subheader("👨‍🔬 Investigador a cargo")
                nombre_completo = f"{df_equipo['Investigador'][0]} {df_equipo['apellido'][0]}"
                st.info(f"**Nombre:** {nombre_completo}\n\n**Especialidad:** {df_equipo['especialidad'][0]}")
            with col_emp:
                st.subheader("🏢 Empresa Aliada")
                st.success(f"**Nombre:** {df_equipo['Empresa'][0]}\n\n**Sector:** {df_equipo['industria'][0]}")
        else:
            st.warning("No se encontró personal asignado a este proyecto.")

        # Consulta dinámica filtrada
        query_detalle = f"""
            SELECT p.nombre, p.ubicacion, t.tipo as energia, i.monto as inversion
            FROM proyectos p
            JOIN tipos_energia t ON p.tipo_energia = t.id_tipo
            JOIN inversiones i ON p.id_proyecto = i.proyecto_id
            WHERE p.nombre = '{proyecto_seleccionado}'
        """
        df_detalle = conectar_base_datos(query_detalle)
        st.write(df_detalle)

    # Métricas
    col1, col2, col3 = st.columns(3)
    total_inv = df_inversion['total'].sum() if not df_inversion.empty else 0
    num_proyectos = len(df_proyectos) if not df_proyectos.empty else 0

    with col1:
        st.metric(label="Inversión Total", value=f"${total_inv:,.0f}")
    with col2:
        st.metric(label="Total de Proyectos", value=num_proyectos)
    with col3:
        st.metric(label="Eficiencia Promedio", value="85%", delta="5%")

    # Gráfico de Barras
    st.subheader("⚡ Generación por Proyecto (kWh)")
    query_eficiencia = """
    SELECT p.nombre, e.kw_h_generado 
    FROM eficiencia_energetica e
    JOIN proyectos p ON e.proyecto_id = p.id_proyecto
    """
    df_efi = conectar_base_datos(query_eficiencia)
    if not df_efi.empty:
        fig_bar = px.bar(df_efi, x='nombre', y='kw_h_generado', color='nombre', title="Energía Generada por Planta")
        st.plotly_chart(fig_bar, use_container_width=True)

    # Mapa/Barra de regiones
    st.markdown("---")
    st.subheader("📍 Concentración de Inversión por Ubicación")
    query_mapa = """
    SELECT p.ubicacion, SUM(i.monto) as total_monto
    FROM proyectos p
    JOIN inversiones i ON p.id_proyecto = i.proyecto_id
    GROUP BY p.ubicacion
    ORDER BY total_monto DESC
    """
    df_mapa = conectar_base_datos(query_mapa)
    if not df_mapa.empty:
        fig_mapa = px.bar(df_mapa, x='total_monto', y='ubicacion', orientation='h', color='total_monto', color_continuous_scale='Viridis')
        st.plotly_chart(fig_mapa, use_container_width=True)