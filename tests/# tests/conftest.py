# ============================================================
# CONFTEST: Fixtures compartidas entre todos los tests
# ============================================================
import os
import sys
import pytest
import pandas as pd

# ============================================================
# RUTAS: Usamos rutas absolutas para evitar problemas con cwd
# ============================================================
# Estrategia: subir desde tests/ hasta la raíz del proyecto
# con múltiples alternativas por si una falla.

# Intento 1: subir 2 niveles desde este archivo
_este_archivo = os.path.abspath(__file__)
ROOT_DIR = os.path.dirname(os.path.dirname(_este_archivo))

# Verificación: si "data/inversion.xlsx" no existe ahí, subimos un nivel más
EXCEL_PATH = os.path.join(ROOT_DIR, "data", "inversion.xlsx")

if not os.path.exists(EXCEL_PATH):
    # Intento 2: subir 3 niveles (por si conftest está más adentro)
    ROOT_DIR = os.path.dirname(ROOT_DIR)
    EXCEL_PATH = os.path.join(ROOT_DIR, "data", "inversion.xlsx")

if not os.path.exists(EXCEL_PATH):
    # Intento 3: buscar el Excel subiendo por el árbol de carpetas
    _dir = os.path.dirname(_este_archivo)
    for _ in range(5):  # máximo 5 niveles
        _candidato = os.path.join(_dir, "data", "inversion.xlsx")
        if os.path.exists(_candidato):
            ROOT_DIR = _dir
            EXCEL_PATH = _candidato
            break
        _dir = os.path.dirname(_dir)

# Verificación final
if not os.path.exists(EXCEL_PATH):
    raise FileNotFoundError(
        f"❌ No se encontró el Excel.\n"
        f"Buscado en: {EXCEL_PATH}\n"
        f"Directorio actual: {os.getcwd()}\n"
        f"Este archivo está en: {_este_archivo}"
    )

# Agregar la raíz al path para importar módulos
sys.path.insert(0, ROOT_DIR)

# Info de debug (útil si algo falla)
print(f"✅ Excel encontrado en: {EXCEL_PATH}")
print(f"📁 ROOT_DIR: {ROOT_DIR}")


# ============================================================
# FIXTURES
# ============================================================
@pytest.fixture(scope="session")
def data_path():
    """Ruta absoluta al archivo Excel."""
    return EXCEL_PATH


@pytest.fixture(scope="session")
def df_recursos(data_path):
    """DataFrame de Recursos Financieros."""
    return pd.read_excel(data_path, "Recursos Financieros")


@pytest.fixture(scope="session")
def df_sector(data_path):
    """DataFrame de Sector."""
    df = pd.read_excel(data_path, "Sector")
    df['SECT_EJEC'] = df['SECT_EJEC'].str.strip()
    return df


@pytest.fixture(scope="session")
def df_provincias(data_path):
    """DataFrame de Provincias."""
    df = pd.read_excel(data_path, "Provincias")
    df['PROVINCIA'] = df['PROVINCIA'].str.replace(r'\s+', ' ', regex=True).str.strip()
    return df


@pytest.fixture(scope="session")
def df_disciplinas(data_path):
    """DataFrame de Disciplinas."""
    df = pd.read_excel(data_path, "Disciplinas")
    df['DISCIPL_ID'] = df['DISCIPL_ID'].str.strip()
    return df