
import streamlit as st
import pandas as pd
import plotly.express as px
from supabase_client import get_client

st.set_page_config(layout="wide", page_title="Comparativa Producción vs Proyección")

supabase = get_client()

# ── Parámetro opcional ─────────────────────────────────────────────────────
grafico_id = st.query_params.get("grafico_id")

# Si viene un grafico_id ⇒ modo “iframe individual”
if grafico_id:
    st.markdown("### Gráfico individual")
    iframe_url = f"https://graficos2-production.up.railway.app/?grafico_id={grafico_id}"
    st.components.v1.iframe(src=iframe_url, height=760, width=1200)
    st.stop()           # ← no ejecutamos el resto del dashboard
# ───────────────────────────────────────────────────────────────────────────

# 🔍 Carga completa del dashboard (sin grafico_id)
data = supabase.table("comparativa_produccion_teams").select("*").execute().data
df = pd.DataFrame(data)

# Conversión de tipos y limpieza
df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
df[["produccion_total", "volumen_proyectado", "diferencia"]] = (
    df[["produccion_total", "volumen_proyectado", "diferencia"]].apply(pd.to_numeric, errors="coerce")
)

st.title("📊 Comparativa Producción vs Proyección por Team")

# Filtros interactivos
col1, col2, col3 = st.columns(3)
zonas     = sorted(df["zona"].dropna().unique())
calidades = sorted(df["calidad"].dropna().unique())
fechas    = sorted(df["fecha"].dt.date.unique(), reverse=True)

zona_sel    = col1.selectbox("Zona", zonas)
calidad_sel = col2.selectbox("Calidad", calidades)
fecha_sel   = col3.selectbox("Fecha", fechas)

df_f = df[(df["zona"] == zona_sel) &
          (df["calidad"] == calidad_sel) &
          (df["fecha"].dt.date == fecha_sel)]

# Gráfico barras Producción vs Proyección
fig_pp = px.bar(df_f, x="team",
                y=["produccion_total", "volumen_proyectado"],
                barmode="group",
                title=f"Producción vs Proyección • {zona_sel} • {calidad_sel} • {fecha_sel}",
                labels={"value": "Volumen (m³)", "variable": "Tipo"})

st.plotly_chart(fig_pp, use_container_width=True)

# Gráfico diferencia
fig_dif = px.bar(df_f, x="team", y="diferencia",
                 title="Diferencia Producción - Proyección",
                 labels={"diferencia": "Diferencia (m³)"},
                 color="diferencia", color_continuous_scale="RdYlGn")

st.plotly_chart(fig_dif, use_container_width=True)

# Tabla detalle
st.markdown("### Detalle")
st.dataframe(df_f)
