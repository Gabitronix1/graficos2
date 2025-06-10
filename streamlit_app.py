import streamlit as st
import plotly.express as px
import pandas as pd
from supabase_client import get_client
import uuid

st.set_page_config(layout="wide", page_title="Gráficos Tronix")

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
serie_original = resp.data["serie"]

# 🔐 Blindaje: limpiar la serie para que value sea siempre numérico
def sanitizar_serie(serie):
    def limpiar_valor(v):
        if isinstance(v, dict):
            return list(v.values())[0] if len(v) == 1 else 0
        elif isinstance(v, (int, float)):
            return v
        elif isinstance(v, str):
            try:
                return float(v)
            except:
                return 0
        else:
            return 0

    for item in serie:
        item["value"] = limpiar_valor(item.get("value"))

    return serie

serie = sanitizar_serie(serie_original)
df = pd.DataFrame(serie)

# ✅ Función para renderizar múltiples tipos de gráfico
def render_dynamic_chart(df, meta):
    chart_type = meta.get("tipo", "bar")

    if "label" not in df.columns or "value" not in df.columns:
        st.error("Los datos no tienen las columnas requeridas: 'label' y 'value'")
        st.stop()

    if chart_type == "pie":
        fig = px.pie(df, names="label", values="value", title=meta["titulo"])
    elif chart_type == "line" and df.shape[1] > 2:
        df_melted = df.melt(id_vars=["label"], var_name="serie", value_name="value")
        fig = px.line(df_melted, x="label", y="value", color="serie", markers=True, text="value", title=meta["titulo"])
    elif chart_type == "line":
        fig = px.line(df, x="label", y="value", markers=True, text="value", title=meta["titulo"], color="label")
    elif chart_type == "area":
        fig = px.area(df, x="label", y="value", title=meta["titulo"], markers=True, color="label", text="value")
    elif chart_type == "scatter":
        fig = px.scatter(df, x="label", y="value", title=meta["titulo"], text="value", color="label")
    elif chart_type == "horizontal_bar":
        fig = px.bar(df, y="label", x="value", title=meta["titulo"], text="value", orientation='h', color="label")
    else:  # default bar
        fig = px.bar(df, x="label", y="value", title=meta["titulo"], text="value", color="label")

    fig.update_traces(
        texttemplate='%{text} m³',
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

# Mostrar gráfico
st.plotly_chart(render_dynamic_chart(df, meta), use_container_width=True)








