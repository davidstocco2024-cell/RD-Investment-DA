# ============================================================
# ETL: INVERSIÓN EN I+D LATAM
# ============================================================
#
# Flujo:
#
# Excel
#   ↓
# Validación de estructura
#   ↓
# Lectura de datos
#   ↓
# Normalización de dimensiones
#   ↓
# Inicio de transacción
#   ↓
# Limpieza controlada de tablas destino
#   ↓
# Carga de dimensiones en SQL Server
#   ↓
# Recuperación de IDs generados por SQL Server
#   ↓
# Normalización de tablas de hechos
#   ↓
# Carga de hechos
#   ↓
# Validación de carga
#   ↓
# Validación de integridad
#   ↓
# COMMIT
#
# Si ocurre un error:
#
# ROLLBACK
#
# Base de datos:
#     InversionID
#
# Motor:
#     SQL Server
#
# ============================================================

# ============================================================
# IMPORTS
# ============================================================

import logging
import os
import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL


# ============================================================
# CONFIGURACIÓN DE LOGGING
# ============================================================

LOG_WIDTH = 70

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def log_separador(caracter="=", ancho=LOG_WIDTH):
    """Imprime una línea separadora en el log."""
    logger.info(caracter * ancho)


# ============================================================
# CONFIGURACIÓN DEL PROYECTO
# ============================================================

# parents[0] -> Read excel and load into SQL Server
# parents[1] -> scripts
# parents[2] -> raíz del proyecto

BASE_DIR = Path(__file__).resolve().parents[2]


# ============================================================
# CARGAR VARIABLES DE ENTORNO
# ============================================================

# ✅ CORRECCIÓN CHATGPT: ruta explícita al .env
load_dotenv(BASE_DIR / ".env")


# ============================================================
# CONFIGURACIÓN DEL ARCHIVO EXCEL
# ============================================================

if len(sys.argv) > 1:

    ARCHIVO_EXCEL = Path(sys.argv[1])

    if not ARCHIVO_EXCEL.is_absolute():
        ARCHIVO_EXCEL = Path.cwd() / ARCHIVO_EXCEL

    ARCHIVO_EXCEL = ARCHIVO_EXCEL.resolve()

else:

    ARCHIVO_EXCEL = BASE_DIR / "data" / "inversion.xlsx"


# ============================================================
# CONFIGURACIÓN SQL SERVER
# ============================================================

SQL_SERVER_CONFIG = {

    "server": os.getenv("SQL_SERVER", "localhost"),

    "database": os.getenv("SQL_DATABASE", "InversionID"),

    "username": os.getenv("SQL_USERNAME"),

    "password": os.getenv("SQL_PASSWORD"),

    "driver": os.getenv(
        "SQL_DRIVER",
        "ODBC Driver 17 for SQL Server"
    ),
}


# ============================================================
# REGLAS DE NEGOCIO DEL DATASET
# ============================================================

# ------------------------------------------------------------
# GRANULARIDAD DE LAS TABLAS DE HECHOS
# ------------------------------------------------------------
#
# fact_inversion_general
#     Grain: 1 fila por año
#
# fact_inversion_por_sector
#     Grain: 1 fila por año y sector
#
# fact_inversion_por_provincia
#     Grain: 1 fila por año y provincia
#
# fact_inversion_por_disciplina
#     Grain: 1 fila por año y disciplina
#
# ------------------------------------------------------------
# SEMÁNTICA DE PORCENTAJES
# ------------------------------------------------------------
#
#     0.62 = 0.62%
#     1.50 = 1.50%
#
# NO se dividen por 100.
# Regla de negocio confirmada contra el origen.
#
# ------------------------------------------------------------
# COLUMNA DISCIPL_ID
# ------------------------------------------------------------
#
# Aunque se llama DISCIPL_ID, contiene NOMBRES.
#
#     Source column: DISCIPL_ID
#     Source content: discipline description
#     Target column: disciplina_nombre
#     Target PK: disciplina_id (IDENTITY)
#


# ============================================================
# NOMBRES DE HOJAS ESPERADAS
# ============================================================

REQUIRED_SHEETS = {

    "Recursos Financieros",

    "Sector",

    "Provincias",

    "Disciplinas",
}


# ============================================================
# COLUMNAS ESPERADAS
# ============================================================

EXPECTED_COLUMNS = {

    "Recursos Financieros": {

        "ANIO",
        "INV_ID_PESOS_CORR",
        "INV_ID_PESOS_CONS",
        "INV_ID_DOL_CORR",
        "INV_ID_DOL_PPC",
        "INV_ID_PBI",
        "INV_ID_PUB_PBI",
        "INV_ID_PRI_PBI",
    },

    "Sector": {

        "ANIO",
        "SECT_EJEC",
        "INV_ID_PESOS_CORR",
    },

    "Provincias": {

        "ANIO",
        "PROVINCIA",
        "INV_ID_PESOS_CORR",
    },

    "Disciplinas": {

        "ANIO",
        "DISCIPL_ID",
        "INV_ID_PESOS_CORR",
    },
}


# ============================================================
# TABLAS DESTINO
# ============================================================

FACT_TABLES = [

    "fact_inversion_general",
    "fact_inversion_por_sector",
    "fact_inversion_por_provincia",
    "fact_inversion_por_disciplina",
]


DIMENSION_TABLES = [

    "dim_tiempo",
    "dim_sector",
    "dim_provincia",
    "dim_disciplina",
]


# ============================================================
# VALIDACIÓN DE CONFIGURACIÓN
# ============================================================

def validar_configuracion():
    """
    Valida que las credenciales SQL estén configuradas.

    Solo valida username/password porque server, database
    y driver tienen valores por defecto.
    """

    if not SQL_SERVER_CONFIG["username"]:

        raise ValueError(
            "No se encontró SQL_USERNAME. "
            "Configurá las variables de entorno "
            "antes de ejecutar el ETL."
        )

    if not SQL_SERVER_CONFIG["password"]:

        raise ValueError(
            "No se encontró SQL_PASSWORD. "
            "Configurá las variables de entorno "
            "antes de ejecutar el ETL."
        )


# ============================================================
# CONEXIÓN SQL SERVER
# ============================================================

def crear_engine():
    """
    Crea y valida la conexión SQLAlchemy con SQL Server.
    """

    logger.info("Creando conexión con SQL Server...")

    validar_configuracion()

    connection_url = URL.create(

        "mssql+pyodbc",

        username=SQL_SERVER_CONFIG["username"],

        password=SQL_SERVER_CONFIG["password"],

        host=SQL_SERVER_CONFIG["server"],

        database=SQL_SERVER_CONFIG["database"],

        query={
            "driver": SQL_SERVER_CONFIG["driver"]
        }
    )

    engine = create_engine(

        connection_url,

        fast_executemany=True,

        pool_pre_ping=True
    )

    try:

        with engine.connect() as conn:

            conn.execute(text("SELECT 1"))

        logger.info("Conexión a SQL Server exitosa.")

    except Exception as e:

        logger.error(
            f"Error conectando a SQL Server: {e}"
        )

        raise

    return engine


# ============================================================
# LECTURA DEL EXCEL
# ============================================================

def leer_excel(archivo_excel):
    """
    Lee todas las hojas del archivo Excel.

    Retorna un diccionario:
        {nombre_hoja: DataFrame}

    NOTA: la validación de columnas requeridas se hace en
    validar_estructura_excel(), no acá.
    """

    log_separador()
    logger.info("LEYENDO ARCHIVO EXCEL")
    log_separador()

    if not archivo_excel.exists():

        raise FileNotFoundError(
            f"No se encontró el archivo Excel: "
            f"{archivo_excel}"
        )

    logger.info(f"Archivo: {archivo_excel}")

    # --------------------------------------------------------
    # Leer todas las hojas de una sola vez
    # --------------------------------------------------------

    datos = pd.read_excel(
        archivo_excel,
        sheet_name=None
    )

    logger.info(
        f"Hojas encontradas: "
        f"{list(datos.keys())}"
    )

    # --------------------------------------------------------
    # Validar hojas requeridas
    # --------------------------------------------------------

    missing_sheets = (
        REQUIRED_SHEETS
        - set(datos.keys())
    )

    if missing_sheets:

        raise ValueError(
            "Faltan hojas requeridas en el Excel: "
            f"{sorted(missing_sheets)}"
        )

    # --------------------------------------------------------
    # Limpiar nombres de columnas
    # --------------------------------------------------------

    for sheet_name, df in datos.items():

        df.columns = (
            df.columns
            .astype(str)
            .str.strip()
        )

        logger.info(
            f"  {sheet_name}: "
            f"{len(df)} filas x "
            f"{len(df.columns)} columnas"
        )

    return datos

# ============================================================
# VALIDACIÓN DE ESTRUCTURA
# ============================================================
def validar_estructura_excel(datos):
    """
    Valida que las hojas principales contengan
    las columnas requeridas.
    """

    log_separador()
    logger.info("VALIDANDO ESTRUCTURA DEL EXCEL")
    log_separador()

    for sheet_name, required_columns in EXPECTED_COLUMNS.items():

        if sheet_name not in datos:

            raise ValueError(
                f"No existe la hoja requerida: {sheet_name}"
            )

        actual_columns = set(datos[sheet_name].columns)

        missing_columns = required_columns - actual_columns

        if missing_columns:

            raise ValueError(
                f"En la hoja '{sheet_name}' faltan columnas: "
                f"{sorted(missing_columns)}"
            )

        logger.info(f"OK - {sheet_name}")

    logger.info("Estructura del Excel validada correctamente.")


# ============================================================
# UTILIDADES DE LIMPIEZA
# ============================================================

def limpiar_texto(df, columna):
    """
    Limpia una columna de texto:
    - convierte a string
    - elimina espacios
    - convierte valores vacíos a NA
    """
    df[columna] = (
        df[columna]
        .astype("string")
        .str.strip()
        .replace("", pd.NA)
    )
    return df


# ============================================================
# CONVERTIR AÑO
# ============================================================

def convertir_anio(df, columna="ANIO"):
    """
    Convierte ANIO a entero y valida
    que no existan valores inválidos.
    """

    valores = pd.to_numeric(df[columna], errors="coerce")

    if valores.isna().any():

        cantidad = valores.isna().sum()

        raise ValueError(
            f"La columna {columna} contiene "
            f"{cantidad} valores de año inválidos."
        )

    if not (valores == valores.round()).all():

        raise ValueError(
            f"La columna {columna} contiene "
            "valores que no son años enteros."
        )

    df[columna] = valores.astype(int)

    return df


# ============================================================
# CONVERTIR MEDIDAS ENTERAS
# ============================================================
def convertir_medida_entera(df, columnas):
    """
    Convierte medidas monetarias a enteros.

    Antes verifica:
    - valores numéricos
    - ausencia de decimales
    - ausencia de valores negativos

    SQL Server utiliza BIGINT para estas medidas.
    """

    for columna in columnas:

        valores = pd.to_numeric(df[columna], errors="coerce")

        if valores.isna().any():

            cantidad = valores.isna().sum()

            raise ValueError(
                f"La columna {columna} contiene "
                f"{cantidad} valores no numéricos."
            )

        # ----------------------------------------------------
        # ✅ Verificar números enteros (round en vez de %)
        # ----------------------------------------------------

        if not (valores == valores.round()).all():

            raise ValueError(
                f"La columna {columna} contiene "
                "valores decimales pero la BD "
                "espera BIGINT."
            )

        # ----------------------------------------------------
        # Verificar valores negativos
        # ----------------------------------------------------

        if (valores < 0).any():

            raise ValueError(
                f"La columna {columna} contiene "
                "valores negativos."
            )

        df[columna] = valores.astype("int64")

    return df


# ============================================================
# CONVERTIR PORCENTAJES
# ============================================================

def convertir_porcentajes(df, columnas):

    """
    Convierte variables porcentuales a float.

    El dataset utiliza valores como:

        0.62 = 0.62%
        1.50 = 1.50%

    Por eso NO se divide por 100.
    """

    for columna in columnas:

        valores = pd.to_numeric(

            df[columna],

            errors="coerce"
        )

        if valores.isna().any():

            cantidad = valores.isna().sum()

            raise ValueError(

                f"La columna {columna} contiene "
                f"{cantidad} valores no numéricos."
            )

        # ----------------------------------------------------
        # Valores negativos
        # ----------------------------------------------------

        if (valores < 0).any():

            raise ValueError(

                f"La columna {columna} contiene "
                "porcentajes negativos."
            )

        # ----------------------------------------------------
        # Valores mayores a 100
        # ----------------------------------------------------

        if (valores > 100).any():

            raise ValueError(

                f"La columna {columna} contiene "
                "porcentajes superiores a 100."
            )

        df[columna] = valores.astype(float)

    return df


# ============================================================
# DIM_TIEMPO
# ============================================================

def normalizar_tiempo(datos):
    """
    Construye DIM_TIEMPO.

    Modelo:
        anio INT PRIMARY KEY
    """

    log_separador()
    logger.info("NORMALIZANDO DIM_TIEMPO")
    log_separador()

    anios = set()

    for nombre_hoja, df in datos.items():

        if "ANIO" not in df.columns:
            continue

        valores = pd.to_numeric(df["ANIO"], errors="coerce").dropna()

        # ----------------------------------------------------
        # ✅ Vectorizado: detectar no-enteros de una vez
        # ----------------------------------------------------

        if not (valores == valores.round()).all():

            invalidos = valores[valores != valores.round()].unique()

            raise ValueError(
                f"Años inválidos encontrados en "
                f"'{nombre_hoja}': {invalidos}"
            )

        anios.update(valores.astype(int).tolist())

    if not anios:

        raise ValueError("No se encontraron años en el Excel.")

    dim_tiempo = pd.DataFrame({
        "anio": sorted(anios)
    })

    logger.info(f"Años encontrados: {len(dim_tiempo)}")

    logger.info(
        f"Rango: {dim_tiempo['anio'].min()} - "
        f"{dim_tiempo['anio'].max()}"
    )

    return dim_tiempo

# ============================================================
# DIM_SECTOR
# ============================================================

def _normalizar_dimension_texto(df, columna_origen, columna_destino):
    """
    Helper común para normalizar dimensiones de texto.

    - Limpia la columna
    - Elimina NA
    - Elimina duplicados
    - Ordena
    - Renombra a la columna destino
    """

    dimension = df[[columna_origen]].copy()

    dimension = limpiar_texto(dimension, columna_origen)

    dimension = (
        dimension[dimension[columna_origen].notna()]
        .drop_duplicates()
        .sort_values(columna_origen)
        .reset_index(drop=True)
        .rename(columns={columna_origen: columna_destino})
    )

    return dimension


def normalizar_sector(df_sector):
    """Construye DIM_SECTOR."""

    log_separador()
    logger.info("NORMALIZANDO DIM_SECTOR")
    log_separador()

    sectores = _normalizar_dimension_texto(
        df_sector,
        "SECT_EJEC",
        "sector_nombre"
    )

    logger.info(f"Sectores únicos: {len(sectores)}")

    return sectores


def normalizar_provincia(df_provincia):
    """Construye DIM_PROVINCIA."""

    log_separador()
    logger.info("NORMALIZANDO DIM_PROVINCIA")
    log_separador()

    provincias = _normalizar_dimension_texto(
        df_provincia,
        "PROVINCIA",
        "provincia_nombre"
    )

    logger.info(f"Provincias únicas: {len(provincias)}")

    return provincias


def normalizar_disciplina(df_disciplina):
    """Construye DIM_DISCIPLINA."""

    log_separador()
    logger.info("NORMALIZANDO DIM_DISCIPLINA")
    log_separador()

    disciplinas = _normalizar_dimension_texto(
        df_disciplina,
        "DISCIPL_ID",
        "disciplina_nombre"
    )

    logger.info(f"Disciplinas únicas: {len(disciplinas)}")

    return disciplinas

# ============================================================
# LIMPIAR TABLAS DESTINO
# ============================================================

def limpiar_tablas_destino(conn):

    """
    Realiza una carga completa del dataset.

    Primero elimina los registros de las tablas FACT
    y posteriormente los registros de las DIMENSIONES.

    Esto permite volver a ejecutar el ETL sin acumular
    duplicados.

    IMPORTANTE:

    Se utiliza DELETE y no TRUNCATE porque las tablas
    de dimensiones están referenciadas por Foreign Keys.
    """

    logger.info("=" * 60)
    logger.info("LIMPIANDO TABLAS DESTINO")
    logger.info("=" * 60)

    # --------------------------------------------------------
    # Eliminar primero las FACTS
    # --------------------------------------------------------

    for tabla in FACT_TABLES:

        logger.info(
            f"Eliminando datos de {tabla}..."
        )

        conn.execute(
            text(f"DELETE FROM {tabla}")
        )

    # --------------------------------------------------------
    # Eliminar después las DIMENSIONES
    # --------------------------------------------------------

    for tabla in DIMENSION_TABLES:

        logger.info(
            f"Eliminando datos de {tabla}..."
        )

        conn.execute(
            text(f"DELETE FROM {tabla}")
        )

    logger.info(
        "Tablas destino limpiadas correctamente."
    )


# ============================================================
# CARGAR DIMENSIONES
# ============================================================

def cargar_dimensiones(
    conn,
    dim_tiempo,
    dim_sector,
    dim_provincia,
    dim_disciplina
):
    """
    Carga las dimensiones en SQL Server.

    IMPORTANTE:
    sector_id, provincia_id y disciplina_id
    NO son enviados desde Python.
    SQL Server los genera mediante IDENTITY.
    """

    log_separador()
    logger.info("CARGANDO DIMENSIONES")
    log_separador()

    dimensiones = {
        "dim_tiempo": dim_tiempo,
        "dim_sector": dim_sector,
        "dim_provincia": dim_provincia,
        "dim_disciplina": dim_disciplina,
    }

    for nombre, df in dimensiones.items():

        df.to_sql(
            nombre,
            con=conn,
            if_exists="append",
            index=False
        )

        logger.info(f"OK - {nombre}: {len(df)} filas")

# ============================================================
# RECUPERAR MAPPINGS GENERADOS POR SQL SERVER
# ============================================================

def obtener_mappings(conn):

    """
    Recupera los IDs generados por SQL Server.

    Esto es fundamental porque las tablas de dimensiones
    utilizan columnas IDENTITY.
    """

    logger.info("=" * 60)
    logger.info("RECUPERANDO IDS DE SQL SERVER")
    logger.info("=" * 60)

    # --------------------------------------------------------
    # Sector
    # --------------------------------------------------------

    sector_db = pd.read_sql(

        text("""
            SELECT
                sector_id,
                sector_nombre
            FROM dim_sector
        """),

        conn
    )

    sector_map = dict(

        zip(

            sector_db["sector_nombre"],

            sector_db["sector_id"]
        )
    )

    # --------------------------------------------------------
    # Provincia
    # --------------------------------------------------------

    provincia_db = pd.read_sql(

        text("""
            SELECT
                provincia_id,
                provincia_nombre
            FROM dim_provincia
        """),

        conn
    )

    provincia_map = dict(

        zip(

            provincia_db["provincia_nombre"],

            provincia_db["provincia_id"]
        )
    )

    # --------------------------------------------------------
    # Disciplina
    # --------------------------------------------------------

    disciplina_db = pd.read_sql(

        text("""
            SELECT
                disciplina_id,
                disciplina_nombre
            FROM dim_disciplina
        """),

        conn
    )

    disciplina_map = dict(

        zip(

            disciplina_db["disciplina_nombre"],

            disciplina_db["disciplina_id"]
        )
    )

    logger.info(

        f"Sectores recuperados: "
        f"{len(sector_map)}"
    )

    logger.info(

        f"Provincias recuperadas: "
        f"{len(provincia_map)}"
    )

    logger.info(

        f"Disciplinas recuperadas: "
        f"{len(disciplina_map)}"
    )

    return (

        sector_map,

        provincia_map,

        disciplina_map
    )


# ============================================================
# NORMALIZAR HECHOS
# ============================================================

def _normalizar_fact_por_dimension(
    df,
    columna_origen,
    columna_id,
    mapa,
    nombre_dim
):
    """
    Helper para construir una FACT que referencia
    a una dimensión.

    Distingue entre:
    - valores NULL en el origen
    - valores que no existen en la dimensión
    """

    df = convertir_anio(df)
    df = limpiar_texto(df, columna_origen)
    df = convertir_medida_entera(df, ["INV_ID_PESOS_CORR"])

    # --------------------------------------------------------
    # Validar NULL explícitamente
    # --------------------------------------------------------

    nulos = df[df[columna_origen].isna()]

    if not nulos.empty:

        raise ValueError(
            f"La columna {columna_origen} contiene "
            f"{len(nulos)} valores NULL. "
            f"No se pueden cargar en {nombre_dim}."
        )

    # --------------------------------------------------------
    # Validar valores desconocidos
    # --------------------------------------------------------

    desconocidos = (
        set(df[columna_origen])
        - set(mapa.keys())
    )

    if desconocidos:

        raise ValueError(
            f"Se encontraron valores que no existen "
            f"en {nombre_dim}: {sorted(desconocidos)}"
        )

    # --------------------------------------------------------
    # Construir fact
    # --------------------------------------------------------

    fact = df[
        ["ANIO", columna_origen, "INV_ID_PESOS_CORR"]
    ].copy()

    fact[columna_id] = fact[columna_origen].map(mapa)

    fact = fact[
        ["ANIO", columna_id, "INV_ID_PESOS_CORR"]
    ]

    fact.columns = [
        "anio",
        columna_id,
        "inversion_pesos_corrientes",
    ]

    # --------------------------------------------------------
    # Validar PK compuesta
    # --------------------------------------------------------

    if fact[["anio", columna_id]].duplicated().any():

        raise ValueError(
            f"{nombre_dim} contiene duplicados de "
            f"(anio, {columna_id})."
        )

    return fact

def normalizar_hechos(
    datos,
    sector_map,
    provincia_map,
    disciplina_map
):
    """
    Construye las cuatro tablas de hechos.
    """

    log_separador()
    logger.info("NORMALIZANDO TABLAS DE HECHOS")
    log_separador()

    # ========================================================
    # FACT_INVERSION_GENERAL (esta sí es única)
    # ========================================================

    logger.info("Procesando FACT_INVERSION_GENERAL...")

    df_general = datos["Recursos Financieros"].copy()

    df_general = convertir_anio(df_general)

    df_general = convertir_medida_entera(
        df_general,
        [
            "INV_ID_PESOS_CORR",
            "INV_ID_PESOS_CONS",
            "INV_ID_DOL_CORR",
            "INV_ID_DOL_PPC",
        ]
    )

    df_general = convertir_porcentajes(
        df_general,
        [
            "INV_ID_PBI",
            "INV_ID_PUB_PBI",
            "INV_ID_PRI_PBI",
        ]
    )

    fact_general = df_general[
        [
            "ANIO",
            "INV_ID_PESOS_CORR",
            "INV_ID_PESOS_CONS",
            "INV_ID_DOL_CORR",
            "INV_ID_DOL_PPC",
            "INV_ID_PBI",
            "INV_ID_PUB_PBI",
            "INV_ID_PRI_PBI",
        ]
    ].copy()

    fact_general.columns = [
        "anio",
        "inversion_pesos_corrientes",
        "inversion_pesos_constantes",
        "inversion_dolares_corrientes",
        "inversion_dolares_ppp",
        "inversion_pct_pbi",
        "inversion_publica_pct_pbi",
        "inversion_privada_pct_pbi",
    ]

    if fact_general["anio"].duplicated().any():

        duplicados = (
            fact_general[
                fact_general["anio"].duplicated(keep=False)
            ]["anio"].unique()
        )

        raise ValueError(
            "FACT_INVERSION_GENERAL contiene "
            f"años duplicados: {duplicados}"
        )

    logger.info(f"FACT_INVERSION_GENERAL: {len(fact_general)} filas")

    # ========================================================
    # FACT_INVERSION_POR_SECTOR
    # ========================================================

    logger.info("Procesando FACT_INVERSION_POR_SECTOR...")

    fact_sector = _normalizar_fact_por_dimension(
        datos["Sector"].copy(),
        "SECT_EJEC",
        "sector_id",
        sector_map,
        "DIM_SECTOR"
    )

    logger.info(f"FACT_INVERSION_POR_SECTOR: {len(fact_sector)} filas")

    # ========================================================
    # FACT_INVERSION_POR_PROVINCIA
    # ========================================================

    logger.info("Procesando FACT_INVERSION_POR_PROVINCIA...")

    fact_provincia = _normalizar_fact_por_dimension(
        datos["Provincias"].copy(),
        "PROVINCIA",
        "provincia_id",
        provincia_map,
        "DIM_PROVINCIA"
    )

    logger.info(f"FACT_INVERSION_POR_PROVINCIA: {len(fact_provincia)} filas")

    # ========================================================
    # FACT_INVERSION_POR_DISCIPLINA
    # ========================================================

    logger.info("Procesando FACT_INVERSION_POR_DISCIPLINA...")

    fact_disciplina = _normalizar_fact_por_dimension(
        datos["Disciplinas"].copy(),
        "DISCIPL_ID",
        "disciplina_id",
        disciplina_map,
        "DIM_DISCIPLINA"
    )

    logger.info(f"FACT_INVERSION_POR_DISCIPLINA: {len(fact_disciplina)} filas")

    # ========================================================
    # RETORNAR FACTS
    # ========================================================

    return {
        "fact_general": fact_general,
        "fact_sector": fact_sector,
        "fact_provincia": fact_provincia,
        "fact_disciplina": fact_disciplina,
    }


# ============================================================
# CARGAR DIMENSIONES
# ============================================================

def cargar_dimensiones(
    conn,
    dim_tiempo,
    dim_sector,
    dim_provincia,
    dim_disciplina
):
    """
    Carga las dimensiones en SQL Server.

    IMPORTANTE:
    sector_id, provincia_id y disciplina_id
    NO son enviados desde Python.
    SQL Server los genera mediante IDENTITY.

    Retorna un diccionario con los conteos esperados
    para que validar_carga() los compare.
    """

    log_separador()
    logger.info("CARGANDO DIMENSIONES")
    log_separador()

    dimensiones = {
        "dim_tiempo":     dim_tiempo,
        "dim_sector":     dim_sector,
        "dim_provincia":  dim_provincia,
        "dim_disciplina": dim_disciplina,
    }

    conteos_esperados = {}

    for tabla, df in dimensiones.items():

        df.to_sql(
            tabla,
            con=conn,
            if_exists="append",
            index=False
        )

        conteos_esperados[tabla] = len(df)

        logger.info(f"OK - {tabla}: {len(df):,} filas")

    return conteos_esperados


# ============================================================
# CARGAR TABLAS DE HECHOS
# ============================================================

def cargar_hechos(conn, hechos):
    """
    Carga las tablas de hechos en SQL Server.

    Retorna un diccionario con los conteos esperados
    para que validar_carga() los compare.
    """

    log_separador()
    logger.info("CARGANDO TABLAS DE HECHOS")
    log_separador()

    mapeo_tablas = {
        "fact_general":    "fact_inversion_general",
        "fact_sector":     "fact_inversion_por_sector",
        "fact_provincia":  "fact_inversion_por_provincia",
        "fact_disciplina": "fact_inversion_por_disciplina",
    }

    conteos_esperados = {}

    for clave, tabla in mapeo_tablas.items():

        df = hechos[clave]

        df.to_sql(
            tabla,
            con=conn,
            if_exists="append",
            index=False
        )

        conteos_esperados[tabla] = len(df)

        logger.info(f"OK - {tabla}: {len(df):,} filas")

    return conteos_esperados


# ============================================================
# VALIDACIÓN DE CARGA
# ============================================================

def validar_carga(conn, conteos_esperados):
    """
    Valida que la cantidad de registros cargados
    coincida con la cantidad esperada.

    Parámetros
    ----------
    conn : Connection
        Conexión SQLAlchemy activa.
    conteos_esperados : dict
        {nombre_tabla: cantidad_esperada}
    """

    log_separador()
    logger.info("VALIDANDO CARGA")
    log_separador()

    errores = []

    for tabla, esperado in conteos_esperados.items():

        resultado = conn.execute(
            text(f"SELECT COUNT(*) FROM {tabla}")
        )

        cantidad = resultado.scalar()

        if cantidad != esperado:

            errores.append(
                f"{tabla}: esperado {esperado}, "
                f"cargado {cantidad}"
            )

            logger.error(
                f"ERROR - {tabla}: esperado {esperado}, "
                f"cargado {cantidad}"
            )

        else:

            logger.info(
                f"OK - {tabla}: {cantidad:,} filas"
            )

    if errores:

        raise ValueError(
            "Conteos de carga no coinciden:\n"
            + "\n".join(errores)
        )

    logger.info(
        "Conteos de carga validados correctamente."
    )


# ============================================================
# VALIDACIÓN DE INTEGRIDAD
# ============================================================

def validar_integridad(conn):
    """
    Ejecuta controles de integridad en la base:

    - integridad referencial (huérfanos)
    - duplicados de PK compuesta
    - valores negativos
    - porcentajes fuera de rango
    """

    log_separador()
    logger.info("VALIDANDO INTEGRIDAD DE DATOS")
    log_separador()

    # ========================================================
    # 1. INTEGRIDAD REFERENCIAL (huérfanos)
    # ========================================================

    validaciones_fk = {

        "FACT_GENERAL -> DIM_TIEMPO": """
            SELECT COUNT(*)
            FROM fact_inversion_general f
            LEFT JOIN dim_tiempo t
                ON f.anio = t.anio
            WHERE t.anio IS NULL
        """,

        "FACT_SECTOR -> DIM_SECTOR": """
            SELECT COUNT(*)
            FROM fact_inversion_por_sector f
            LEFT JOIN dim_sector s
                ON f.sector_id = s.sector_id
            WHERE s.sector_id IS NULL
        """,

        "FACT_PROVINCIA -> DIM_PROVINCIA": """
            SELECT COUNT(*)
            FROM fact_inversion_por_provincia f
            LEFT JOIN dim_provincia p
                ON f.provincia_id = p.provincia_id
            WHERE p.provincia_id IS NULL
        """,

        "FACT_DISCIPLINA -> DIM_DISCIPLINA": """
            SELECT COUNT(*)
            FROM fact_inversion_por_disciplina f
            LEFT JOIN dim_disciplina d
                ON f.disciplina_id = d.disciplina_id
            WHERE d.disciplina_id IS NULL
        """,
    }

    for nombre, consulta in validaciones_fk.items():

        cantidad = conn.execute(text(consulta)).scalar()

        if cantidad != 0:

            raise ValueError(
                f"{nombre}: {cantidad} huérfanos."
            )

        logger.info(f"OK - Integridad {nombre}")

    # ========================================================
    # 2. DUPLICADOS DE PK (grain del modelo)
    # ========================================================

    validaciones_pk = {

        "fact_inversion_general": """
            SELECT COUNT(*) FROM (
                SELECT anio
                FROM fact_inversion_general
                GROUP BY anio
                HAVING COUNT(*) > 1
            ) AS duplicados
        """,

        "fact_inversion_por_sector": """
            SELECT COUNT(*) FROM (
                SELECT anio, sector_id
                FROM fact_inversion_por_sector
                GROUP BY anio, sector_id
                HAVING COUNT(*) > 1
            ) AS duplicados
        """,

        "fact_inversion_por_provincia": """
            SELECT COUNT(*) FROM (
                SELECT anio, provincia_id
                FROM fact_inversion_por_provincia
                GROUP BY anio, provincia_id
                HAVING COUNT(*) > 1
            ) AS duplicados
        """,

        "fact_inversion_por_disciplina": """
            SELECT COUNT(*) FROM (
                SELECT anio, disciplina_id
                FROM fact_inversion_por_disciplina
                GROUP BY anio, disciplina_id
                HAVING COUNT(*) > 1
            ) AS duplicados
        """,
    }

    for tabla, consulta in validaciones_pk.items():

        cantidad = conn.execute(text(consulta)).scalar()

        if cantidad != 0:

            raise ValueError(
                f"{tabla}: {cantidad} duplicados de PK."
            )

        logger.info(f"OK - Sin duplicados PK en {tabla}")

    # ========================================================
    # 3. VALORES NEGATIVOS
    # ========================================================

    validaciones_negativos = {

        "fact_inversion_general": """
            SELECT COUNT(*)
            FROM fact_inversion_general
            WHERE inversion_pesos_corrientes < 0
               OR inversion_pesos_constantes < 0
               OR inversion_dolares_corrientes < 0
               OR inversion_dolares_ppp < 0
        """,

        "fact_inversion_por_sector": """
            SELECT COUNT(*)
            FROM fact_inversion_por_sector
            WHERE inversion_pesos_corrientes < 0
        """,

        "fact_inversion_por_provincia": """
            SELECT COUNT(*)
            FROM fact_inversion_por_provincia
            WHERE inversion_pesos_corrientes < 0
        """,

        "fact_inversion_por_disciplina": """
            SELECT COUNT(*)
            FROM fact_inversion_por_disciplina
            WHERE inversion_pesos_corrientes < 0
        """,
    }

    for tabla, consulta in validaciones_negativos.items():

        cantidad = conn.execute(text(consulta)).scalar()

        if cantidad != 0:

            raise ValueError(
                f"{tabla}: {cantidad} valores negativos."
            )

        logger.info(f"OK - Sin negativos en {tabla}")

    # ========================================================
    # 4. PORCENTAJES PBI
    # ========================================================

    cantidad = conn.execute(
        text("""
            SELECT COUNT(*)
            FROM fact_inversion_general
            WHERE inversion_pct_pbi < 0
               OR inversion_pct_pbi > 100
               OR inversion_publica_pct_pbi < 0
               OR inversion_publica_pct_pbi > 100
               OR inversion_privada_pct_pbi < 0
               OR inversion_privada_pct_pbi > 100
        """)
    ).scalar()

    if cantidad != 0:

        raise ValueError(
            "Porcentajes PBI fuera del rango 0-100."
        )

    logger.info("OK - Porcentajes PBI dentro de rango.")

    logger.info("Integridad validada correctamente.")


# ============================================================
# MAIN
# ============================================================

def main():

    logger.info("")

    log_separador("=", 70)
    logger.info("ETL INVERSIÓN EN I+D LATAM")
    log_separador("=", 70)

    logger.info("")

    # --------------------------------------------------------
    # Mostrar configuración
    # --------------------------------------------------------

    logger.info(f"Archivo Excel: {ARCHIVO_EXCEL}")
    logger.info(f"Base de datos: {SQL_SERVER_CONFIG['database']}")
    logger.info(f"Servidor SQL:  {SQL_SERVER_CONFIG['server']}")

    # --------------------------------------------------------
    # 1. Leer Excel
    # --------------------------------------------------------

    datos = leer_excel(ARCHIVO_EXCEL)

    # --------------------------------------------------------
    # 2. Validar estructura
    # --------------------------------------------------------

    validar_estructura_excel(datos)

    # --------------------------------------------------------
    # 3. Crear dimensiones
    # --------------------------------------------------------

    dim_tiempo     = normalizar_tiempo(datos)
    dim_sector     = normalizar_sector(datos["Sector"])
    dim_provincia  = normalizar_provincia(datos["Provincias"])
    dim_disciplina = normalizar_disciplina(datos["Disciplinas"])

    # --------------------------------------------------------
    # 4. Crear conexión
    # --------------------------------------------------------

    engine = crear_engine()

    # --------------------------------------------------------
    # 5. TRANSACCIÓN
    # --------------------------------------------------------

    try:

        with engine.begin() as conn:

            logger.info("")
            logger.info("INICIANDO TRANSACCIÓN SQL...")

            # ------------------------------------------------
            # 6. Limpiar tablas destino
            # ------------------------------------------------

            limpiar_tablas_destino(conn)

            # ------------------------------------------------
            # 7. Cargar dimensiones
            # ------------------------------------------------

            conteos_dim = cargar_dimensiones(
                conn,
                dim_tiempo,
                dim_sector,
                dim_provincia,
                dim_disciplina
            )

            # ------------------------------------------------
            # 8. Recuperar IDs
            # ------------------------------------------------

            (
                sector_map,
                provincia_map,
                disciplina_map
            ) = obtener_mappings(conn)

            # ------------------------------------------------
            # 9. Normalizar facts
            # ------------------------------------------------

            hechos = normalizar_hechos(
                datos,
                sector_map,
                provincia_map,
                disciplina_map
            )

            # ------------------------------------------------
            # 10. Cargar facts
            # ------------------------------------------------

            conteos_fact = cargar_hechos(conn, hechos)

            # ------------------------------------------------
            # 11. Validar carga (unificando conteos)
            # ------------------------------------------------

            conteos_esperados = {**conteos_dim, **conteos_fact}

            validar_carga(conn, conteos_esperados)

            # ------------------------------------------------
            # 12. Validar integridad
            # ------------------------------------------------

            validar_integridad(conn)

            logger.info("")
            logger.info("VALIDACIONES COMPLETADAS.")

        # ----------------------------------------------------
        # COMMIT automático
        # ----------------------------------------------------

        logger.info("")
        log_separador("=", 70)
        logger.info("ETL COMPLETADO CORRECTAMENTE")
        log_separador("=", 70)
        logger.info("")

    except Exception as e:

        logger.error("")
        log_separador("=", 70)
        logger.error("ERROR DURANTE EL ETL")
        log_separador("=", 70)
        logger.error(str(e))
        logger.error("")
        logger.error("La transacción fue revertida (ROLLBACK).")

        raise

    finally:

        engine.dispose()

# ============================================================
# EJECUCIÓN
# ============================================================

if __name__ == "__main__":
    main()