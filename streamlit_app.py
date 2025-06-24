import json
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from supabase_client import get_client
from streamlit.web.server.websocket_headers import _get_websocket_headers

# -----------------------------------------------------------------------------
#  ⚙️  Configuración inicial
# -----------------------------------------------------------------------------

def _allow_iframe():
    """Permite que la app sea embebida dentro de un <iframe>."""
    headers = _get_websocket_headers()
    headers["X-Frame-Options"] = "ALLOWALL"
    headers["Content-Security-Policy"] = "frame-ancestors *"

st.set_page_config(layout="wide", page_title="Gráficos Tronix")
_allow_iframe()

# -----------------------------------------------------------------------------
#  🔌  Obtener datos del gráfico desde Supabase
# -----------------------------------------------------------------------------

grafico_id = st.query_params.get("grafico_id")
if not grafico_id:
    st.error("Falta el parámetro grafico_id en la URL")
    st.stop()

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

meta = resp.data  # Dict con todas las columnas de la tabla

# -----------------------------------------------------------------------------
#  🛠️  Utilidades de deserialización y sanitizado
# -----------------------------------------------------------------------------

def _jsonify(field, default):
    """Convierte un string JSON a Python o devuelve el valor tal cual."""
    if field is None:
        return default
    if isinstance(field, (list, dict)):
        return field
    if isinstance(field, str):
        try:
            return json.loads(field)
        except json.JSONDecodeError:
            return default
    return default

def _clean_value(v):
    if isinstance(v, (int, float)):
        return v
    if isinstance(v, str):
        try:
            return float(v)
        except ValueError:
            return 0
    if isinstance(v, dict):
        return list(v.values())[0] if len(v) == 1 else 0
    return 0

# -----------------------------------------------------------------------------
#  📦  Preparar datos según el tipo de gráfico
# -----------------------------------------------------------------------------

tipo = meta.get("tipo", "bar")
labels = _jsonify(meta.get("labels"), [])
series = _jsonify(meta.get("series"), [])
legacy_serie = _jsonify(meta.get("serie"), [])  # compatibilidad vieja

# Si no hay labels/series busca reconstruirlos desde legacy
if tipo == "multi-line" and (not labels or not series):
    if isinstance(legacy_serie, list) and legacy_serie and isinstance(legacy_serie[0], dict):
        labels = sorted({
            p["label"]
            for s in legacy_serie or []
            if isinstance(s, dict) and "data" in s and isinstance(s["data"], list)
            for p in s["data"]
            if isinstance(p, dict) and "label" in p
        })
        # Intentar ordenar por fecha si es posible
        try:
            labels = sorted(labels, key=lambda x: pd.to_datetime(x))
        except Exception:
            pass
        series = legacy_serie

# Sanitizar valores de cada punto
for s in series:
    if isinstance(s, dict) and "data" in s:
        for p in s["data"]:
            if isinstance(p, dict) and "value" in p:
                p["value"] = _clean_value(p["value"])

if tipo != "multi-line":
    # Serie simple → construir DataFrame para Plotly Express
    simple_data = _jsonify(legacy_serie, [])
    for p in simple_data:
        if isinstance(p, dict) and "value" in p:
            p["value"] = _clean_value(p["value"])
    df = pd.DataFrame(simple_data)
else:
    df = pd.DataFrame()  # no se usa

# -----------------------------------------------------------------------------
#  📊  Renderizado del gráfico
# -----------------------------------------------------------------------------

def render_chart():
    titulo = meta.get("titulo", "Gráfico Tronix")

    if tipo == "multi-line":
        if not labels or not series:
            st.error("Faltan labels o series para un gráfico multi‑line.")
            return None

        fig = go.Figure()
        for s in series:
            if not isinstance(s, dict):
                continue
            nombre = s.get("name", "¿?")
            line_style = s.get("line", {})  # Espera {"dash": "dot"}, etc.

            datos_raw = s.get("data", [])
            if all(isinstance(v, (int, float)) or v is None for v in datos_raw):
                # data es una lista plana → mapear usando labels
                puntos = {lbl: val for lbl, val in zip(labels, datos_raw)}
            else:
                # data ya viene con label → usar normal
                puntos = {p["label"]: p.get("value") for p in datos_raw if isinstance(p, dict)}

            y_vals = [puntos.get(lbl, None) for lbl in labels]

            fig.add_trace(go.Scatter(
                x=labels,
                y=y_vals,
                name=nombre,
                mode="lines+markers",
                connectgaps=True if nombre.lower().startswith("proyección") else False,
                line=line_style if isinstance(line_style, dict) else {}
            ))

    else:
        if df.empty or "label" not in df.columns or "value" not in df.columns:
            st.error("Datos insuficientes para el gráfico solicitado.")
            return None

        if tipo == "pie":
            fig = px.pie(df, names="label", values="value", title=titulo)
        elif tipo == "line":
            fig = px.line(df, x="label", y="value", markers=True, text="value", title=titulo)
        elif tipo == "area":
            fig = px.area(df, x="label", y="value", markers=True, title=titulo)
        elif tipo == "scatter":
            fig = px.scatter(df, x="label", y="value", text="value", title=titulo)
        elif tipo == "horizontal_bar":
            fig = px.bar(df, y="label", x="value", orientation="h", text="value", title=titulo)
        else:  # bar
            fig = px.bar(df, x="label", y="value", text="value", title=titulo)

        fig.update_traces(texttemplate="%{text} m³", marker_line_width=0.5, marker_line_color="black")

    fig.update_layout(
        title=dict(text=titulo, x=0.5),
        colorway=["#228B22", "#8B4513", "#1E90FF", "#800080", "#FF6347", "#9370DB"],
        xaxis_title="Fecha", yaxis_title="Producción (m³)", height=600,
        template="plotly_white", plot_bgcolor="white",
        margin=dict(t=80, l=60, r=40, b=60),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

fig = render_chart()
if fig:
    st.plotly_chart(fig, use_container_width=True)











