import streamlit as st
import plotly.graph_objects as go
import json
import os
from pathlib import Path
from streamlit.runtime.scriptrunner import get_script_run_ctx
from streamlit.web.server.websocket_headers import _get_websocket_headers

DATA_PATH = Path("graficos_guardados")
DATA_PATH.mkdir(exist_ok=True)

st.set_page_config(page_title="Gráfico", layout="centered")

def save_chart_data(grafico_id, data):
    with open(DATA_PATH / f"{grafico_id}.json", "w") as f:
        json.dump(data, f)

def handle_post_request():
    headers = _get_websocket_headers()
    if headers.get("X-Streamlit-Post", None):
        content_len = int(headers.get("Content-Length", 0))
        if content_len > 0:
            raw_data = st.request.body.read(content_len)
            try:
                parsed = json.loads(raw_data.decode("utf-8"))
                grafico_id = parsed.get("grafico_id")
                if grafico_id:
                    save_chart_data(grafico_id, parsed)
                    st.write({"status": "ok", "grafico_id": grafico_id})
                    st.stop()
            except Exception as e:
                st.error(f"Error al guardar: {e}")
                st.stop()

# Página principal
params = st.query_params
grafico_id = params.get("grafico_id")

if grafico_id:
    try:
        with open(DATA_PATH / f"{grafico_id}.json", "r") as f:
            data = json.load(f)
        fig = go.Figure()
        for dataset in data.get("datasets", []):
            fig.add_trace(go.Bar(
                x=data["labels"],
                y=dataset["values"],
                name=dataset["label"],
                marker_color=dataset.get("backgroundColor", None)
            ))
        fig.update_layout(
            title=data.get("title", "Gráfico"),
            yaxis_title=data.get("ylabel", ""),
            xaxis_title=data.get("xlabel", "")
        )
        st.title("Gráfico")
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error al cargar el gráfico: {e}")
else:
    st.info("No se ha especificado ningún gráfico.")