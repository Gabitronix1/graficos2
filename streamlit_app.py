import streamlit as st
import runpy
import pandas as pd
import plotly.express as px
from supabase_client import get_client

# ── Configuración general ────────────────────────────────────────────────
st.set_page_config(layout="wide", page_title="Gráficos Tronix")

# ── Leer parámetros de la URL ────────────────────────────────────────────
params      = st.query_params.get()
view        = params.get("view", [""])[0]
grafico_id  = params.get("grafico_id", [""])[0]

# ── 1. Dashboard completo: /?view=comparativa ───────────────────────────
if view == "comparativa":
    runpy.run_path("comparativa_produccion_teams.py", run_name="__main__")
    st.stop()

# ── 2. Gráfico individual: /?grafico_id=XYZ ─────────────────────────────
if grafico_id:
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

    meta = resp.data                 # título, tipo, etc.
    serie = meta["serie"]            # lista de dicts {label, value}
    df = pd.DataFrame(serie)

    # Función para renderizar distintos tipos
    def render_dynamic_chart(df, meta):
        tipo = meta.get("tipo", "bar").lower()

        if tipo == "pie":
            fig = px.pie(df, names="label", values="value", title=meta["titulo"])
        elif tipo == "line" and df.shape[1] > 2:
            df_melted = df.melt(id_vars=["label"], var_name="serie", value_name="value")
            fig = px.line(df_melted, x="label", y="value", color="serie",
                          markers=True, text="value", title=meta["titulo"])
        elif tipo == "line":
            fig = px.line(df, x="label", y="value", markers=True,
                          text="value", title=meta["titulo"], color="label")
        elif tipo == "scatter":
            fig = px.scatter(df, x="label", y="value", title=meta["titulo"],
                             text="value", color="label")
        else:  # bar por defecto
            fig = px.bar(df, x="label", y="value", title=meta["titulo"],
                         text="value", color="label")

        fig.update_traces(texttemplate="%{text} m³",
                          textposition="outside",
                          marker=dict(line=dict(width=0.5, color="black")))
        fig.update_layout(plot_bgcolor="white", template="plotly_white")
        return fig

    st.markdown(f"**🔢 Total producido:** {int(df['value'].sum()):,} m³")
    st.plotly_chart(render_dynamic_chart(df, meta), use_container_width=True)
    st.stop()

# ── 3. Página de bienvenida ─────────────────────────────────────────────
st.title("📊 Servidor de Gráficos Tronix")
st.markdown("""
Bienvenido. Puedes:
- Ver el **dashboard completo**: [`?view=comparativa`](?view=comparativa)  
- Ver un **gráfico individual**: [`?grafico_id=TU_ID`](?grafico_id=123)
""")




