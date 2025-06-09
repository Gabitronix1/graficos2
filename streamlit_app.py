import streamlit as st
import plotly.express as px
import pandas as pd
from supabase_client import get_client
import uuid

st.set_page_config(layout="wide", page_title="Gráficos Tronix")
# 🔥 DASHBOARD PREDICTIVO
st.title("📊 Panel de Control - Agente Tronix")

supabase = get_client()
data = supabase.table("vista_comparativa_despachos").select("*").execute().data
df_dashboard = pd.DataFrame(data)

if not df_dashboard.empty:
    volumen_planificado = df_dashboard["volumen_planificado"].sum()
    volumen_despachado = df_dashboard["volumen_despachado"].sum()
    diferencia = volumen_despachado - volumen_planificado

    col1, col2, col3 = st.columns(3)
    col1.metric("✅ Planificado (m³)", f"{volumen_planificado:,.0f}")
    col2.metric("🚛 Despachado (m³)", f"{volumen_despachado:,.0f}")
    col3.metric("📉 Diferencia", f"{diferencia:,.0f}")

    df_zona = df_dashboard.groupby("codigo_destino")[["volumen_planificado", "volumen_despachado"]].sum().reset_index()
    fig = px.bar(df_zona, x="codigo_destino", y=["volumen_planificado", "volumen_despachado"],
                 barmode="group", title="Volumen por Zona")
    st.plotly_chart(fig, use_container_width=True)

    st.divider()
else:
    st.info("No hay datos para mostrar el panel predictivo.")

# ⬇️ Lo que ya tenías antes (gráfico por grafico_id)

# 1️⃣ Leer query param
grafico_id = st.query_params.get("grafico_id")
if not grafico_id:
    st.error("Falta el parámetro grafico_id")
    st.stop()

# 2️⃣ Consultar Supabase
supabase = get_client()
resp = (
    supabase.table("graficos")
    .select("*")
    .eq("id", grafico_id)
    .single()
    .execute()
)

if not resp.data:
    st.error("No se encontró el gráfico solicitado")
    st.stop()

meta = resp.data           # título, tipo, etc.
serie = resp.data["serie"] # lista de dicts {label, value}
df = pd.DataFrame(serie)

# 3️⃣ Renderizar con Plotly mejorado deluxe
# Función nueva con mejoras y soporte para múltiples tipos de gráfico
def render_dynamic_chart(df, meta):
    chart_type = meta.get("tipo", "bar")

    if chart_type == "pie":
        fig = px.pie(df, names="label", values="value", title=meta["titulo"])
    elif chart_type == "line" and "label" in df.columns and df.shape[1] > 2:
        df_melted = df.melt(id_vars=["label"], var_name="serie", value_name="value")
        fig = px.line(df_melted, x="label", y="value", color="serie", markers=True, text="value", title=meta["titulo"])
    elif chart_type == "line":
        fig = px.line(df, x="label", y="value", markers=True, text="value", title=meta["titulo"], color="label")
    elif chart_type == "scatter":
        fig = px.scatter(df, x="label", y="value", title=meta["titulo"], text="value", color="label")
    else:
        fig = px.bar(df, x="label", y="value", title=meta["titulo"], text="value", color="label")

    fig.update_traces(
        texttemplate='%{text} m³',
        textposition='outside',
        marker=dict(line=dict(width=0.5, color='black'))
    )

    fig.update_layout(
        colorway=["#228B22", "#8B4513", "#1E90FF", "#800080"],
        yaxis_title="",
        xaxis_title="",
        title_font_size=24,
        uniformtext_minsize=8,
        uniformtext_mode='hide',
        plot_bgcolor='white',
        margin=dict(t=60, l=20, r=20, b=40),
        template="plotly_white"
    )

    return fig

# Mostrar total
total = df["value"].sum()
st.markdown(f"**🔢 Total producido:** {int(total)} m³")

# Mostrar descripción
st.markdown("Este gráfico muestra la producción total por zona agrupada por categoría.")

# Mostrar el gráfico usando la función mejorada
st.plotly_chart(render_dynamic_chart(df, meta), use_container_width=True)



