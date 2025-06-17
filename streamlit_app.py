import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from supabase_client import get_client
from streamlit.web.server.websocket_headers import _get_websocket_headers
import json

st.set_page_config(layout="wide", page_title="Gráficos Tronix")

def allow_iframe():
    headers = _get_websocket_headers()
    headers["X-Frame-Options"] = "ALLOWALL"
    headers["Content-Security-Policy"] = "frame-ancestors *"
allow_iframe()

# Leer parámetro de URL
grafico_id = st.query_params.get("grafico_id")
if not grafico_id:
    st.error("Falta el parámetro grafico_id")
    st.stop()

# Consulta a Supabase
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
tipo = meta.get("tipo", "bar")

# === FUNCIÓN PARA DESERIALIZAR DATOS JSON ===
def deserializar_campo(campo):
    """Convierte string JSON a objeto Python si es necesario"""
    if isinstance(campo, str):
        try:
            return json.loads(campo)
        except (json.JSONDecodeError, TypeError):
            return campo
    return campo

# === PROCESAMIENTO MEJORADO DE DATOS ===
def procesar_datos_supabase(meta):
    """Procesa y normaliza los datos de Supabase"""
    
    # Deserializar campos JSON
    labels = deserializar_campo(meta.get("labels", []))
    series_data = deserializar_campo(meta.get("series", []))
    serie_data = deserializar_campo(meta.get("serie", []))
    
    # Debug info
    st.write("DEBUG - Datos deserializados:")
    st.write(f"Labels: {labels}")
    st.write(f"Series: {series_data}")
    st.write(f"Serie: {serie_data}")
    st.write(f"Tipo: {tipo}")
    st.write(f"Multiserie: {meta.get('multiserie', False)}")
    
    return labels, series_data, serie_data

# Procesar datos
labels, series_data, serie_data = procesar_datos_supabase(meta)

# Caso legacy para serie simple
if isinstance(serie_data, dict) and "labels" in serie_data and "values" in serie_data:
    serie_data = [
        {"label": l, "value": v}
        for l, v in zip(serie_data["labels"], serie_data["values"])
    ]

def sanitizar_serie(serie):
    """Limpia y normaliza una serie de datos"""
    if not serie:
        return []
    
    def limpiar_valor(v):
        if isinstance(v, dict):
            return list(v.values())[0] if len(v) == 1 else 0
        if isinstance(v, (int, float)):
            return v
        if isinstance(v, str):
            try: 
                return float(v)
            except: 
                return 0
        return 0
    
    # Asegurar que serie sea una lista
    if not isinstance(serie, list):
        return []
    
    for item in serie:
        if isinstance(item, dict) and "value" in item:
            item["value"] = limpiar_valor(item.get("value"))
    
    return serie

def sanitizar_series(series):
    """Limpia y normaliza múltiples series"""
    if not series or not isinstance(series, list):
        return []
    
    series_limpias = []
    for s in series:
        if isinstance(s, dict) and "name" in s and "data" in s:
            serie_limpia = {
                "name": s["name"],
                "data": sanitizar_serie(s["data"])
            }
            series_limpias.append(serie_limpia)
    
    return series_limpias

# Procesar series según el tipo
if tipo == "multi-line" and meta.get("multiserie", False):
    # Para gráficos multi-línea
    series_procesadas = sanitizar_series(series_data)
    df = None  # No se usa DataFrame para multi-line
else:
    # Para gráficos de serie simple
    serie_procesada = sanitizar_serie(serie_data) if serie_data else []
    df = pd.DataFrame(serie_procesada) if serie_procesada else pd.DataFrame()
    series_procesadas = []

# === RENDER DINÁMICO MEJORADO ===
def render_chart(df, meta, labels, series_procesadas):
    tipo = meta.get("tipo", "bar")
    titulo = meta.get("titulo", "Gráfico Tronix")

    if tipo == "multi-line":
        # Verificar que tenemos los datos necesarios
        if not labels or not isinstance(labels, list) or len(labels) == 0:
            st.error(f"Faltan labels para multi-line. Labels encontrados: {labels}")
            return None
            
        if not series_procesadas or len(series_procesadas) == 0:
            st.error(f"Faltan series para multi-line. Series encontradas: {series_procesadas}")
            return None

        fig = go.Figure()
        
        for s in series_procesadas:
            if not isinstance(s, dict) or "name" not in s or "data" not in s:
                st.warning(f"Serie inválida saltada: {s}")
                continue
                
            # Crear diccionario de puntos para mapeo
            puntos = {}
            for p in s.get("data", []):
                if isinstance(p, dict) and "label" in p:
                    puntos[p["label"]] = p.get("value", 0)
            
            # Crear valores Y mapeados a los labels
            y_vals = [puntos.get(lbl, 0) for lbl in labels]
            
            fig.add_trace(go.Scatter(
                x=labels,
                y=y_vals,
                name=s.get("name", "Serie sin nombre"),
                mode="lines+markers",
                line=dict(width=3),
                marker=dict(size=8)
            ))

    else:
        # Gráficos de serie simple
        if df is None or df.empty:
            st.error("No hay datos para el gráfico")
            return None
            
        if "label" not in df.columns or "value" not in df.columns:
            st.error("Los datos no contienen columnas 'label' y 'value'.")
            return None

        if tipo == "pie":
            fig = px.pie(df, names="label", values="value", title=titulo)
        elif tipo == "line":
            fig = px.line(df, x="label", y="value", markers=True, text="value", title=titulo)
        elif tipo == "area":
            fig = px.area(df, x="label", y="value", title=titulo, markers=True, color="label", text="value")
        elif tipo == "scatter":
            fig = px.scatter(df, x="label", y="value", title=titulo, text="value", color="label")
        elif tipo == "horizontal_bar":
            fig = px.bar(df, y="label", x="value", title=titulo, text="value", orientation="h", color="label")
        else:
            fig = px.bar(df, x="label", y="value", title=titulo, text="value", color="label")

        # Agregar formato de texto solo para gráficos no multi-line
        fig.update_traces(
            texttemplate='%{text} m³',
            marker=dict(line=dict(width=0.5, color='black'))
        )

    # Configuración común del layout
    fig.update_layout(
        colorway=["#228B22", "#8B4513", "#1E90FF", "#800080", "#FF6347", "#9370DB"],
        yaxis_title="Producción (m³)",
        xaxis_title="Fecha",
        title_font_size=24,
        title_x=0.5,  # Centrar título
        uniformtext_minsize=8,
        uniformtext_mode="hide",
        plot_bgcolor="white",
        template="plotly_white",
        margin=dict(t=80, l=60, r=40, b=60),
        height=600,
        showlegend=True if tipo == "multi-line" else True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

# Renderizar el gráfico
fig = render_chart(df, meta, labels, series_procesadas)

if fig:
    st.plotly_chart(fig, use_container_width=True)
else:
    st.error("No se pudo generar el gráfico. Revisa los datos de entrada.")











