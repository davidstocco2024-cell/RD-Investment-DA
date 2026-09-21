# ETL: Inversión en I+D LATAM

Script automatizado para cargar datos de inversión en I+D a SQL Server en 5 minutos.

## 📋 Requisitos Previos

### 1. SQL Server instalado
- SQL Server Express (gratuito) o superior
- SQL Server Management Studio (SSMS) para ejecutar scripts

### 2. Python 3.8+
```bash
python --version
```

### 3. ODBC Driver 17 for SQL Server
Windows: Descargar desde https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server

## 🚀 Instalación (5 minutos)

### Paso 1: Clonar/Descargar archivos
```bash
# Asegúrate de tener estos 3 archivos en la misma carpeta:
# - 01_crear_bd_inversion.sql
# - 02_etl_inversion.py
# - README.md (este archivo)
# - inversion.xlsx (tu dataset)
```

### Paso 2: Instalar dependencias Python
```bash
pip install pandas openpyxl sqlalchemy pyodbc
```

### Paso 3: Crear la base de datos en SQL Server

**Opción A: Desde SQL Server Management Studio (SSMS)**
1. Abre SSMS
2. Conecta a tu SQL Server (ej: `localhost` o `NACHO-PC\SQLEXPRESS`)
3. Abre el archivo `01_crear_bd_inversion.sql`
4. Ejecuta (F5 o Ctrl+E)

**Opción B: Desde command line**
```bash
sqlcmd -S localhost -U sa -P tu_password -i 01_crear_bd_inversion.sql
```

### Paso 4: Configurar credenciales Python

Abre `02_etl_inversion.py` y busca esta sección:
```python
SQL_SERVER_CONFIG = {
    'server': 'localhost',  # ← CAMBIAR AQUÍ (tu servidor)
    'database': 'InversionID',
    'username': 'sa',  # ← CAMBIAR AQUÍ (tu usuario)
    'password': 'tu_password',  # ← CAMBIAR AQUÍ (tu contraseña)
    'driver': 'ODBC Driver 17 for SQL Server'
}
```

**Ejemplos de server:**
- `localhost` - SQL Server local
- `NACHO-PC\SQLEXPRESS` - SQL Server Express en la máquina
- `192.168.1.100` - SQL Server remoto
- `servidor.database.windows.net` - Azure SQL

### Paso 5: Ejecutar el script ETL
```bash
python 02_etl_inversion.py
```

Esperado:
```
INFO - ✅ Conexión a SQL Server exitosa
INFO - 📖 Leyendo archivo: inversion.xlsx
INFO - 🔄 Normalizando: DIM_TIEMPO
INFO - 📥 Cargando datos en SQL Server...
INFO - ✅ Todos los datos cargados correctamente
INFO - ✅ ETL COMPLETADO EXITOSAMENTE
```

## ✅ Validar que funcionó

### Desde SSMS:
```sql
-- Conecta a la base de datos InversionID y ejecuta:
USE InversionID;

-- Ver años cargados
SELECT * FROM dim_tiempo;

-- Ver sectores
SELECT * FROM dim_sector;

-- Ver inversión total por año
SELECT * FROM vw_inversion_total_anio;

-- Ver top 10 provincias
SELECT TOP 10 * FROM vw_top_provincias_anio WHERE ranking <= 5;
```

## 📊 Estructura de datos

### Dimensiones
- **dim_tiempo**: 21 años (2004-2024)
- **dim_sector**: 5 sectores (públicos, privados, ONGs, empresas)
- **dim_provincia**: ~24 provincias argentinas
- **dim_disciplina**: ~7 disciplinas científicas

### Tablas de Hechos
- **fact_inversion_general**: Datos agregados nacionales
- **fact_inversion_por_sector**: Inversión desagregada por sector
- **fact_inversion_por_provincia**: Inversión desagregada por provincia
- **fact_inversion_por_disciplina**: Inversión desagregada por disciplina

### Vistas Útiles
```sql
SELECT * FROM vw_inversion_total_anio;  -- Inversión anual
SELECT * FROM vw_top_sectores_anio;      -- Ranking de sectores
SELECT * FROM vw_top_provincias_anio;    -- Ranking de provincias
SELECT * FROM vw_disciplina_tendencia;   -- Evolución disciplinas
```

## 🔧 Troubleshooting

### Error: "Connection refused" o "Named Pipes Provider, error: 40"
**Solución**: Verifica que:
- SQL Server está corriendo (Services → SQL Server)
- El nombre de servidor es correcto
- Las credenciales son válidas

### Error: "ODBC Driver 17 not found"
**Solución**: Instala el driver desde:
https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server

### Error: "Login failed for user 'sa'"
**Solución**: 
- Verifica credenciales en el script
- Si SQL Server está en modo Windows Auth, no uses 'sa'

### Error: "Database InversionID already exists"
**Solución**: Ejecuta en SSMS:
```sql
DROP DATABASE InversionID;
```

## 📈 Próximos pasos (después de esto)

1. **EDA en Python**: Usa este notebook template
   ```python
   import pandas as pd
   import pyodbc
   
   conn = pyodbc.connect(...)
   df = pd.read_sql("SELECT * FROM vw_inversion_total_anio", conn)
   df.plot(x='anio')
   ```

2. **Conectar a Tableau**:
   - Data → New Data Source → SQL Server
   - Server: localhost
   - Database: InversionID
   - Elige la tabla

3. **ML**: Forecasting, clustering con scikit-learn

## 📝 Notas

- El script es **idempotente**: Si lo ejecutas 2 veces, te dará error en la carga (va a intentar insertar duplicados). Para re-ejecutar, borra la BD y corre el SQL nuevamente.
- Los datos están en **pesos corrientes**, **pesos constantes** y **dólares** según columna
- El dataset es **limpio**: sin valores nulos ni anomalías evidentes

## 🆘 Soporte

Si algo no funciona, revisa:
1. ¿Está corriendo SQL Server? 
2. ¿Tenés conexión a la BD? (trata de hacer ping con SSMS)
3. ¿Las credenciales son correctas?
4. ¿El archivo inversion.xlsx está en la ruta correcta?

## 📧 Contacto

Para preguntas sobre el script, pasá por el grupo de Slack!
