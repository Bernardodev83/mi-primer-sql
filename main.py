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



# --- SECCIÓN: EXPLORADOR DETALLADO DE EQUIPO ---
st.markdown("---")
st.header("👥 Equipo y Aliados por Proyecto")

# 1. Obtenemos la lista de proyectos para el buscador
proyectos_lista = conectar_base_datos("SELECT nombre FROM proyectos")
seleccion = st.selectbox("Busca un proyecto para ver el equipo técnico:", proyectos_lista['nombre'])

# 2. Consulta Relacional: Investigadores + Empresas + Proyecto
query_equipo = f"""
    SELECT 
        i.nombre AS Investigador, 
        i.apellido, 
        i.especialidad,
        e.nombre AS Empresa,
        e.industria
    FROM proyectos p
    LEFT JOIN investigadores i ON p.id_proyecto = i.proyecto_id
    LEFT JOIN empresas e ON p.id_proyecto = e.proyecto_id
    WHERE p.nombre = '{seleccion}'
"""

df_equipo = conectar_base_datos(query_equipo)

# 3. Mostrar la información de forma elegante
if not df_equipo.empty:
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


st.markdown("---")
st.header("🚀 Simulador de Inversión Estratégica")
st.write("Mueve el deslizador para ver cómo impactaría un aumento de capital en el presupuesto total de EPM.")

# 1. Creamos el Slider en la barra lateral o en el centro
porcentaje = st.slider("Selecciona el porcentaje de aumento (%)", 0, 100, 10)

# 2. Obtenemos el total actual (usando la tabla que ya teníamos)
inversion_actual = df_inversion['total'].sum()

# 3. Calculamos los nuevos valores
aumento_dinero = inversion_actual * (porcentaje / 100)
nueva_inversion_total = inversion_actual + aumento_dinero

# 4. Mostramos el resultado con un diseño llamativo
c1, c2 = st.columns(2)
with c1:
    st.metric("Inversión Proyectada", f"${nueva_inversion_total:,.2f}", f"+{porcentaje}%")
with c2:
    st.metric("Capital Adicional Necesario", f"${aumento_dinero:,.2f}")

# 5. Gráfico comparativo
df_simulacion = pd.DataFrame({
    'Escenario': ['Actual', 'Con Aumento'],
    'Monto': [inversion_actual, nueva_inversion_total]
})

fig_sim = px.bar(df_simulacion, x='Escenario', y='Monto', 
                 color='Escenario', text_auto='.2s',
                 title="Comparativa: Presupuesto Actual vs Proyectado")
st.plotly_chart(fig_sim)    


# Crea tres pestañas en la parte superior
tab1, tab2, tab3 = st.tabs(["📈 Dashboard Principal", "⚡ Eficiencia", "💰 Simulador"])

with tab1:
    # Aquí mueves el código del gráfico de torta y la tabla de proyectos
    st.write("Visualización general de la base de datos.")

with tab2:
    # Aquí mueves el código de eficiencia (kWh)
    st.write("Análisis detallado de producción.")

with tab3:
    # Aquí pones el código del simulador que acabamos de escribir
    st.write("Herramienta de proyección financiera.")



# Mover el simulador a la izquierda (Sidebar)
with st.sidebar:
    st.title("⚙️ Configuración")
    porcentaje = st.slider("Aumento de Presupuesto (%)", 0, 100, 10)
    
    # Cálculos rápidos
    total_actual = df_inversion['total'].sum()
    nuevo_total = total_actual * (1 + porcentaje/100)
    
    st.metric("Nuevo Presupuesto", f"${nuevo_total:,.0f}")
    st.write("Esta proyección afecta a todos los cálculos del dashboard.")