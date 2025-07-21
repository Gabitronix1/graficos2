# streamlit_app.py
# ---------------------------------------------------------------------
#  🚀  Servicio de gráficos Tronix — Streamlit ≥ 1.35
# ---------------------------------------------------------------------
import json
from typing import Any, Dict, List, Union

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from supabase_client import get_client as _raw_client

# -----------------------------------------------------------------
#  🎨  Paleta corporativa Arauco
# -----------------------------------------------------------------
ARAUCO_PALETTE = ["#696158", "#BFB800", "#EA7600", "#DFD1A7", "#2AA5A0"]
LOGO_URL = "https://images.seeklogo.com/logo-png/19/1/arauco-logo-png_seeklogo-191105.png"

# (Opcional) Carga .env en local — ignóralo en prod si no lo necesitas
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ---------------------------------------------------------------------
#  🔌  Conexión Supabase
# ---------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def get_client():
    """Wrapper cacheado: usa las env-vars vía tu helper."""
    return _raw_client()


# ---------------------------------------------------------------------
#  🛠️  Utilidades de des-serialización y sanitizado
# ---------------------------------------------------------------------
Json = Union[str, Dict[str, Any], List[Any]]


def _jsonify(field: Json, default: Any) -> Any:
    """Convierte un string JSON a Python o devuelve un valor por defecto."""
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


def _clean_value(v: Any) -> float:
    """Intenta convertir a float; si falla, retorna 0 (para evitar NaNs)."""
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        try:
            return float(v)
        except ValueError:
            return 0.0
    if isinstance(v, dict) and len(v) == 1:
        return float(next(iter(v.values())))
    return 0.0


# ---------------------------------------------------------------------
#  🎨  Estilo dinámico
# ---------------------------------------------------------------------
def _get_palette(meta: Dict[str, Any]) -> List[str]:
    """Devuelve la paleta a usar (meta > corporativa)."""
    pal = _jsonify(meta.get("palette"), [])
    if isinstance(pal, list) and pal:
        return pal          # override desde la BD
    return ARAUCO_PALETTE   # default corporativo


def _get_unit(meta: Dict[str, Any]) -> str:
    return meta.get("unidad", "").strip()


def _axis_labels(meta: Dict[str, Any], unit: str) -> tuple[str, str]:
    x_lab = meta.get("eje_x", "Fecha")
    y_lab = meta.get("eje_y", "Valor")
    if unit:
        y_lab = f"{y_lab} ({unit})"
    return x_lab, y_lab


# ---------------------------------------------------------------------
#  ⚙️  Configuración inicial (iframe friendly)
# ---------------------------------------------------------------------
def _allow_iframe() -> None:
    st.set_page_config(
        layout="wide",
        page_title="Gráficos Tronix",
        initial_sidebar_state="collapsed",
        menu_items=None,
    )
    # Streamlit ≥ 1.35 permite iframes con esta flag oficial
    st.iframe_allow = True


_allow_iframe()

# ---------------------------------------------------------------------
#  🔌  Obtener datos del gráfico desde Supabase
# ---------------------------------------------------------------------
grafico_id: str | None = st.query_params.get("grafico_id")
if not grafico_id:
    st.error("Falta el parámetro ‘grafico_id’ en la URL")
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

meta: Dict[str, Any] = resp.data  # incluye tipo, labels, series, etc.

# ---------------------------------------------------------------------
#  📦  Preparar datos según el tipo de gráfico
# ---------------------------------------------------------------------
tipo: str = meta.get("tipo", "bar")

labels = _jsonify(meta.get("labels"), [])
series = _jsonify(meta.get("series"), [])
legacy_serie = _jsonify(meta.get("serie"), [])  # compat. anterior

# Reconstruir labels/series si vienen en formato legacy
if tipo == "multi-line" and (not labels or not series):
    if (
        isinstance(legacy_serie, list)
        and legacy_serie
        and isinstance(legacy_serie[0], dict)
    ):
        labels = sorted(
            {
                p["label"]
                for s in legacy_serie
                if isinstance(s, dict)
                for p in s.get("data", [])
                if isinstance(p, dict) and "label" in p
            }
        )
        # Ordenar por fecha si se puede
        try:
            labels = sorted(labels, key=pd.to_datetime)
        except Exception:
            pass
        series = legacy_serie

# Sanitizar valores
for s in series:
    if isinstance(s, dict):
        for p in s.get("data", []):
            if isinstance(p, dict) and "value" in p:
                p["value"] = _clean_value(p["value"])

if tipo != "multi-line":
    # Serie simple → df para Plotly Express
    simple_data = _jsonify(legacy_serie, [])
    for p in simple_data:
        if isinstance(p, dict) and "value" in p:
            p["value"] = _clean_value(p["value"])
    df = pd.DataFrame(simple_data)
else:
    df = pd.DataFrame()  # placeholder vacío

# ---------------------------------------------------------------------
#  📊  Renderizado
# ---------------------------------------------------------------------
def render_chart():
    titulo: str = meta.get("titulo", "Gráfico Tronix")
    unit: str = _get_unit(meta)
    palette: List[str] = _get_palette(meta)
    alto: int = int(meta.get("alto", 0))  # 0 = autosize en Plotly
    x_lab, y_lab = _axis_labels(meta, unit)

    # ---------------- multi-line ----------------
    if tipo == "multi-line":
        if not labels or not series:
            st.error("Faltan ‘labels’ o ‘series’ para el gráfico multi-line.")
            return None

        fig = go.Figure()
        for s in series:
            if not isinstance(s, dict):
                continue
            nombre = s.get("name", "¿?")
            line_style = s.get("line", {})  # {"dash": "dot", ...}

            datos_raw = s.get("data", [])
            # Data puede venir lista plana o lista de dicts
            if all(isinstance(v, (int, float)) or v is None for v in datos_raw):
                puntos = {lbl: val for lbl, val in zip(labels, datos_raw)}
            else:
                puntos = {
                    p["label"]: p.get("value")
                    for p in datos_raw
                    if isinstance(p, dict)
                }

            y_vals = [puntos.get(lbl, None) for lbl in labels]

            fig.add_trace(
                go.Scatter(
                    x=labels,
                    y=y_vals,
                    name=nombre,
                    mode="lines+markers",
                    connectgaps=False,
                    line=line_style if isinstance(line_style, dict) else {},
                )
            )

    # ---------------- todo lo demás ----------------
    else:
        if df.empty or {"label", "value"} - set(df.columns):
            st.error("Datos insuficientes para el gráfico solicitado.")
            return None

        if tipo == "pie":
            fig = px.pie(df, names="label", values="value", title=titulo)
        elif tipo == "line":
            fig = px.line(
                df, x="label", y="value", markers=True, text="value", title=titulo
            )
        elif tipo == "area":
            fig = px.area(df, x="label", y="value", markers=True, title=titulo)
        elif tipo == "scatter":
            fig = px.scatter(df, x="label", y="value", text="value", title=titulo)
        elif tipo == "horizontal_bar":
            fig = px.bar(
                df, y="label", x="value", orientation="h", text="value", title=titulo
            )
        else:  # bar (default)
            fig = px.bar(df, x="label", y="value", text="value", title=titulo)

        # Texto con unidad & formato
        fig.update_traces(
            texttemplate="%{text:.1f}" + (f" {unit}" if unit else ""),
            marker_line_width=0.5,
            marker_line_color="black",
        )

  # ---------------- layout común ----------------
    fig.update_layout(
        # ---------- títulos & tipografía ----------
        title=dict(text=titulo, x=0.0, xanchor="left"),  # evita que choque con la leyenda
        font=dict(family="Inter, sans-serif", size=13),

        # ---------- colores & ejes ----------
        colorway=palette,
        xaxis_title=x_lab,
        yaxis_title=y_lab,

        # ---------- tamaño & márgenes ----------
        autosize=True,
        height=None if alto == 0 else alto,
        margin=dict(t=100, l=20, r=20, b=40),  # más espacio a la derecha para logo

        # ---------- leyenda ----------
        legend=dict(
            orientation="v",
            yanchor="top", y=1,
            xanchor="right", x=1.15  # fuera de la zona del gráfico
        ),

        template="plotly_white",
        plot_bgcolor="white",
    )

    fig.add_layout_image(
        dict(
            source=LOGO_URL,
            xref="paper", yref="paper",
            x=1.02, y=1.18,      # ajusta según necesites
            sizex=0.18, sizey=0.18,
            xanchor="right", yanchor="top",
            layer="above", opacity=0.9,
        )
    )
    fig.add_shape(
        type="rect",
        xref="paper", yref="paper",
        x0=0, y0=0, x1=1, y1=1,
        fillcolor="#F9F7F2",  # beige muy suave
        layer="below",
        line_width=0,
    )


    return fig

# ---------------------------------------------------------------------
#  📈  Mostrar gráfico
# ---------------------------------------------------------------------
fig = render_chart()
if fig:
    st.plotly_chart(fig, use_container_width=True)









