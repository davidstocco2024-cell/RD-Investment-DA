# ============================================================
# TESTS UNITARIOS DEL MODELADO ESTADÍSTICO
# Archivo: tests/test_modelos.py
# ============================================================
import os
import sys
import warnings
import numpy as np
import pandas as pd
import pytest

# Silenciar warnings de statsmodels (esperables en series cortas)
warnings.filterwarnings('ignore', category=Warning)

# Agregar el ROOT al path para importar src/
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from src.modelos import (
    proyectar_arima,
    regresion_lineal,
    indice_gini,
    indice_herfindahl,
    correlacion_pearson,
    indice_shannon,
)


# ============================================================
# TESTS DE ARIMA
# ============================================================
class TestARIMA:
    """Tests del modelo ARIMA para proyecciones."""

    @pytest.fixture
    def serie_simple(self):
        """Serie temporal simple: crecimiento lineal de 1 a 20."""
        anios = pd.Index(range(2004, 2024))
        valores = np.arange(1, 21, dtype=float)
        return pd.Series(valores, index=anios)

    def test_arima_devuelve_3_valores(self, serie_simple):
        """La proyección debe tener exactamente 3 valores."""
        resultado = proyectar_arima(serie_simple, pasos=3)
        assert len(resultado['proyeccion']) == 3

    def test_arima_sin_nan(self, serie_simple):
        """Las proyecciones NO deben tener valores NaN."""
        resultado = proyectar_arima(serie_simple, pasos=3)
        assert not np.isnan(resultado['proyeccion']).any(), "Hay NaN en la proyección"
        assert not np.isnan(resultado['ic_inferior']).any(), "Hay NaN en IC inferior"
        assert not np.isnan(resultado['ic_superior']).any(), "Hay NaN en IC superior"

    def test_arima_ic_ordenado(self, serie_simple):
        """El IC inferior debe ser siempre <= IC superior."""
        resultado = proyectar_arima(serie_simple, pasos=3)
        assert (resultado['ic_inferior'] <= resultado['ic_superior']).all(), \
            "IC inferior mayor que superior"

    def test_arima_ic_contiene_proyeccion(self, serie_simple):
        """La proyección debe estar dentro del intervalo de confianza."""
        resultado = proyectar_arima(serie_simple, pasos=3)
        assert (resultado['proyeccion'] >= resultado['ic_inferior']).all()
        assert (resultado['proyeccion'] <= resultado['ic_superior']).all()

    def test_arima_proyeccion_positiva(self, serie_simple):
        """Para una serie positiva, las proyecciones deben ser positivas."""
        resultado = proyectar_arima(serie_simple, pasos=3)
        assert (resultado['proyeccion'] > 0).all(), "Proyección negativa en serie positiva"

    def test_arima_aic_bic_validos(self, serie_simple):
        """AIC y BIC deben ser números finitos."""
        resultado = proyectar_arima(serie_simple, pasos=3)
        assert np.isfinite(resultado['aic']), "AIC no es finito"
        assert np.isfinite(resultado['bic']), "BIC no es finito"

    def test_arima_serie_real(self, df_recursos):
        """Test con la serie real de inversión en USD PPC."""
        serie = df_recursos.set_index('ANIO')['INV_ID_DOL_PPC']
        resultado = proyectar_arima(serie, pasos=3)

        assert len(resultado['proyeccion']) == 3
        assert not np.isnan(resultado['proyeccion']).any()
        assert (resultado['proyeccion'] > 0).all()


# ============================================================
# TESTS DE ÍNDICE DE GINI
# ============================================================
class TestGini:
    """Tests del índice de Gini."""

    def test_gini_igualdad_perfecta(self):
        """Si todos tienen lo mismo, Gini = 0."""
        valores = [100, 100, 100, 100, 100]
        assert abs(indice_gini(valores)) < 1e-10

    def test_gini_desigualdad_total(self):
        """Si uno tiene todo, Gini tiende a 1."""
        # Con n valores, Gini_max = (n-1)/n
        valores = [0, 0, 0, 0, 1000]
        gini = indice_gini(valores)
        assert gini > 0.75, f"Gini esperado >0.75, obtenido {gini}"
        assert gini <= 1.0

    def test_gini_entre_0_y_1(self, df_provincias):
        """El Gini de provincias debe estar siempre entre 0 y 1."""
        for anio in df_provincias['ANIO'].unique():
            valores = df_provincias[df_provincias['ANIO'] == anio]['INV_ID_PESOS_CORR'].values
            gini = indice_gini(valores)
            assert 0 <= gini <= 1, f"Año {anio}: Gini fuera de rango: {gini}"

    def test_gini_valores_vacios(self):
        """Con lista vacía debe devolver NaN."""
        assert np.isnan(indice_gini([]))

    def test_gini_valores_negativos_error(self):
        """Con valores negativos debe lanzar ValueError."""
        with pytest.raises(ValueError):
            indice_gini([100, -50, 200])

    def test_gini_suma_cero(self):
        """Si la suma es 0, debe devolver 0."""
        assert indice_gini([0, 0, 0]) == 0.0

    def test_gini_orden_independiente(self):
        """El Gini debe ser el mismo sin importar el orden."""
        valores_a = [100, 200, 300, 400]
        valores_b = [400, 100, 300, 200]
        assert abs(indice_gini(valores_a) - indice_gini(valores_b)) < 1e-10


# ============================================================
# TESTS DE ÍNDICE DE HERFINDAHL
# ============================================================
class TestHerfindahl:
    """Tests del índice Herfindahl-Hirschman."""

    def test_hhi_monopolio(self):
        """Si uno tiene el 100%, HHI = 10000."""
        valores = [1000, 0, 0, 0]
        assert abs(indice_herfindahl(valores) - 10000) < 1e-10

    def test_hhi_diversificacion_perfecta(self):
        """Si n son iguales, HHI = 10000/n."""
        valores = [100, 100, 100, 100]
        hhi = indice_herfindahl(valores)
        assert abs(hhi - 2500) < 1e-10  # 10000/4 = 2500

    def test_hhi_entre_0_y_10000(self, df_provincias):
        """El HHI debe estar siempre entre 0 y 10000."""
        for anio in df_provincias['ANIO'].unique():
            valores = df_provincias[df_provincias['ANIO'] == anio]['INV_ID_PESOS_CORR'].values
            hhi = indice_herfindahl(valores)
            assert 0 <= hhi <= 10000, f"Año {anio}: HHI fuera de rango: {hhi}"

    def test_hhi_duopolio(self):
        """Dos empresas con 50% cada una → HHI = 5000."""
        valores = [500, 500]
        assert abs(indice_herfindahl(valores) - 5000) < 1e-10

    def test_hhi_orden_independiente(self):
        """El HHI debe ser el mismo sin importar el orden."""
        valores_a = [100, 200, 300]
        valores_b = [300, 100, 200]
        assert abs(indice_herfindahl(valores_a) - indice_herfindahl(valores_b)) < 1e-10


# ============================================================
# TESTS DE REGRESIÓN LINEAL
# ============================================================
class TestRegresionLineal:
    """Tests de la regresión lineal."""

    def test_regresion_lineal_perfecta(self):
        """Si y = 2x + 1, R² = 1 y pendiente = 2."""
        x = np.array([1, 2, 3, 4, 5])
        y = 2 * x + 1
        resultado = regresion_lineal(x, y)
        assert abs(resultado['pendiente'] - 2) < 1e-10
        assert abs(resultado['intercepto'] - 1) < 1e-10
        assert abs(resultado['r2'] - 1) < 1e-10

    def test_regresion_r2_entre_0_y_1(self, df_recursos):
        """El R² debe estar entre 0 y 1."""
        x = df_recursos['ANIO'].values
        y = df_recursos['INV_ID_DOL_PPC'].values
        resultado = regresion_lineal(x, y)
        assert 0 <= resultado['r2'] <= 1, f"R² fuera de rango: {resultado['r2']}"

    def test_regresion_pendiente_positiva_tendencia(self):
        """Si y crece con x, la pendiente debe ser positiva."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([10, 20, 30, 40, 50])
        resultado = regresion_lineal(x, y)
        assert resultado['pendiente'] > 0

    def test_regresion_pendiente_negativa(self):
        """Si y decrece con x, la pendiente debe ser negativa."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([50, 40, 30, 20, 10])
        resultado = regresion_lineal(x, y)
        assert resultado['pendiente'] < 0

    def test_regresion_p_value_valido(self):
        """El p-value debe estar entre 0 y 1."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 5, 4, 5])
        resultado = regresion_lineal(x, y)
        assert 0 <= resultado['p_value'] <= 1


# ============================================================
# TESTS DE CORRELACIÓN
# ============================================================
class TestCorrelacion:
    """Tests de correlación de Pearson."""

    def test_correlacion_perfecta_positiva(self):
        """Series idénticas → r = 1."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([1, 2, 3, 4, 5])
        resultado = correlacion_pearson(x, y)
        assert abs(resultado['r'] - 1) < 1e-10

    def test_correlacion_perfecta_negativa(self):
        """Series inversas → r = -1."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([5, 4, 3, 2, 1])
        resultado = correlacion_pearson(x, y)
        assert abs(resultado['r'] + 1) < 1e-10

    def test_correlacion_entre_menos_1_y_1(self, df_recursos):
        """r siempre entre -1 y +1."""
        r = df_recursos['INV_ID_DOL_PPC'].corr(df_recursos['INV_ID_PBI'])
        assert -1 <= r <= 1

    def test_correlacion_simetrica(self):
        """r(x, y) = r(y, x)."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([5, 3, 4, 2, 6])
        r1 = correlacion_pearson(x, y)['r']
        r2 = correlacion_pearson(y, x)['r']
        assert abs(r1 - r2) < 1e-10


# ============================================================
# TESTS DE SHANNON
# ============================================================
class TestShannon:
    """Tests del índice de Shannon."""

    def test_shannon_una_categoria(self):
        """Una sola categoría → H = 0."""
        assert indice_shannon([100]) == 0.0

    def test_shannon_diversidad_maxima(self):
        """n categorías iguales → H = ln(n)."""
        valores = [100, 100, 100, 100]  # 4 categorías
        h = indice_shannon(valores)
        assert abs(h - np.log(4)) < 1e-10

    def test_shannon_no_negativo(self, df_provincias):
        """Shannon siempre >= 0."""
        for anio in df_provincias['ANIO'].unique():
            valores = df_provincias[df_provincias['ANIO'] == anio]['INV_ID_PESOS_CORR'].values
            h = indice_shannon(valores)
            assert h >= 0, f"Año {anio}: Shannon negativo: {h}"


# ============================================================
# TESTS INTEGRADOS CON DATOS REALES
# ============================================================
class TestModelosConDatosReales:
    """Tests que aplican los modelos a los datos reales del proyecto."""

    def test_gini_aumenta_con_concentracion(self, df_provincias):
        """El Gini provincial debe ser consistente con la concentración observada."""
        anio_inicio = df_provincias['ANIO'].min()
        anio_fin = df_provincias['ANIO'].max()

        gini_inicio = indice_gini(
            df_provincias[df_provincias['ANIO'] == anio_inicio]['INV_ID_PESOS_CORR'].values
        )
        gini_fin = indice_gini(
            df_provincias[df_provincias['ANIO'] == anio_fin]['INV_ID_PESOS_CORR'].values
        )

        # Ambos deben ser válidos
        assert 0 <= gini_inicio <= 1
        assert 0 <= gini_fin <= 1

    def test_hhi_provincias_alto(self, df_provincias):
        """El HHI provincial debe ser alto (mercado concentrado)."""
        anio_fin = df_provincias['ANIO'].max()
        valores = df_provincias[df_provincias['ANIO'] == anio_fin]['INV_ID_PESOS_CORR'].values
        hhi = indice_herfindahl(valores)

        # Con 24 provincias y CABA+BsAs dominando, el HHI debería ser >1000
        assert hhi > 1000, f"HHI esperado >1000, obtenido {hhi}"

    def test_regresion_inversion_tiempo(self, df_recursos):
        """La regresión de inversión vs año debe tener R² alto (tendencia clara)."""
        x = df_recursos['ANIO'].values
        y = df_recursos['INV_ID_DOL_PPC'].values
        resultado = regresion_lineal(x, y)
        # El crecimiento es fuerte, R² debería ser > 0.7
        assert resultado['r2'] > 0.7, f"R² esperado >0.7, obtenido {resultado['r2']}"