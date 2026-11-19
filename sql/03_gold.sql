/* =====================================================================
   03_gold.sql  ·  SQL Server 2022 (T-SQL)
   Modelo estrella gold, tablas de pronóstico y métricas, vistas de KPI y
   el procedimiento gold.usp_build (MERGE desde silver). Idempotente.
   ===================================================================== */
USE FavoritaForecast;
GO
IF OBJECT_ID(N'gold.dim_store') IS NULL
CREATE TABLE gold.dim_store (
    store_nbr INT NOT NULL CONSTRAINT pk_dim_store PRIMARY KEY,
    city NVARCHAR(60) NOT NULL, [state] NVARCHAR(60) NOT NULL, store_type NVARCHAR(5) NOT NULL,
    cluster INT NOT NULL, is_earthquake_zone BIT NOT NULL);
IF OBJECT_ID(N'gold.dim_family') IS NULL
CREATE TABLE gold.dim_family (
    family_id INT NOT NULL CONSTRAINT pk_dim_family PRIMARY KEY,
    family NVARCHAR(60) NOT NULL CONSTRAINT uq_dim_family UNIQUE);
IF OBJECT_ID(N'gold.dim_date') IS NULL
CREATE TABLE gold.dim_date (
    [date] DATE NOT NULL CONSTRAINT pk_dim_date PRIMARY KEY,
    [year] INT NOT NULL, [month] INT NOT NULL, [day] INT NOT NULL,
    day_of_week INT NOT NULL,             -- 0 = lunes ... 6 = domingo
    week_of_year INT NOT NULL, is_weekend BIT NOT NULL, is_month_end BIT NOT NULL,
    is_payday BIT NOT NULL, days_to_payday INT NOT NULL, days_since_payday INT NOT NULL,
    is_holiday_national BIT NOT NULL, is_national_event BIT NOT NULL, is_work_day BIT NOT NULL,
    holiday_name NVARCHAR(200) NULL, oil_price FLOAT NULL);
IF OBJECT_ID(N'gold.fact_sales') IS NULL
CREATE TABLE gold.fact_sales (
    [date] DATE NOT NULL CONSTRAINT fk_fs_date REFERENCES gold.dim_date ([date]),
    store_nbr INT NOT NULL CONSTRAINT fk_fs_store REFERENCES gold.dim_store (store_nbr),
    family_id INT NOT NULL CONSTRAINT fk_fs_family REFERENCES gold.dim_family (family_id),
    sales FLOAT NOT NULL, onpromotion INT NOT NULL,
    CONSTRAINT pk_fact_sales PRIMARY KEY ([date], store_nbr, family_id));
IF OBJECT_ID(N'gold.fact_forecast') IS NULL
CREATE TABLE gold.fact_forecast (
    [date] DATE NOT NULL, store_nbr INT NOT NULL, family_id INT NOT NULL,
    model_name NVARCHAR(40) NOT NULL, model_version NVARCHAR(40) NOT NULL,
    forecast FLOAT NOT NULL, onpromotion INT NULL, created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    CONSTRAINT pk_fact_forecast PRIMARY KEY ([date], store_nbr, family_id, model_name, model_version));
IF OBJECT_ID(N'gold.fact_backtest_metrics') IS NULL
CREATE TABLE gold.fact_backtest_metrics (
    model_name NVARCHAR(40) NOT NULL, model_version NVARCHAR(40) NOT NULL, fold INT NOT NULL,
    cutoff_date DATE NOT NULL, segment NVARCHAR(60) NOT NULL,
    rmsle FLOAT NULL, wape FLOAT NULL, bias FLOAT NULL, n_rows INT NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    CONSTRAINT pk_backtest PRIMARY KEY (model_name, model_version, fold, segment));
GO

CREATE OR ALTER VIEW gold.v_store_holiday AS
SELECT d.[date], s.store_nbr, d.is_holiday_national,
       CAST(CASE WHEN EXISTS (
           SELECT 1 FROM silver.holidays h
           WHERE h.[date] = d.[date] AND h.is_day_off = 1
             AND ((h.locale = N'Local' AND h.locale_name = s.city)
               OR (h.locale = N'Regional' AND h.locale_name = s.[state]))) THEN 1 ELSE 0 END AS BIT)
           AS is_holiday_local_for_store
FROM gold.dim_date d CROSS JOIN gold.dim_store s;
GO
CREATE OR ALTER VIEW gold.v_kpi_daily AS
SELECT f.[date], d.[year], d.[month], d.day_of_week, d.is_payday, d.is_holiday_national,
       SUM(f.sales) AS sales, SUM(f.onpromotion) AS items_on_promo
FROM gold.fact_sales f JOIN gold.dim_date d ON d.[date] = f.[date]
GROUP BY f.[date], d.[year], d.[month], d.day_of_week, d.is_payday, d.is_holiday_national;
GO
CREATE OR ALTER VIEW gold.v_kpi_yearly AS
SELECT [year], sales, n_days, sales / n_days AS avg_daily_sales,
       (sales / n_days) / LAG(sales / n_days) OVER (ORDER BY [year]) - 1 AS growth_avg_daily
FROM (SELECT [year], SUM(sales) AS sales, COUNT(DISTINCT [date]) AS n_days
      FROM gold.v_kpi_daily GROUP BY [year]) y;
GO
CREATE OR ALTER VIEW gold.v_kpi_family AS
SELECT fam.family, SUM(f.sales) AS sales,
       SUM(f.sales) / SUM(SUM(f.sales)) OVER () AS share,
       AVG(CASE WHEN f.onpromotion > 0 THEN f.sales END) AS avg_sales_promo,
       AVG(CASE WHEN f.onpromotion = 0 THEN f.sales END) AS avg_sales_no_promo
FROM gold.fact_sales f JOIN gold.dim_family fam ON fam.family_id = f.family_id
GROUP BY fam.family;
GO
CREATE OR ALTER VIEW gold.v_kpi_store AS
SELECT s.store_nbr, s.city, s.[state], s.store_type, s.cluster, SUM(f.sales) AS sales
FROM gold.fact_sales f JOIN gold.dim_store s ON s.store_nbr = f.store_nbr
GROUP BY s.store_nbr, s.city, s.[state], s.store_type, s.cluster;
GO

CREATE OR ALTER PROCEDURE gold.usp_build
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    SET DATEFIRST 1;  -- lunes = 1
    BEGIN TRANSACTION;

    MERGE gold.dim_store AS t
    USING (SELECT store_nbr, city, [state], store_type, cluster,
                  CAST(CASE WHEN [state] IN (N'Manabi', N'Esmeraldas') THEN 1 ELSE 0 END AS BIT) AS eq
           FROM silver.stores) AS s
    ON t.store_nbr = s.store_nbr
    WHEN MATCHED THEN UPDATE SET city = s.city, [state] = s.[state], store_type = s.store_type,
                                 cluster = s.cluster, is_earthquake_zone = s.eq
    WHEN NOT MATCHED THEN INSERT VALUES (s.store_nbr, s.city, s.[state], s.store_type, s.cluster, s.eq);

    MERGE gold.dim_family AS t USING silver.product_families AS s ON t.family_id = s.family_id
    WHEN MATCHED THEN UPDATE SET family = s.family
    WHEN NOT MATCHED THEN INSERT VALUES (s.family_id, s.family);

    ;WITH cal AS (
        SELECT DATEADD(DAY, value, CAST('2013-01-01' AS DATE)) AS [date]
        FROM GENERATE_SERIES(0, DATEDIFF(DAY, '2013-01-01', '2017-08-31'))
    ), base AS (
        SELECT [date], EOMONTH([date]) AS eom,
               CASE WHEN DAY([date]) <= 15 THEN DATEFROMPARTS(YEAR([date]), MONTH([date]), 15) ELSE EOMONTH([date]) END AS next_pay,
               CASE WHEN DAY([date]) >= 15 THEN DATEFROMPARTS(YEAR([date]), MONTH([date]), 15) ELSE EOMONTH(DATEADD(MONTH, -1, [date])) END AS prev_pay
        FROM cal
    ), nat AS (
        SELECT [date],
               MAX(CAST(is_day_off AS INT)) AS off_, MAX(CAST(is_event AS INT)) AS ev_, MAX(CAST(is_work_day AS INT)) AS wd_,
               STRING_AGG([description], N' | ') AS names
        FROM silver.holidays WHERE locale = N'National' GROUP BY [date]
    ), src AS (
        SELECT b.[date], YEAR(b.[date]) AS y, MONTH(b.[date]) AS m, DAY(b.[date]) AS d,
               DATEPART(WEEKDAY, b.[date]) - 1 AS dow, DATEPART(ISO_WEEK, b.[date]) AS wk,
               CAST(CASE WHEN DATEPART(WEEKDAY, b.[date]) IN (6, 7) THEN 1 ELSE 0 END AS BIT) AS wkend,
               CAST(CASE WHEN b.[date] = b.eom THEN 1 ELSE 0 END AS BIT) AS me,
               CAST(CASE WHEN DAY(b.[date]) = 15 OR b.[date] = b.eom THEN 1 ELSE 0 END AS BIT) AS pay,
               DATEDIFF(DAY, b.[date], b.next_pay) AS dtp, DATEDIFF(DAY, b.prev_pay, b.[date]) AS dsp,
               CAST(ISNULL(n.off_, 0) AS BIT) AS hol, CAST(ISNULL(n.ev_, 0) AS BIT) AS ev,
               CAST(ISNULL(n.wd_, 0) AS BIT) AS wd, n.names, o.dcoilwtico
        FROM base b LEFT JOIN nat n ON n.[date] = b.[date] LEFT JOIN silver.oil_prices o ON o.[date] = b.[date]
    )
    MERGE gold.dim_date AS t USING src AS s ON t.[date] = s.[date]
    WHEN MATCHED THEN UPDATE SET is_holiday_national = s.hol, is_national_event = s.ev, is_work_day = s.wd,
                                 holiday_name = s.names, oil_price = s.dcoilwtico
    WHEN NOT MATCHED THEN INSERT VALUES (s.[date], s.y, s.m, s.d, s.dow, s.wk, s.wkend, s.me, s.pay, s.dtp, s.dsp,
                                         s.hol, s.ev, s.wd, s.names, s.dcoilwtico);

    MERGE gold.fact_sales AS t USING silver.daily_sales AS s
    ON t.[date] = s.[date] AND t.store_nbr = s.store_nbr AND t.family_id = s.family_id
    WHEN MATCHED AND (t.sales <> s.sales OR t.onpromotion <> s.onpromotion)
        THEN UPDATE SET sales = s.sales, onpromotion = s.onpromotion
    WHEN NOT MATCHED THEN INSERT VALUES (s.[date], s.store_nbr, s.family_id, s.sales, s.onpromotion);

    COMMIT;
END;
GO
