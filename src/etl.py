import os
import pandas as pd

# 1. Definir ruta del archivo Excel
data_path = os.path.join("data", "inversion.xlsx")

# 2. Cargar las hojas del Excel
xls = pd.ExcelFile(data_path)
print("Hojas encontradas en el Excel:", xls.sheet_names)

# 3. Leer cada dataset en un DataFrame
df_recursos = pd.read_excel(xls, "Recursos Financieros")
df_sector = pd.read_excel(xls, "Sector")
df_provincias = pd.read_excel(xls, "Provincias")
df_disciplinas = pd.read_excel(xls, "Disciplinas")

# 4. Validaciones iniciales
print("\n--- Recursos Financieros (Head) ---")
print(df_recursos.head(3))

print("\n--- Sector (Head) ---")
print(df_sector.head(3))

print("\n--- Provincias (Head) ---")
print(df_provincias.head(3))

print("\n--- Disciplinas (Head) ---")
print(df_disciplinas.head(3))