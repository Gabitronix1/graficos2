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

# 3️⃣ Renderizar con Plotly mejorado deluxe y múltiple series
chart_type = meta.get("tipo", "bar")
title = meta.get("titulo", "")

# 🎨 Colores personalizados
custom_colors = ["#EBB34F", "#696158", "#BFB800", "#DFD1A7", "#A67B5B", "#F2C57C", "#D4A373"]

# Convertir valores a enteros
value_cols = [col for col in df.columns if col != "label"]
df[value_cols] = df[value_cols].astype(int)

# Para gráficos múltiples → derretimos la tabla
df_melted = df.melt(id_vars="label", var_name="serie", value_name="value")

if chart_type == "pie":
    fig = px.pie(df, names="label", values=value_cols[0], title=title, hole=0.4)
elif chart_type == "line":
    fig = px.line(df_melted, x="label", y="value", color="serie", markers=True, text="value", title=title)
elif chart_type == "scatter":
    fig = px.scatter(df_melted, x="label", y="value", color="serie", text="value", title=title)
else:
    fig = px.bar(df_melted, x="label", y="value", color="serie", text="value", title=title)

fig.update_traces(
    texttemplate='%{text} m³',
    textposition='outside',
    marker=dict(line=dict(width=0.5, color='black'))
)
fig.update_layout(
    colorway=custom_colors,
    yaxis_title="",
    xaxis_title="",
    title_font_size=24,
    uniformtext_minsize=8,
    uniformtext_mode='hide',
    plot_bgcolor='white',
    margin=dict(t=60, l=20, r=20, b=40),
    template="plotly_white"
)

total = df_melted["value"].sum()
st.markdown(f"**🔢 Total producido:** {int(total)} m³")
st.markdown("Este gráfico muestra la producción total por zona agrupada por categoría.")
st.plotly_chart(fig, use_container_width=True)


