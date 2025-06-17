
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from supabase_client import get_client
from streamlit.web.server.websocket_headers import _get_websocket_headers

st.set_page_config(layout="wide", page_title="Gráficos Tronix")

# 🛡️ Permitir iframes embebidos
def allow_iframe():
    headers = _get_websocket_headers()
    headers["X-Frame-Options"] = "ALLOWALL"
    headers["Content-Security-Policy"] = "frame-ancestors *"
allow_iframe()

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
    .maybe_single()
    .execute()
)

if not resp or not getattr(resp, "data", None):
    st.error("No se encontró el gráfico solicitado")
    st.stop()

meta = resp.data
serie_original = meta.get("serie", None)

# 🔍 Caso legacy: venía como {labels:[], values:[]}
if isinstance(serie_original, dict) and    "labels" in serie_original and "values" in serie_original:
    serie_original = [
        {"label": l, "value": v}
        for l, v in zip(serie_original["labels"], serie_original["values"])
    ]

# 🔐 Blindaje: limpiar value
def sanitizar_serie(serie):
    if not serie:
        return []
    def limpiar_valor(v):
        if isinstance(v, dict):
            return list(v.values())[0] if len(v)==1 else 0
        if isinstance(v, (int, float)):
            return v
        if isinstance(v, str):
            try:
                return float(v)
            except:
                return 0
        return 0
    for item in serie:
        item["value"] = limpiar_valor(item.get("value"))
    return serie

serie = sanitizar_serie(serie_original) if serie_original else []
df    = pd.DataFrame(serie) if serie else pd.DataFrame()

# ✅ Render dinámico
def render_chart(df, meta):
    tipo = meta.get("tipo", "bar")

    # -------------- MULTI‑LINE -----------------
    if tipo == "multi-line":
        labels = meta.get("labels", [])
        series = meta.get("series") or meta.get("serie") or []   # ← fallback

        if not labels or not series:
            st.error(f"Faltan datos para multi-line. Keys meta: {list(meta.keys())}")
            st.stop()

        fig = go.Figure()
        for s in series:
            # dict label→value para rellenar huecos
            mapping = {
                p["label"]: p.get("value", 0)
                for p in s.get("data", [])
                if isinstance(p, dict) and "label" in p
            }
            y_vals = [mapping.get(lbl, 0) for lbl in labels]
            fig.add_trace(go.Scatter(
                x   = labels,
                y   = y_vals,
                name= s.get("name", "¿?"),
                mode= "lines+markers"
            ))
    # ----------- OTROS GRÁFICOS ---------------
    else:
        if ("label" not in df.columns or "value" not in df.columns):
            st.error("Los datos no traen columnas 'label' y 'value'.")
            st.stop()

        if tipo == "pie":
            fig = px.pie(df, names="label", values="value", title=meta["titulo"])
        elif tipo == "line" and df.shape[1] > 2:
            melt = df.melt(id_vars=["label"], var_name="serie", value_name="value")
            fig  = px.line(melt, x="label", y="value", color="serie",
                           markers=True, text="value", title=meta["titulo"])
        elif tipo == "line":
            fig = px.line(df, x="label", y="value", markers=True, text="value",
                          title=meta["titulo"])
        elif tipo == "area":
            fig = px.area(df, x="label", y="value", title=meta["titulo"],
                          markers=True, color="label", text="value")
        elif tipo == "scatter":
            fig = px.scatter(df, x="label", y="value", title=meta["titulo"],
                             text="value", color="label")
        elif tipo == "horizontal_bar":
            fig = px.bar(df, y="label", x="value", title=meta["titulo"],
                         text="value", orientation="h", color="label")
        else:  # bar
            fig = px.bar(df, x="label", y="value", title=meta["titulo"],
                         text="value", color="label")

        # Formato texto solo para no­multi‑line
        fig.update_traces(texttemplate='%{text} m³',
                          marker=dict(line=dict(width=0.5, color='black')))

    # ----------- LAYOUT GLOBAL ---------------
    fig.update_layout(
        colorway=["#228B22", "#8B4513", "#1E90FF", "#800080"],
        yaxis_title="", xaxis_title="", title_font_size=24,
        uniformtext_minsize=8, uniformtext_mode="hide",
        plot_bgcolor="white", template="plotly_white",
        margin=dict(t=60, l=20, r=20, b=40)
    )
    return fig

st.plotly_chart(render_chart(df, meta), use_container_width=True)










