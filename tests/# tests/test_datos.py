# ============================================================
# TESTS DE CARGA Y LIMPIEZA DE DATOS
# ============================================================
import pandas as pd
import numpy as np
import pytest


class TestCargaDatos:
    """Tests sobre la carga correcta de las 4 hojas del Excel."""

    def test_recursos_shape(self, df_recursos):
        """Recursos Financieros debe tener 21 filas (2004-2024) y 8 columnas."""
        assert df_recursos.shape == (21, 8), f"Shape inesperado: {df_recursos.shape}"

    def test_sector_shape(self, df_sector):
        """Sector debe tener 105 filas (21 años × 5 sectores)."""
        assert df_sector.shape == (105, 3), f"Shape inesperado: {df_sector.shape}"

    def test_provincias_shape(self, df_provincias):
        """Provincias debe tener 504 filas (21 años × 24 provincias)."""
        assert df_provincias.shape == (504, 3), f"Shape inesperado: {df_provincias.shape}"

    def test_disciplinas_shape(self, df_disciplinas):
        """Disciplinas debe tener 147 filas (21 años × 7 disciplinas)."""
        assert df_disciplinas.shape == (147, 3), f"Shape inesperado: {df_disciplinas.shape}"


class TestValoresEsperados:
    """Tests sobre los valores esperados en las columnas clave."""

    def test_recursos_anios(self, df_recursos):
        """Los años deben ir de 2004 a 2024 sin saltos."""
        anios_esperados = list(range(2004, 2025))
        anios_reales = sorted(df_recursos['ANIO'].tolist())
        assert anios_reales == anios_esperados, f"Faltan años: {set(anios_esperados) - set(anios_reales)}"

    def test_sector_categorias(self, df_sector):
        """Debe haber 5 sectores únicos."""
        sectores = df_sector['SECT_EJEC'].unique()
        assert len(sectores) == 5, f"Se esperaban 5 sectores, hay {len(sectores)}"

    def test_provincias_categorias(self, df_provincias):
        """Debe haber 24 provincias únicas (23 + CABA)."""
        provincias = df_provincias['PROVINCIA'].unique()
        assert len(provincias) == 24, f"Se esperaban 24 provincias, hay {len(provincias)}"

    def test_disciplinas_categorias(self, df_disciplinas):
        """Debe haber 7 disciplinas únicas."""
        disciplinas = df_disciplinas['DISCIPL_ID'].unique()
        assert len(disciplinas) == 7, f"Se esperaban 7 disciplinas, hay {len(disciplinas)}"


class TestCalidadDatos:
    """Tests sobre la calidad de los datos (nulos, negativos, etc.)."""

    def test_no_hay_nulos_recursos(self, df_recursos):
        """No debe haber valores nulos en Recursos Financieros."""
        nulos = df_recursos.isnull().sum().sum()
        assert nulos == 0, f"Hay {nulos} valores nulos en Recursos"

    def test_no_hay_nulos_sector(self, df_sector):
        """No debe haber valores nulos en Sector."""
        assert df_sector.isnull().sum().sum() == 0

    def test_no_hay_nulos_provincias(self, df_provincias):
        """No debe haber valores nulos en Provincias."""
        assert df_provincias.isnull().sum().sum() == 0

    def test_no_hay_nulos_disciplinas(self, df_disciplinas):
        """No debe haber valores nulos en Disciplinas."""
        assert df_disciplinas.isnull().sum().sum() == 0

    def test_inversion_positiva(self, df_recursos):
        """La inversión en pesos corrientes debe ser siempre positiva."""
        assert (df_recursos['INV_ID_PESOS_CORR'] > 0).all(), "Hay valores <= 0"

    def test_pbi_entre_0_y_1(self, df_recursos):
        """El % del PBI debe estar entre 0 y 1 (0% y 100%)."""
        assert (df_recursos['INV_ID_PBI'] >= 0).all()
        assert (df_recursos['INV_ID_PBI'] <= 1).all()

    def test_suma_publica_privada_igual_pbi(self, df_recursos):
        """La suma de inversión pública + privada debe ser ≈ % del PBI."""
        suma = df_recursos['INV_ID_PUB_PBI'] + df_recursos['INV_ID_PRI_PBI']
        # Tolerancia de 0.02 por redondeo
        diff = (suma - df_recursos['INV_ID_PBI']).abs()
        assert (diff < 0.02).all(), f"Discrepancias: {diff[diff >= 0.02].tolist()}"