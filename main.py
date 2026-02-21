import streamlit as st
import pandas as pd
import plotly.express as px
import mysql.connector

# 1. Función para conectar Python con tu base de datos
def conectar_base_datos(consulta_sql):
    conexion = mysql.connector.connect(
        host="localhost",
        user="root",        # Por defecto en XAMPP/Workbench es root
        password="",        # Pon tu contraseña aquí si tienes una
        database="EPM"
    )
    # Leemos la consulta y la guardamos en una tabla (DataFrame)
    resultado = pd.read_sql(consulta_sql, conexion)
    conexion.close()
    return resultado

# 2. Configuración visual de la página
st.set_page_config(page_title="Portal Energético EPM", layout="wide")
st.title("⚡ Panel de Control Energético EPM")
st.markdown("Bienvenido al sistema de visualización de proyectos.")

# 3. Creando los gráficos profesionales
st.header("Análisis de Inversiones")

# Consulta SQL: Sumamos el monto por tipo de energía
query_pie = """
SELECT t.tipo, SUM(i.monto) as total 
FROM inversiones i
JOIN proyectos p ON i.proyecto_id = p.id_proyecto
JOIN tipos_energia t ON p.tipo_energia = t.id_tipo
GROUP BY t.tipo
"""
df_inversion = conectar_base_datos(query_pie)

# Creamos un gráfico de torta con Plotly
fig = px.pie(df_inversion, values='total', names='tipo', title="Distribución de Inversión por Tecnología")
st.plotly_chart(fig)

# 4. Tabla de proyectos registrados
st.header("Listado de Proyectos Actuales")
df_proyectos = conectar_base_datos("SELECT nombre, ubicacion, fecha_inicio FROM proyectos")
st.table(df_proyectos)

# --- NUEVA FUNCIÓN: Filtro Interactivo ---
st.sidebar.header("Filtros")
opciones_proyectos = conectar_base_datos("SELECT nombre FROM proyectos")
proyecto_seleccionado = st.sidebar.selectbox("Selecciona un Proyecto", opciones_proyectos['nombre'])

st.subheader(f"Detalle de: {proyecto_seleccionado}")

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

col1, col2, col3 = st.columns(3)

# Calculamos algunos totales desde la base de datos
total_inv = df_inversion['total'].sum()
num_proyectos = len(df_proyectos)

with col1:
    st.metric(label="Inversión Total", value=f"${total_inv:,.0f}")
with col2:
    st.metric(label="Total de Proyectos", value=num_proyectos)
with col3:
    st.metric(label="Eficiencia Promedio", value="85%", delta="5%") # Ejemplo estático


st.subheader("⚡ Generación por Proyecto (kWh)")

query_eficiencia = """
SELECT p.nombre, e.kw_h_generado 
FROM eficiencia_energetica e
JOIN proyectos p ON e.proyecto_id = p.id_proyecto
"""
df_efi = conectar_base_datos(query_eficiencia)

if not df_efi.empty:
    fig_bar = px.bar(df_efi, x='nombre', y='kw_h_generado', 
                     color='nombre', text_auto='.2s',
                     title="Energía Generada por Planta")
    st.plotly_chart(fig_bar, use_container_width=True)

    