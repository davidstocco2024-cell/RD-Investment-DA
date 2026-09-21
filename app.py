# ============================================================
# DASHBOARD INTERACTIVO — INVERSIÓN EN I+D EN ARGENTINA
# Archivo: app.py
# Framework: Streamlit + Plotly
# ============================================================

import os
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# ============================================================
# CONFIGURACIÓN DE LA PÁGINA
# ============================================================
st.set_page_config(
    page_title="I+D Argentina 2004-2024",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CSS PERSONALIZADO (simplificado para evitar problemas de contraste)
# ============================================================
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# CARGA DE DATOS (cacheada para performance)
# ============================================================
@st.cache_data
def cargar_datos():
    """Carga las hojas del Excel en DataFrames."""
    data_path = os.path.join("data", "inversion.xlsx")

    df_recursos    = pd.read_excel(data_path, "Recursos Financieros")
    df_sector      = pd.read_excel(data_path, "Sector")
    df_provincias  = pd.read_excel(data_path, "Provincias")
    df_disciplinas = pd.read_excel(data_path, "Disciplinas")

    # Limpieza
    df_sector['SECT_EJEC']       = df_sector['SECT_EJEC'].str.strip()
    df_provincias['PROVINCIA']   = df_provincias['PROVINCIA'].str.replace(r'\s+', ' ', regex=True).str.strip()
    df_disciplinas['DISCIPL_ID'] = df_disciplinas['DISCIPL_ID'].str.strip()

    return df_recursos, df_sector, df_provincias, df_disciplinas

df_recursos, df_sector, df_provincias, df_disciplinas = cargar_datos()

# ============================================================
# HEADER
# ============================================================
st.markdown('<div class="main-header">🔬 Inversión en I+D en Argentina</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Análisis interactivo 2004-2024 | Sector, Territorio y Disciplina</div>', unsafe_allow_html=True)
st.markdown("---")

# ============================================================
# SIDEBAR — FILTROS
# ============================================================
st.sidebar.header("🎛️ Filtros")

# Selector de rango de años
anio_min = int(df_recursos['ANIO'].min())
anio_max = int(df_recursos['ANIO'].max())
rango_anios = st.sidebar.slider(
    "Rango de años",
    min_value=anio_min,
    max_value=anio_max,
    value=(anio_min, anio_max),
    step=1
)

# Selector de variable monetaria
variable = st.sidebar.selectbox(
    "Variable de inversión",
    options=['INV_ID_DOL_PPC', 'INV_ID_PESOS_CORR', 'INV_ID_DOL_CORR'],
    format_func=lambda x: {
        'INV_ID_DOL_PPC': 'USD PPC (constantes)',
        'INV_ID_PESOS_CORR': 'Pesos corrientes',
        'INV_ID_DOL_CORR': 'USD corrientes'
    }[x]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Secciones")
seccion = st.sidebar.radio(
    "Ir a:",
    options=[
        "📈 Resumen General",
        "🏢 Por Sector",
        "🗺️ Por Provincia",
        "🔬 Por Disciplina"
    ]
)

st.sidebar.markdown("---")
st.sidebar.caption("Datos: Inversión en I+D Argentina 2004-2024")
st.sidebar.caption("Fuente: [Nombre de la fuente]")

# ============================================================
# FILTRAR DATOS SEGÚN RANGO DE AÑOS
# ============================================================
mask_recursos    = (df_recursos['ANIO'] >= rango_anios[0]) & (df_recursos['ANIO'] <= rango_anios[1])
mask_sector      = (df_sector['ANIO'] >= rango_anios[0]) & (df_sector['ANIO'] <= rango_anios[1])
mask_provincias  = (df_provincias['ANIO'] >= rango_anios[0]) & (df_provincias['ANIO'] <= rango_anios[1])
mask_disciplinas = (df_disciplinas['ANIO'] >= rango_anios[0]) & (df_disciplinas['ANIO'] <= rango_anios[1])

df_recursos_f    = df_recursos[mask_recursos].copy()
df_sector_f      = df_sector[mask_sector].copy()
df_provincias_f  = df_provincias[mask_provincias].copy()
df_disciplinas_f = df_disciplinas[mask_disciplinas].copy()

# ============================================================
# SECCIÓN 1: RESUMEN GENERAL
# ============================================================
if seccion == "📈 Resumen General":

    # KPIs mejorados
    col1, col2, col3, col4 = st.columns(4)

    valor_inicial = df_recursos_f[variable].iloc[0]
    valor_final   = df_recursos_f[variable].iloc[-1]
    variacion     = (valor_final / valor_inicial - 1) * 100
    pbi_promedio  = df_recursos_f['INV_ID_PBI'].mean() * 100
    pbi_ultimo    = df_recursos_f['INV_ID_PBI'].iloc[-1] * 100

    with col1:
        st.metric(
            label=f"Inversión {rango_anios[1]}",
            value=f"{valor_final:,.0f}",
            delta=f"{variacion:+.1f}% vs {rango_anios[0]}"
        )
    with col2:
        st.metric(
            label="% PBI (promedio período)",
            value=f"{pbi_promedio:.2f}%"
        )
    with col3:
        st.metric(
            label="% PBI (último año)",
            value=f"{pbi_ultimo:.2f}%",
            delta=f"{(pbi_ultimo - pbi_promedio):+.2f} pp vs promedio"
        )
    with col4:
        st.metric(
            label="Años analizados",
            value=f"{len(df_recursos_f)}"
        )

    st.markdown("---")

    # Gráfico: Evolución temporal
    st.subheader("📈 Evolución de la Inversión")

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df_recursos_f['ANIO'], y=df_recursos_f[variable],
        mode='lines+markers',
        name='Inversión',
        line=dict(color='#1f77b4', width=3),
        marker=dict(size=8),
        hovertemplate='<b>Año %{x}</b><br>Inversión: %{y:,.0f}<extra></extra>'
    ))

    fig.update_layout(
        title=f"Evolución de la Inversión ({variable})",
        xaxis_title="Año",
        yaxis_title="Inversión",
        hovermode='x unified',
        height=450,
        template='plotly_white'
    )

    st.plotly_chart(fig, use_container_width=True)

    # Gráfico secundario: % PBI y Público vs Privado
    col_a, col_b = st.columns(2)

    with col_a:
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=df_recursos_f['ANIO'], y=df_recursos_f['INV_ID_PBI'] * 100,
            mode='lines+markers',
            line=dict(color='#d62728', width=3),
            marker=dict(size=8),
            fill='tozeroy',
            fillcolor='rgba(214,39,40,0.1)',
            hovertemplate='<b>Año %{x}</b><br>% PBI: %{y:.2f}%<extra></extra>'
        ))
        fig2.update_layout(
            title="Esfuerzo en I+D (% del PBI)",
            xaxis_title="Año", yaxis_title="% del PBI",
            height=400, template='plotly_white'
        )
        st.plotly_chart(fig2, use_container_width=True)

    with col_b:
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(
            x=df_recursos_f['ANIO'], y=df_recursos_f['INV_ID_PUB_PBI'] * 100,
            mode='lines+markers', name='Público',
            line=dict(color='#2ca02c', width=3)
        ))
        fig3.add_trace(go.Scatter(
            x=df_recursos_f['ANIO'], y=df_recursos_f['INV_ID_PRI_PBI'] * 100,
            mode='lines+markers', name='Privado',
            line=dict(color='#ff7f0e', width=3)
        ))
        fig3.update_layout(
            title="Inversión Pública vs Privada (% del PBI)",
            xaxis_title="Año", yaxis_title="% del PBI",
            height=400, template='plotly_white',
            hovermode='x unified'
        )
        st.plotly_chart(fig3, use_container_width=True)

# ============================================================
# SECCIÓN 2: POR SECTOR
# ============================================================
elif seccion == "🏢 Por Sector":

    st.subheader("🏢 Inversión por Sector de Ejecución")

    pivot = df_sector_f.pivot_table(
        index='ANIO', columns='SECT_EJEC',
        values='INV_ID_PESOS_CORR', aggfunc='sum'
    ).fillna(0)
    pivot_pct = pivot.div(pivot.sum(axis=1), axis=0) * 100

    col1, col2 = st.columns(2)

    with col1:
        fig = go.Figure()
        for sector in pivot_pct.columns:
            fig.add_trace(go.Scatter(
                x=pivot_pct.index, y=pivot_pct[sector],
                mode='lines', name=sector,
                stackgroup='one',
                hovertemplate='<b>%{fullData.name}</b><br>Año %{x}<br>%{y:.1f}%<extra></extra>'
            ))

        fig.update_layout(
            title="Composición por Sector (100% apilado)",
            xaxis_title="Año", yaxis_title="% del total",
            height=500, template='plotly_white',
            hovermode='x unified'
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        ultimo_anio = int(df_sector_f['ANIO'].max())
        ranking = df_sector_f[df_sector_f['ANIO'] == ultimo_anio].groupby('SECT_EJEC')['INV_ID_PESOS_CORR'].sum().sort_values()

        fig2 = go.Figure(go.Bar(
            x=ranking.values, y=ranking.index,
            orientation='h',
            marker=dict(color=ranking.values, colorscale='Blues'),
            text=[f'{v:,.0f}' for v in ranking.values],
            textposition='auto',
            hovertemplate='<b>%{y}</b><br>%{x:,.0f}<extra></extra>'
        ))
        fig2.update_layout(
            title=f"Ranking por Sector ({ultimo_anio})",
            xaxis_title="Inversión (pesos corrientes)", yaxis_title="",
            height=500, template='plotly_white'
        )
        st.plotly_chart(fig2, use_container_width=True)

# ============================================================
# SECCIÓN 3: POR PROVINCIA
# ============================================================
elif seccion == "🗺️ Por Provincia":

    st.subheader("🗺️ Distribución Territorial de la Inversión")

    total_anio = df_provincias_f.groupby('ANIO')['INV_ID_PESOS_CORR'].transform('sum')
    df_provincias_f['PROPORCION'] = df_provincias_f['INV_ID_PESOS_CORR'] / total_anio * 100

    col1, col2 = st.columns(2)

    with col1:
        ultimo_anio = int(df_provincias_f['ANIO'].max())
        top_prov = df_provincias_f[df_provincias_f['ANIO'] == ultimo_anio].nlargest(10, 'INV_ID_PESOS_CORR')

        fig = px.bar(
            top_prov.sort_values('INV_ID_PESOS_CORR'),
            x='INV_ID_PESOS_CORR', y='PROVINCIA',
            orientation='h',
            color='INV_ID_PESOS_CORR',
            color_continuous_scale='Reds',
            title=f"Top 10 Provincias ({ultimo_anio})",
            labels={'INV_ID_PESOS_CORR': 'Inversión', 'PROVINCIA': ''}
        )
        fig.update_layout(height=500, template='plotly_white', showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        anio_inicio = int(df_provincias_f['ANIO'].min())
        prov_ini = df_provincias_f[df_provincias_f['ANIO'] == anio_inicio].set_index('PROVINCIA')['PROPORCION']
        prov_fin = df_provincias_f[df_provincias_f['ANIO'] == ultimo_anio].set_index('PROVINCIA')['PROPORCION']

        comp = pd.DataFrame({str(anio_inicio): prov_ini, str(ultimo_anio): prov_fin}).fillna(0)
        comp = comp.sort_values(str(ultimo_anio), ascending=True).tail(12)

        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            y=comp.index, x=comp[str(anio_inicio)],
            name=str(anio_inicio), orientation='h',
            marker=dict(color='#1f77b4')
        ))
        fig2.add_trace(go.Bar(
            y=comp.index, x=comp[str(ultimo_anio)],
            name=str(ultimo_anio), orientation='h',
            marker=dict(color='#d62728')
        ))
        fig2.update_layout(
            title=f"Comparativa {anio_inicio} vs {ultimo_anio}",
            xaxis_title="% del total nacional",
            barmode='group', height=500, template='plotly_white'
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("🔥 Heatmap: Provincias × Años")

    pivot_prov = df_provincias_f.pivot_table(
        index='PROVINCIA', columns='ANIO',
        values='PROPORCION', aggfunc='sum'
    ).fillna(0)
    pivot_prov = pivot_prov.loc[pivot_prov.mean(axis=1).sort_values(ascending=False).index]

    fig3 = px.imshow(
        pivot_prov,
        aspect='auto',
        color_continuous_scale='YlOrRd',
        labels=dict(x="Año", y="Provincia", color="% del total"),
        title="Distribución Territorial de la Inversión en I+D"
    )
    fig3.update_layout(height=700, template='plotly_white')
    st.plotly_chart(fig3, use_container_width=True)

# ============================================================
# SECCIÓN 4: POR DISCIPLINA
# ============================================================
elif seccion == "🔬 Por Disciplina":

    st.subheader("🔬 Inversión por Disciplina Científica")

    st.info("⚠️ La hoja de Disciplinas no suma el total nacional. Los porcentajes son sobre el total categorizado.")

    pivot_disc = df_disciplinas_f.pivot_table(
        index='ANIO', columns='DISCIPL_ID',
        values='INV_ID_PESOS_CORR', aggfunc='sum'
    ).fillna(0)
    pivot_disc_pct = pivot_disc.div(pivot_disc.sum(axis=1), axis=0) * 100

    fig = go.Figure()
    for disc in pivot_disc_pct.columns:
        fig.add_trace(go.Scatter(
            x=pivot_disc_pct.index, y=pivot_disc_pct[disc],
            mode='lines', name=disc,
            stackgroup='one',
            hovertemplate='<b>%{fullData.name}</b><br>Año %{x}<br>%{y:.1f}%<extra></extra>'
        ))

    fig.update_layout(
        title="Composición por Disciplina (100% apilado)",
        xaxis_title="Año", yaxis_title="% del total categorizado",
        height=500, template='plotly_white',
        hovermode='x unified'
    )
    st.plotly_chart(fig, use_container_width=True)

    ultimo_anio = int(df_disciplinas_f['ANIO'].max())
    ranking = df_disciplinas_f[df_disciplinas_f['ANIO'] == ultimo_anio].groupby('DISCIPL_ID')['INV_ID_PESOS_CORR'].sum().sort_values()

    fig2 = px.bar(
        x=ranking.values, y=ranking.index,
        orientation='h',
        color=ranking.values,
        color_continuous_scale='Viridis',
        title=f"Ranking por Disciplina ({ultimo_anio})",
        labels={'x': 'Inversión', 'y': ''}
    )
    fig2.update_layout(height=500, template='plotly_white', showlegend=False)
    st.plotly_chart(fig2, use_container_width=True)

# ============================================================
# FOOTER
# ============================================================
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #999;'>"
    "Dashboard desarrollado con Streamlit + Plotly | "
    "Datos: Inversión en I+D Argentina 2004-2024"
    "</div>",
    unsafe_allow_html=True
)