import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Fase 1: Entendimiento y Limpieza de Datos 

# 1 Carga de datos

data_path = os.path.join("data", "inversion.xlsx")
xls = pd.ExcelFile(data_path)
print("Hojas encontradas en el Excel:", xls.sheet_names)

df_recursos = pd.read_excel(xls, "Recursos Financieros")
df_sector = pd.read_excel(xls, "Sector")
df_provincias = pd.read_excel(xls, "Provincias")
df_disciplinas = pd.read_excel(xls, "Disciplinas")

# 2 Verificar consistencias

print("--- Verificación de Consistencia ---")

# Sumar la columna de inversión de la hoja Sector, agrupando por año
sector_sum = df_sector.groupby('ANIO')['INV_ID_PESOS_CORR'].sum().reset_index()
sector_sum.columns = ['ANIO', 'SUMA_SECTOR']

# Unir esa suma con el total de Recursos Financieros por año
comparacion = pd.merge(
    df_recursos[['ANIO', 'INV_ID_PESOS_CORR']],
    sector_sum,
    on='ANIO',
    how='left'
)

# Calcular la diferencia
comparacion['DIFERENCIA'] = comparacion['INV_ID_PESOS_CORR'] - comparacion['SUMA_SECTOR']

# Mostrar los primeros 10 años
print("Diferencia entre Total y Suma Sector:")
print(comparacion[['ANIO', 'INV_ID_PESOS_CORR', 'SUMA_SECTOR', 'DIFERENCIA']].head(10))

# 3 Verificaciones adicionales

# Verificar Provincias
prov_sum = df_provincias.groupby('ANIO')['INV_ID_PESOS_CORR'].sum().reset_index()
prov_sum.columns = ['ANIO', 'SUMA_PROV']
comp_prov = pd.merge(df_recursos[['ANIO', 'INV_ID_PESOS_CORR']], prov_sum, on='ANIO', how='left')
comp_prov['DIFERENCIA'] = comp_prov['INV_ID_PESOS_CORR'] - comp_prov['SUMA_PROV']
print("\nDiferencia Total vs Suma Provincias:")
print(comp_prov[['ANIO', 'DIFERENCIA']].head(10))

# Verificar Disciplinas
disc_sum = df_disciplinas.groupby('ANIO')['INV_ID_PESOS_CORR'].sum().reset_index()
disc_sum.columns = ['ANIO', 'SUMA_DISC']
comp_disc = pd.merge(df_recursos[['ANIO', 'INV_ID_PESOS_CORR']], disc_sum, on='ANIO', how='left')
comp_disc['DIFERENCIA'] = comp_disc['INV_ID_PESOS_CORR'] - comp_disc['SUMA_DISC']
print("\nDiferencia Total vs Suma Disciplinas:")
print(comp_disc[['ANIO', 'DIFERENCIA']].head(10))

# 4 Normalizar nombres y limpiar strings 

# Limpiar espacios en blanco al inicio/final de strings
df_sector['SECT_EJEC'] = df_sector['SECT_EJEC'].str.strip()
df_provincias['PROVINCIA'] = df_provincias['PROVINCIA'].str.strip()
df_disciplinas['DISCIPL_ID'] = df_disciplinas['DISCIPL_ID'].str.strip()

# Ver valores únicos para detectar errores
print("\nSectores únicos:")
print(df_sector['SECT_EJEC'].unique())

print("\nProvincias únicas:")
print(sorted(df_provincias['PROVINCIA'].unique()))

print("\nDisciplinas únicas:")
print(df_disciplinas['DISCIPL_ID'].unique())

# 5 Identificar valores faltantes y atipicos

# Ver cuántos nulos hay en cada DataFrame
print("\n--- Valores nulos por columna ---")
print("Recursos:", df_recursos.isnull().sum().sum())
print("Sector:", df_sector.isnull().sum().sum())
print("Provincias:", df_provincias.isnull().sum().sum())
print("Disciplinas:", df_disciplinas.isnull().sum().sum())

# Estadísticas descriptivas básicas
print("\n--- Estadísticas de Recursos Financieros ---")
print(df_recursos.describe())