import streamlit as st
import plotly.graph_objects as go
import json
import os
from pathlib import Path
from fastapi import FastAPI, Request
from threading import Thread
import uvicorn

# Carpeta para guardar gráficos
DATA_PATH = Path("graficos_guardados")
DATA_PATH.mkdir(exist_ok=True)

# Inicializamos FastAPI
api = FastAPI()

@api.post("/api/graficos")
async def recibir_grafico(request: Request):
    try:
        data = await request.json()
        grafico_id = data.get("grafico_id")
        if not grafico_id:
            return {"error": "grafico_id es requerido"}
        with open(DATA_PATH / f"{grafico_id}.json", "w") as f:
            json.dump(data, f)
        return {"status": "ok", "grafico_id": grafico_id}
    except Exception as e:
        return {"error": str(e)}

# Servidor FastAPI en hilo aparte
def run_api():
    uvicorn.run(api, host="0.0.0.0", port=8000)

Thread(target=run_api, daemon=True).start()

# Streamlit App
st.set_page_config(page_title="Gráfico", layout="centered")
st.title("Gráfico")

params = st.query_params
grafico_id = params.get("grafico_id", None)

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
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error al cargar el gráfico: {e}")
else:
    st.info("No se ha especificado ningún gráfico.")