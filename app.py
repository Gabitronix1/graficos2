import streamlit as st
import plotly.graph_objects as go
import json
import os

DATA_PATH = "graficos_guardados"

# Crea la carpeta si no existe
os.makedirs(DATA_PATH, exist_ok=True)

st.set_page_config(page_title="Gráfico", layout="centered")
st.title("Gráfico")

# Si viene un gráfico nuevo por POST
if st.query_params.get("grafico_id"):
    grafico_id = st.query_params["grafico_id"]
    try:
        with open(f"{DATA_PATH}/{grafico_id}.json", "r") as f:
            data = json.load(f)
        fig = go.Figure(data=[go.Bar(x=data["labels"], y=data["data"])])
        fig.update_layout(title=data.get("title", "Gráfico"), yaxis_title=data.get("ylabel", ""))
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error("Error al cargar el gráfico: " + str(e))
else:
    st.info("No se ha especificado ningún gráfico.")