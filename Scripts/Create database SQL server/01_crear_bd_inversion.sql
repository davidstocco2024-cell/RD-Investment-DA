-- ==============================================
-- BASE DE DATOS: INVERSION EN I+D LATAM
-- ==============================================
-- Modelo dimensional para análisis de inversión
-- en investigación y desarrollo.
--
-- SQL Server
-- ==============================================


-- ==============================================
-- CREAR BASE DE DATOS
-- ==============================================

IF DB_ID('InversionID') IS NOT NULL
BEGIN
    ALTER DATABASE InversionID
    SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE InversionID;
END;
GO

CREATE DATABASE InversionID;
GO

USE InversionID;
GO


-- ==============================================
-- DIMENSIONES
-- ==============================================

-- DIM_TIEMPO
-- Simplificación: anio como PK (no necesita surrogate key)
CREATE TABLE dim_tiempo (
    anio INT NOT NULL,
    CONSTRAINT pk_dim_tiempo PRIMARY KEY (anio)
);
GO


-- DIM_SECTOR
-- NOTA: sector_nombre es UNIQUE.
-- La collation por defecto de SQL Server es case-insensitive,
-- por lo que 'Universidades' y 'universidades' colisionarían.
-- El ETL debe garantizar que el Excel no tenga esas variaciones.
CREATE TABLE dim_sector (
    sector_id INT PRIMARY KEY IDENTITY(1,1),
    sector_nombre NVARCHAR(100) NOT NULL UNIQUE
);
GO


-- DIM_PROVINCIA
-- NOTA: misma consideración de collation que dim_sector.
CREATE TABLE dim_provincia (
    provincia_id INT PRIMARY KEY IDENTITY(1,1),
    provincia_nombre NVARCHAR(100) NOT NULL UNIQUE
);
GO


-- DIM_DISCIPLINA
-- NOTA: misma consideración de collation que dim_sector.
CREATE TABLE dim_disciplina (
    disciplina_id INT PRIMARY KEY IDENTITY(1,1),
    disciplina_nombre NVARCHAR(150) NOT NULL UNIQUE
);
GO


-- ==============================================
-- TABLA DE HECHOS: INVERSIÓN GENERAL
-- Granularidad: 1 fila = 1 año
-- ==============================================

CREATE TABLE fact_inversion_general (
    anio INT NOT NULL,

    inversion_pesos_corrientes    BIGINT        NOT NULL,
    inversion_pesos_constantes    BIGINT        NOT NULL,
    inversion_dolares_corrientes  BIGINT        NOT NULL,
    inversion_dolares_ppp         BIGINT        NOT NULL,

    inversion_pct_pbi             DECIMAL(18,6) NOT NULL,
    inversion_publica_pct_pbi     DECIMAL(18,6) NOT NULL,
    inversion_privada_pct_pbi     DECIMAL(18,6) NOT NULL,

    CONSTRAINT pk_fact_general
        PRIMARY KEY (anio),

    CONSTRAINT fk_fact_general_anio
        FOREIGN KEY (anio)
        REFERENCES dim_tiempo(anio),

    CONSTRAINT chk_general_pesos_corrientes
        CHECK (inversion_pesos_corrientes >= 0),

    CONSTRAINT chk_general_pesos_constantes
        CHECK (inversion_pesos_constantes >= 0),

    CONSTRAINT chk_general_dolares_corrientes
        CHECK (inversion_dolares_corrientes >= 0),

    CONSTRAINT chk_general_dolares_ppp
        CHECK (inversion_dolares_ppp >= 0),

    -- NOTA: el % PBI está expresado en PORCENTAJE DIRECTO
    -- (0.62 = 0.62%), no en fracción (0.62 = 62%).
    -- El límite superior se fija en 100 como regla de negocio
    -- y coincide con la validación del ETL en Python.
    CONSTRAINT chk_general_pct_pbi
        CHECK (inversion_pct_pbi >= 0 AND inversion_pct_pbi <= 100),

    CONSTRAINT chk_general_publica_pct_pbi
        CHECK (inversion_publica_pct_pbi >= 0 AND inversion_publica_pct_pbi <= 100),

    CONSTRAINT chk_general_privada_pct_pbi
        CHECK (inversion_privada_pct_pbi >= 0 AND inversion_privada_pct_pbi <= 100)
);
GO


-- ==============================================
-- INVERSIÓN POR SECTOR
-- Granularidad: 1 fila = 1 año + 1 sector
-- ==============================================

CREATE TABLE fact_inversion_por_sector (
    anio INT NOT NULL,
    sector_id INT NOT NULL,
    inversion_pesos_corrientes BIGINT NOT NULL,

    CONSTRAINT pk_fact_sector
        PRIMARY KEY (anio, sector_id),

    CONSTRAINT fk_fact_sector_anio
        FOREIGN KEY (anio)
        REFERENCES dim_tiempo(anio),

    CONSTRAINT fk_fact_sector_sector
        FOREIGN KEY (sector_id)
        REFERENCES dim_sector(sector_id),

    CONSTRAINT chk_fact_sector_inversion
        CHECK (inversion_pesos_corrientes >= 0)
);
GO


-- ==============================================
-- INVERSIÓN POR PROVINCIA
-- Granularidad: 1 fila = 1 año + 1 provincia
-- ==============================================

CREATE TABLE fact_inversion_por_provincia (
    anio INT NOT NULL,
    provincia_id INT NOT NULL,
    inversion_pesos_corrientes BIGINT NOT NULL,

    CONSTRAINT pk_fact_provincia
        PRIMARY KEY (anio, provincia_id),

    CONSTRAINT fk_fact_provincia_anio
        FOREIGN KEY (anio)
        REFERENCES dim_tiempo(anio),

    CONSTRAINT fk_fact_provincia_provincia
        FOREIGN KEY (provincia_id)
        REFERENCES dim_provincia(provincia_id),

    CONSTRAINT chk_fact_provincia_inversion
        CHECK (inversion_pesos_corrientes >= 0)
);
GO


-- ==============================================
-- INVERSIÓN POR DISCIPLINA
-- Granularidad: 1 fila = 1 año + 1 disciplina
-- ==============================================

CREATE TABLE fact_inversion_por_disciplina (
    anio INT NOT NULL,
    disciplina_id INT NOT NULL,
    inversion_pesos_corrientes BIGINT NOT NULL,

    CONSTRAINT pk_fact_disciplina
        PRIMARY KEY (anio, disciplina_id),

    CONSTRAINT fk_fact_disciplina_anio
        FOREIGN KEY (anio)
        REFERENCES dim_tiempo(anio),

    CONSTRAINT fk_fact_disciplina_disciplina
        FOREIGN KEY (disciplina_id)
        REFERENCES dim_disciplina(disciplina_id),

    CONSTRAINT chk_fact_disciplina_inversion
        CHECK (inversion_pesos_corrientes >= 0)
);
GO


-- ==============================================
-- VISTAS ANALÍTICAS
-- ==============================================

CREATE VIEW vw_inversion_total_anio AS
SELECT
    t.anio,
    f.inversion_pesos_corrientes,
    f.inversion_pesos_constantes,
    f.inversion_dolares_corrientes,
    f.inversion_dolares_ppp,
    f.inversion_pct_pbi,
    f.inversion_publica_pct_pbi,
    f.inversion_privada_pct_pbi
FROM fact_inversion_general f
INNER JOIN dim_tiempo t ON f.anio = t.anio;
GO


CREATE VIEW vw_top_sectores_anio AS
SELECT
    t.anio,
    s.sector_nombre,
    f.inversion_pesos_corrientes,
    RANK() OVER (
        PARTITION BY t.anio
        ORDER BY f.inversion_pesos_corrientes DESC
    ) AS ranking
FROM fact_inversion_por_sector f
INNER JOIN dim_tiempo t ON f.anio = t.anio
INNER JOIN dim_sector s ON f.sector_id = s.sector_id;
GO


CREATE VIEW vw_top_provincias_anio AS
SELECT
    t.anio,
    p.provincia_nombre,
    f.inversion_pesos_corrientes,
    RANK() OVER (
        PARTITION BY t.anio
        ORDER BY f.inversion_pesos_corrientes DESC
    ) AS ranking
FROM fact_inversion_por_provincia f
INNER JOIN dim_tiempo t ON f.anio = t.anio
INNER JOIN dim_provincia p ON f.provincia_id = p.provincia_id;
GO


CREATE VIEW vw_disciplina_tendencia AS
SELECT
    t.anio,
    d.disciplina_nombre,
    f.inversion_pesos_corrientes
FROM fact_inversion_por_disciplina f
INNER JOIN dim_tiempo t ON f.anio = t.anio
INNER JOIN dim_disciplina d ON f.disciplina_id = d.disciplina_id;
GO


-- ==============================================
-- FIN
-- ==============================================

PRINT 'Base de datos InversionID creada correctamente.';
GO