import streamlit as st
import plotly.express as px
import pandas as pd
from supabase_client import get_client
from streamlit.web.server.websocket_headers import _get_websocket_headers

def allow_iframe():
    headers = _get_websocket_headers()
    headers["X-Frame-Options"] = "ALLOWALL"
    headers["Content-Security-Policy"] = "frame-ancestors *"
allow_iframe()

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

# 3️⃣ Renderizar con Plotly
chart_type = meta.get("tipo", "bar")
if chart_type == "line":
    fig = px.line(df, x="label", y="value", markers=True, title=meta["titulo"])
elif chart_type == "scatter":
    fig = px.scatter(df, x="label", y="value", title=meta["titulo"])
else:
    fig = px.bar(df, x="label", y="value", title=meta["titulo"])

st.plotly_chart(fig, use_container_width=True)
