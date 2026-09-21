# ============================================================
# TESTS DE UTILIDADES
# ============================================================
import pandas as pd
import numpy as np
import pytest


class TestLimpiezaStrings:
    """Tests de la limpieza de strings."""

    def test_provincias_sin_espacios_dobles(self, df_provincias):
        """Ninguna provincia debe tener espacios dobles después de la limpieza."""
        for prov in df_provincias['PROVINCIA'].unique():
            assert '  ' not in prov, f"Provincia con espacios dobles: '{prov}'"

    def test_provincias_sin_espacios_extremos(self, df_provincias):
        """Ninguna provincia debe empezar o terminar con espacio."""
        for prov in df_provincias['PROVINCIA'].unique():
            assert prov == prov.strip(), f"Provincia con espacios extremos: '{prov}'"

    def test_sector_sin_espacios_extremos(self, df_sector):
        """Ningún sector debe empezar o terminar con espacio."""
        for sector in df_sector['SECT_EJEC'].unique():
            assert sector == sector.strip(), f"Sector con espacios: '{sector}'"

    def test_rio_negro_correctamente_escrito(self, df_provincias):
        """'Río Negro' debe estar con un solo espacio (no dos)."""
        provincias = df_provincias['PROVINCIA'].unique().tolist()
        assert 'Río Negro' in provincias, "Falta 'Río Negro' (con un espacio)"
        assert 'Río  Negro' not in provincias, "Todavía hay 'Río  Negro' (dos espacios)"


class TestTiposDeDatos:
    """Tests de tipos de datos."""

    def test_anio_es_entero(self, df_recursos):
        """La columna ANIO debe ser de tipo entero."""
        assert df_recursos['ANIO'].dtype in [np.int64, np.int32, int]

    def test_inversion_es_numerica(self, df_recursos):
        """La columna de inversión debe ser numérica."""
        assert pd.api.types.is_numeric_dtype(df_recursos['INV_ID_PESOS_CORR'])

    def test_provincia_es_string(self, df_provincias):
        """La columna PROVINCIA debe ser de tipo texto (string).

        Pandas 2.0+ usa StringDtype en vez de object. Aceptamos ambos.
        """
        dtype = df_provincias['PROVINCIA'].dtype
        dtype_str = str(dtype).lower()
        # Acepta: object, string, str, StringDtype
        assert dtype == object or 'string' in dtype_str or dtype_str == 'str', (
            f"PROVINCIA debería ser string, pero es {dtype}"
        )


class TestRangos:
    """Tests de rangos válidos."""

    def test_anios_en_rango_valido(self, df_recursos):
        """Los años deben estar entre 2004 y 2024."""
        assert df_recursos['ANIO'].min() == 2004
        assert df_recursos['ANIO'].max() == 2024

    def test_no_hay_duplicados_recursos(self, df_recursos):
        """No debe haber años duplicados en Recursos."""
        assert df_recursos['ANIO'].nunique() == len(df_recursos)

    def test_combinacion_anio_provincia_unica(self, df_provincias):
        """Cada combinación (año, provincia) debe ser única."""
        duplicados = df_provincias.duplicated(subset=['ANIO', 'PROVINCIA']).sum()
        assert duplicados == 0, f"Hay {duplicados} duplicados"

    def test_combinacion_anio_sector_unica(self, df_sector):
        """Cada combinación (año, sector) debe ser única."""
        duplicados = df_sector.duplicated(subset=['ANIO', 'SECT_EJEC']).sum()
        assert duplicados == 0, f"Hay {duplicados} duplicados"