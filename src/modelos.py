# ============================================================
# MÓDULOS DE MODELADO ESTADÍSTICO
# Archivo: src/modelos.py
# ============================================================
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.tsa.arima.model import ARIMA


# ============================================================
# 1. MODELOS DE SERIES TEMPORALES
# ============================================================
def proyectar_arima(serie, pasos=3, orden=(1, 1, 1)):
    """
    Proyecta una serie temporal con ARIMA.

    Parámetros
    ----------
    serie : pd.Series con índice de años
    pasos : int, cantidad de años a proyectar
    orden : tuple, (p, d, q)

    Retorna
    -------
    dict con: proyeccion, ic_inferior, ic_superior, aic, bic
    """
    modelo = ARIMA(serie, order=orden)
    resultado = modelo.fit()

    forecast = resultado.get_forecast(steps=pasos)
    proyeccion = forecast.predicted_mean
    ic = forecast.conf_int(alpha=0.05)

    return {
        'proyeccion': proyeccion.values,
        'ic_inferior': ic.iloc[:, 0].values,
        'ic_superior': ic.iloc[:, 1].values,
        'aic': resultado.aic,
        'bic': resultado.bic
    }


def regresion_lineal(x, y):
    """
    Ajusta una regresión lineal simple y devuelve los parámetros.

    Retorna
    -------
    dict con: pendiente, intercepto, r2, p_value
    """
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    return {
        'pendiente': slope,
        'intercepto': intercept,
        'r2': r_value ** 2,
        'p_value': p_value,
        'std_err': std_err
    }


# ============================================================
# 2. ÍNDICES DE CONCENTRACIÓN
# ============================================================
def indice_gini(valores):
    """
    Calcula el Índice de Gini (0 = igualdad perfecta, 1 = desigualdad total).

    Parámetros
    ----------
    valores : array-like de números no negativos

    Retorna
    -------
    float entre 0 y 1
    """
    valores = np.array(valores, dtype=float)

    if len(valores) == 0:
        return np.nan
    if (valores < 0).any():
        raise ValueError("El índice de Gini requiere valores no negativos")
    if valores.sum() == 0:
        return 0.0

    # Ordenar
    valores_ordenados = np.sort(valores)
    n = len(valores_ordenados)

    # Fórmula: G = (2 * sum(i * x_i) - (n+1) * sum(x_i)) / (n * sum(x_i))
    indices = np.arange(1, n + 1)
    numerador = 2 * np.sum(indices * valores_ordenados) - (n + 1) * valores_ordenados.sum()
    denominador = n * valores_ordenados.sum()

    return numerador / denominador


def indice_herfindahl(valores):
    """
    Calcula el Índice Herfindahl-Hirschman (HHI).

    HHI = suma de los cuadrados de las participaciones (en %).
    Rango: 0 (diversificación perfecta) a 10000 (monopolio).

    Parámetros
    ----------
    valores : array-like de números no negativos

    Retorna
    -------
    float entre 0 y 10000
    """
    valores = np.array(valores, dtype=float)

    if len(valores) == 0:
        return np.nan
    if (valores < 0).any():
        raise ValueError("El HHI requiere valores no negativos")

    total = valores.sum()
    if total == 0:
        return 0.0

    # Participaciones en porcentaje
    participaciones = (valores / total) * 100
    hhi = np.sum(participaciones ** 2)

    return hhi


# ============================================================
# 3. CORRELACIONES Y DIVERSIDAD
# ============================================================
def correlacion_pearson(x, y):
    """
    Calcula el coeficiente de correlación de Pearson entre dos series.

    Retorna
    -------
    dict con: r, p_value
    """
    r, p_value = stats.pearsonr(x, y)
    return {'r': r, 'p_value': p_value}


def indice_shannon(valores):
    """
    Calcula el índice de diversidad de Shannon.

    H = -sum(p_i * ln(p_i))
    0 = sin diversidad (una sola categoría)
    ln(n) = diversidad máxima

    Parámetros
    ----------
    valores : array-like de números no negativos

    Retorna
    -------
    float >= 0
    """
    valores = np.array(valores, dtype=float)

    if len(valores) == 0:
        return np.nan
    if (valores < 0).any():
        raise ValueError("El índice de Shannon requiere valores no negativos")

    total = valores.sum()
    if total == 0:
        return 0.0

    proporciones = valores / total
    # Filtrar ceros para evitar log(0)
    proporciones = proporciones[proporciones > 0]

    return -np.sum(proporciones * np.log(proporciones))