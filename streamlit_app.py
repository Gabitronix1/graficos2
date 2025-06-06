import streamlit as st
import plotly.express as px
import pandas as pd
from supabase_client import get_client

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
serie = resp.data["serie"] # lista de dicts {label, value}
df = pd.DataFrame(serie)

# 3️⃣ Renderizar con Plotly mejorado deluxe
chart_type = meta.get("tipo", "bar")

if chart_type == "line":
    fig = px.line(df, x="label", y="value", markers=True, title=meta["titulo"], text="value", color="label")
elif chart_type == "scatter":
    fig = px.scatter(df, x="label", y="value", title=meta["titulo"], text="value", color="label")
else:
    fig = px.bar(df, x="label", y="value", title=meta["titulo"], text="value", color="label")

# Estilo visual pro
fig.update_traces(
    texttemplate='%{text} m³',
    textposition='outside',
    marker=dict(line=dict(width=0.5, color='black'))
)

# Paleta de colores personalizada
fig.update_layout(
    colorway=["#228B22", "#8B4513", "#1E90FF", "#800080"],  # verde, café, azul, púrpura
    yaxis_title="",
    xaxis_title="",
    title_font_size=24,
    uniformtext_minsize=8,
    uniformtext_mode='hide',
    plot_bgcolor='white',
    margin=dict(t=60, l=20, r=20, b=40),
    template="plotly_white"
)

# Mostrar total si aplica
total = df["value"].sum()
st.markdown(f"**🔢 Total producido:** {int(total)} m³")

# Mostrar descripción (puede venir de meta si quisieras)
st.markdown("Este gráfico muestra la producción total por zona agrupada por categoría.")

st.plotly_chart(fig, use_container_width=True)

