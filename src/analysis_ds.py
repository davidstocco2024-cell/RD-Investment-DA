# ============================================================
# ANÁLISIS DE INVERSIÓN EN I+D EN ARGENTINA (2004-2024)
# Archivo: src/analisis.py
# ============================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# ============================================================
# CONFIGURACIÓN DE RUTAS Y ENTORNO
# ============================================================
# Localiza la raíz del proyecto independientemente de dónde ejecutes el comando
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "inversion.xlsx"
OUTPUTS_DIR = BASE_DIR / "outputs"

# Crear carpeta de outputs si no existe
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

# Configuración gráfica
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 10

# ============================================================
# CARGA DE DATOS
# ============================================================
if not DATA_PATH.exists():
    raise FileNotFoundError(f"❌ No se encontró el archivo de datos en: {DATA_PATH}")

df_recursos    = pd.read_excel(DATA_PATH, "Recursos Financieros")
df_sector      = pd.read_excel(DATA_PATH, "Sector")
df_provincias  = pd.read_excel(DATA_PATH, "Provincias")
df_disciplinas = pd.read_excel(DATA_PATH, "Disciplinas")

# Limpieza de strings
df_sector['SECT_EJEC']       = df_sector['SECT_EJEC'].str.strip()
df_provincias['PROVINCIA']   = df_provincias['PROVINCIA'].str.replace(r'\s+', ' ', regex=True).str.strip()
df_disciplinas['DISCIPL_ID'] = df_disciplinas['DISCIPL_ID'].str.strip()

print("=" * 60)
print("✅ Datos cargados y limpios correctamente")
print("=" * 60)
print(f"Recursos Financieros: {df_recursos.shape[0]} filas")
print(f"Sector:               {df_sector.shape[0]} filas")
print(f"Provincias:           {df_provincias.shape[0]} filas")
print(f"Disciplinas:          {df_disciplinas.shape[0]} filas")
print()


# ============================================================
# GRÁFICO 1: EVOLUCIÓN TEMPORAL (USD PPC + % del PBI)
# ============================================================
print("📊 Generando Gráfico 1: Evolución temporal...")

fig, ax1 = plt.subplots(figsize=(13, 6))

# Eje izquierdo: Inversión en dólares PPC
color1 = '#1f77b4'
ax1.plot(df_recursos['ANIO'], df_recursos['INV_ID_DOL_PPC'],
         color=color1, marker='o', linewidth=2, markersize=7,
         label='Inversión (millones USD PPC)')
ax1.set_xlabel('Año', fontsize=12)
ax1.set_ylabel('Millones de USD PPC (constantes)', color=color1, fontsize=12)
ax1.tick_params(axis='y', labelcolor=color1)
ax1.set_xticks(df_recursos['ANIO'])
ax1.tick_params(axis='x', rotation=45)

# Eje derecho: % del PBI
ax2 = ax1.twinx()
color2 = '#d62728'
ax2.plot(df_recursos['ANIO'], df_recursos['INV_ID_PBI'],
         color=color2, marker='s', linewidth=2, markersize=7,
         linestyle='--', label='% del PBI')
ax2.set_ylabel('% del PBI destinado a I+D', color=color2, fontsize=12)
ax2.tick_params(axis='y', labelcolor=color2)
ax2.set_ylim(0, 0.75)

# Título y leyenda
plt.title('Evolución de la Inversión en I+D en Argentina (2004-2024)',
          fontsize=14, fontweight='bold')
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=10)

plt.tight_layout()
out1 = OUTPUTS_DIR / "01_evolucion_temporal.png"
plt.savefig(out1, dpi=150, bbox_inches='tight')
plt.close()

print(f"   ✅ Guardado: {out1}")
print()


# ============================================================
# GRÁFICO 2: COMPOSICIÓN POR SECTOR (ÁREA APILADA 100%)
# ============================================================
print("📊 Generando Gráfico 2: Composición por sector...")

# Pivotear: años en filas, sectores en columnas
pivot_sector = df_sector.pivot_table(
    index='ANIO',
    columns='SECT_EJEC',
    values='INV_ID_PESOS_CORR',
    aggfunc='sum'
).fillna(0)

# Convertir a porcentajes
pivot_sector_pct = pivot_sector.div(pivot_sector.sum(axis=1), axis=0) * 100

# Graficar
fig, ax = plt.subplots(figsize=(13, 7))
pivot_sector_pct.plot(
    kind='area',
    stacked=True,
    ax=ax,
    colormap='tab10',
    alpha=0.85,
    linewidth=0.5
)

ax.set_title('Composición de la Inversión en I+D por Sector de Ejecución (2004-2024)',
             fontsize=14, fontweight='bold')
ax.set_xlabel('Año', fontsize=12)
ax.set_ylabel('Porcentaje del total (%)', fontsize=12)
ax.set_ylim(0, 100)
ax.set_xticks(pivot_sector_pct.index)
ax.tick_params(axis='x', rotation=45)
ax.legend(title='Sector', bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=9)

plt.tight_layout()
out2 = OUTPUTS_DIR / "02_composicion_sector.png"
plt.savefig(out2, dpi=150, bbox_inches='tight')
plt.close()

print(f"   ✅ Guardado: {out2}")
print()


# ============================================================
# GRÁFICO 3: TOP PROVINCIAS 2004 vs 2024
# ============================================================
print("📊 Generando Gráfico 3: Top provincias...")

# Calcular total nacional por año
total_por_anio = df_provincias.groupby('ANIO')['INV_ID_PESOS_CORR'].transform('sum')
df_provincias['PROPORCION'] = df_provincias['INV_ID_PESOS_CORR'] / total_por_anio * 100

# Filtrar 2004 y 2024
prov_2004 = df_provincias[df_provincias['ANIO'] == 2004].set_index('PROVINCIA')['PROPORCION']
prov_2024 = df_provincias[df_provincias['ANIO'] == 2024].set_index('PROVINCIA')['PROPORCION']

# DataFrame comparativo
df_comp = pd.DataFrame({'2004': prov_2004, '2024': prov_2024})
df_comp['Cambio (pp)'] = df_comp['2024'] - df_comp['2004']
df_comp = df_comp.sort_values('2024', ascending=True).tail(12)

# Graficar
fig, ax = plt.subplots(figsize=(12, 8))
y_pos = np.arange(len(df_comp))
height = 0.38

ax.barh(y_pos - height/2, df_comp['2004'], height, label='2004',
        color='#1f77b4', alpha=0.85)
ax.barh(y_pos + height/2, df_comp['2024'], height, label='2024',
        color='#d62728', alpha=0.85)

ax.set_yticks(y_pos)
ax.set_yticklabels(df_comp.index, fontsize=10)
ax.set_xlabel('Participación en la inversión nacional (%)', fontsize=12)
ax.set_title('Top 12 Provincias por Participación en Inversión en I+D\n(Comparativa 2004 vs 2024)',
             fontsize=14, fontweight='bold')
ax.legend(loc='lower right', fontsize=11)
ax.grid(axis='x', alpha=0.3)

plt.tight_layout()
out3 = OUTPUTS_DIR / "03_top_provincias.png"
plt.savefig(out3, dpi=150, bbox_inches='tight')
plt.close()

print(f"   ✅ Guardado: {out3}")
print()


# ============================================================
# RESUMEN FINAL
# ============================================================
print("=" * 60)
print("🎉 ANÁLISIS COMPLETADO")
print("=" * 60)
print(f"Los 3 gráficos fueron generados exitosamente en:\n{OUTPUTS_DIR}")
print("  1. 01_evolucion_temporal.png")
print("  2. 02_composicion_sector.png")
print("  3. 03_top_provincias.png")
print("=" * 60)

# ============================================================
# GRÁFICO 4: EVOLUCIÓN POR DISCIPLINA (ÁREA APILADA 100%)
# ============================================================
print("📊 Generando Gráfico 4: Evolución por disciplina...")

# Pivotear: años en filas, disciplinas en columnas
pivot_disc = df_disciplinas.pivot_table(
    index='ANIO',
    columns='DISCIPL_ID',
    values='INV_ID_PESOS_CORR',
    aggfunc='sum'
).fillna(0)

# Convertir a porcentajes (composición dentro de cada año)
pivot_disc_pct = pivot_disc.div(pivot_disc.sum(axis=1), axis=0) * 100

# Graficar
fig, ax = plt.subplots(figsize=(13, 7))
pivot_disc_pct.plot(
    kind='area',
    stacked=True,
    ax=ax,
    colormap='tab10',
    alpha=0.85,
    linewidth=0.5
)

ax.set_title('Composición de la Inversión en I+D por Disciplina (2004-2024)',
             fontsize=14, fontweight='bold')
ax.set_xlabel('Año', fontsize=12)
ax.set_ylabel('Porcentaje del total categorizado (%)', fontsize=12)
ax.set_ylim(0, 100)
ax.set_xticks(pivot_disc_pct.index)
ax.tick_params(axis='x', rotation=45)
ax.legend(title='Disciplina', bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=9)

plt.tight_layout()
plt.savefig('outputs/04_evolucion_disciplinas.png', dpi=150, bbox_inches='tight')
plt.show()
plt.close()

print("   ✅ Guardado: outputs/04_evolucion_disciplinas.png")
print()


# ============================================================
# GRÁFICO 5: HEATMAP DE PROVINCIAS POR AÑO
# ============================================================
print("📊 Generando Gráfico 5: Heatmap de provincias...")

# Calcular proporción de cada provincia sobre el total del año
total_por_anio = df_provincias.groupby('ANIO')['INV_ID_PESOS_CORR'].transform('sum')
df_provincias['PROPORCION'] = df_provincias['INV_ID_PESOS_CORR'] / total_por_anio * 100

# Pivotear: provincias en filas, años en columnas
pivot_prov = df_provincias.pivot_table(
    index='PROVINCIA',
    columns='ANIO',
    values='PROPORCION',
    aggfunc='sum'
).fillna(0)

# Ordenar provincias por su promedio histórico (para que el heatmap se vea ordenado)
pivot_prov = pivot_prov.loc[pivot_prov.mean(axis=1).sort_values(ascending=False).index]

# Graficar heatmap
fig, ax = plt.subplots(figsize=(14, 9))
sns.heatmap(
    pivot_prov,
    cmap='YlOrRd',
    annot=False,
    fmt='.1f',
    linewidths=0.5,
    linecolor='white',
    cbar_kws={'label': 'Participación en la inversión nacional (%)'},
    ax=ax
)

ax.set_title('Distribución Territorial de la Inversión en I+D por Provincia y Año (2004-2024)',
             fontsize=14, fontweight='bold')
ax.set_xlabel('Año', fontsize=12)
ax.set_ylabel('Provincia', fontsize=12)
ax.tick_params(axis='x', rotation=45)
ax.tick_params(axis='y', rotation=0)

plt.tight_layout()
plt.savefig('outputs/05_heatmap_provincias.png', dpi=150, bbox_inches='tight')
plt.show()
plt.close()

print("   ✅ Guardado: outputs/05_heatmap_provincias.png")
print()