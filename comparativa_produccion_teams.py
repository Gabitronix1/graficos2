
import streamlit as st
import pandas as pd
import plotly.express as px
from supabase_client import get_client

st.set_page_config(layout="wide", page_title="Comparativa Producción vs Proyección")

# 🎯 Conexión a Supabase
supabase = get_client()

# 🧠 Consulta a la vista actualizada
@st.cache_data(ttl=600)
def cargar_datos():
    data = supabase.table("comparativa_produccion_teams").select("*").execute().data
    return pd.DataFrame(data)

df = cargar_datos()

if df.empty:
    st.warning("No hay datos disponibles en la vista comparativa.")
    st.stop()

# 🎛️ Filtros
col1, col2, col3 = st.columns(3)
zonas = df["zona"].dropna().unique()
fechas = df["fecha"].dropna().unique()
calidades = df["calidad"].dropna().unique()

zona_sel = col1.selectbox("Selecciona la zona", sorted(zonas), index=0)
fecha_sel = col2.selectbox("Selecciona la fecha", sorted(fechas, reverse=True), index=0)
calidad_sel = col3.selectbox("Selecciona la calidad", sorted(calidades), index=0)

df_filtrado = df[
    (df["zona"] == zona_sel) &
    (df["fecha"] == fecha_sel) &
    (df["calidad"] == calidad_sel)
]

# 📊 Gráfico de comparación de volumen
fig = px.bar(
    df_filtrado,
    x="team",
    y=["produccion_total", "volumen_proyectado"],
    barmode="group",
    title=f"Comparativa de Producción vs Proyección ({zona_sel} - {calidad_sel} - {fecha_sel})",
    labels={"value": "Volumen (m³)", "team": "Equipo", "variable": "Tipo"},
    text_auto=True
)
st.plotly_chart(fig, use_container_width=True)

# 📉 Diferencia
fig_dif = px.bar(
    df_filtrado,
    x="team",
    y="diferencia",
    title="Diferencia de volumen producido vs proyectado",
    labels={"diferencia": "Diferencia (m³)", "team": "Equipo"},
    text_auto=True,
    color="diferencia",
    color_continuous_scale="RdYlGn"
)
st.plotly_chart(fig_dif, use_container_width=True)

# 🧾 Tabla detallada
st.markdown("### Detalle de datos")
st.dataframe(df_filtrado)
