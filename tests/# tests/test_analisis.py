class TestConsistencia:
    """Tests de que las hojas cuadren entre sí (tolerancia relativa)."""

    def test_sector_suma_al_total(self, df_recursos, df_sector):
        """La suma de inversión por sector debe ser ≈ al total nacional.

        Tolerancia: 1% del total del año. En valores grandes los redondeos
        acumulados pueden dar diferencias de miles de pesos.
        """
        total_por_anio = df_recursos.set_index('ANIO')['INV_ID_PESOS_CORR']
        suma_sector = df_sector.groupby('ANIO')['INV_ID_PESOS_CORR'].sum()

        for anio in total_por_anio.index:
            if anio in suma_sector.index:
                diff = abs(total_por_anio[anio] - suma_sector[anio])
                tolerancia = total_por_anio[anio] * 0.01
                assert diff <= tolerancia, (
                    f"Año {anio}: diferencia = {diff}, tolerancia = {tolerancia:.2f}"
                )

    def test_provincias_suma_al_total(self, df_recursos, df_provincias):
        """La suma de inversión por provincia debe ser ≈ al total nacional."""
        total_por_anio = df_recursos.set_index('ANIO')['INV_ID_PESOS_CORR']
        suma_prov = df_provincias.groupby('ANIO')['INV_ID_PESOS_CORR'].sum()

        for anio in total_por_anio.index:
            if anio in suma_prov.index:
                diff = abs(total_por_anio[anio] - suma_prov[anio])
                tolerancia = total_por_anio[anio] * 0.01
                assert diff <= tolerancia, (
                    f"Año {anio}: diferencia = {diff}, tolerancia = {tolerancia:.2f}"
                )

    def test_disciplinas_no_cuadra(self, df_recursos, df_disciplinas):
        """La hoja de Disciplinas NO cuadra con el total. Documenta limitación."""
        total_por_anio = df_recursos.set_index('ANIO')['INV_ID_PESOS_CORR']
        suma_disc = df_disciplinas.groupby('ANIO')['INV_ID_PESOS_CORR'].sum()

        for anio in total_por_anio.index:
            if anio in suma_disc.index:
                diff = total_por_anio[anio] - suma_disc[anio]
                assert diff > 100, f"Año {anio}: la brecha de Disciplinas es {diff}"