/* =====================================================================
   02_silver.sql  ·  SQL Server 2022 (T-SQL)
   Tablas silver con PK/FK y el procedimiento silver.usp_build, que las
   llena desde bronze con MERGE (idempotente). Requiere SQL Server 2022
   por GENERATE_SERIES y LAST_VALUE ... IGNORE NULLS.
   ===================================================================== */
USE FavoritaForecast;
GO
IF OBJECT_ID(N'silver.stores') IS NULL
CREATE TABLE silver.stores (
    store_nbr INT NOT NULL CONSTRAINT pk_silver_stores PRIMARY KEY,
    city NVARCHAR(60) NOT NULL, [state] NVARCHAR(60) NOT NULL,
    store_type NVARCHAR(5) NOT NULL, cluster INT NOT NULL);
IF OBJECT_ID(N'silver.product_families') IS NULL
CREATE TABLE silver.product_families (
    family_id INT NOT NULL CONSTRAINT pk_silver_families PRIMARY KEY,
    family NVARCHAR(60) NOT NULL CONSTRAINT uq_silver_family UNIQUE);
IF OBJECT_ID(N'silver.daily_sales') IS NULL
CREATE TABLE silver.daily_sales (
    [date] DATE NOT NULL,
    store_nbr INT NOT NULL CONSTRAINT fk_sales_store REFERENCES silver.stores (store_nbr),
    family_id INT NOT NULL CONSTRAINT fk_sales_family REFERENCES silver.product_families (family_id),
    sales FLOAT NOT NULL CONSTRAINT ck_sales_nonneg CHECK (sales >= 0),
    onpromotion INT NOT NULL,
    CONSTRAINT pk_silver_daily_sales PRIMARY KEY ([date], store_nbr, family_id));
IF OBJECT_ID(N'silver.forecast_requests') IS NULL
CREATE TABLE silver.forecast_requests (
    id BIGINT NOT NULL CONSTRAINT pk_silver_requests PRIMARY KEY,
    [date] DATE NOT NULL,
    store_nbr INT NOT NULL CONSTRAINT fk_req_store REFERENCES silver.stores (store_nbr),
    family_id INT NOT NULL CONSTRAINT fk_req_family REFERENCES silver.product_families (family_id),
    onpromotion INT NOT NULL);
IF OBJECT_ID(N'silver.transactions') IS NULL
CREATE TABLE silver.transactions (
    [date] DATE NOT NULL,
    store_nbr INT NOT NULL CONSTRAINT fk_tx_store REFERENCES silver.stores (store_nbr),
    transactions INT NOT NULL,
    CONSTRAINT pk_silver_transactions PRIMARY KEY ([date], store_nbr));
IF OBJECT_ID(N'silver.oil_prices') IS NULL
CREATE TABLE silver.oil_prices (
    [date] DATE NOT NULL CONSTRAINT pk_silver_oil PRIMARY KEY,
    dcoilwtico FLOAT NOT NULL, is_imputed BIT NOT NULL);
IF OBJECT_ID(N'silver.holidays') IS NULL
CREATE TABLE silver.holidays (
    holiday_id INT NOT NULL CONSTRAINT pk_silver_holidays PRIMARY KEY,
    [date] DATE NOT NULL, holiday_type NVARCHAR(20) NOT NULL, locale NVARCHAR(20) NOT NULL,
    locale_name NVARCHAR(60) NOT NULL, [description] NVARCHAR(200) NOT NULL,
    transferred BIT NOT NULL, is_day_off BIT NOT NULL, is_work_day BIT NOT NULL, is_event BIT NOT NULL);
GO

CREATE OR ALTER PROCEDURE silver.usp_build
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    BEGIN TRANSACTION;

    MERGE silver.stores AS t
    USING (SELECT DISTINCT store_nbr, TRIM(city) AS city, TRIM([state]) AS [state], TRIM([type]) AS store_type, cluster
           FROM bronze.stores) AS s
    ON t.store_nbr = s.store_nbr
    WHEN MATCHED THEN UPDATE SET city = s.city, [state] = s.[state], store_type = s.store_type, cluster = s.cluster
    WHEN NOT MATCHED THEN INSERT VALUES (s.store_nbr, s.city, s.[state], s.store_type, s.cluster);

    MERGE silver.product_families AS t
    USING (SELECT ROW_NUMBER() OVER (ORDER BY family) AS family_id, family
           FROM (SELECT DISTINCT TRIM(family) AS family FROM bronze.train
                 UNION SELECT DISTINCT TRIM(family) FROM bronze.test) f) AS s
    ON t.family = s.family
    WHEN NOT MATCHED THEN INSERT (family_id, family) VALUES (s.family_id, s.family);

    MERGE silver.daily_sales AS t
    USING (SELECT b.[date], b.store_nbr, f.family_id, b.sales, b.onpromotion
           FROM bronze.train b JOIN silver.product_families f ON f.family = TRIM(b.family)) AS s
    ON t.[date] = s.[date] AND t.store_nbr = s.store_nbr AND t.family_id = s.family_id
    WHEN MATCHED AND (t.sales <> s.sales OR t.onpromotion <> s.onpromotion)
        THEN UPDATE SET sales = s.sales, onpromotion = s.onpromotion
    WHEN NOT MATCHED THEN INSERT VALUES (s.[date], s.store_nbr, s.family_id, s.sales, s.onpromotion);

    MERGE silver.forecast_requests AS t
    USING (SELECT b.id, b.[date], b.store_nbr, f.family_id, b.onpromotion
           FROM bronze.test b JOIN silver.product_families f ON f.family = TRIM(b.family)) AS s
    ON t.id = s.id
    WHEN NOT MATCHED THEN INSERT VALUES (s.id, s.[date], s.store_nbr, s.family_id, s.onpromotion);

    MERGE silver.transactions AS t
    USING (SELECT [date], store_nbr, MAX(transactions) AS transactions FROM bronze.transactions GROUP BY [date], store_nbr) AS s
    ON t.[date] = s.[date] AND t.store_nbr = s.store_nbr
    WHEN MATCHED THEN UPDATE SET transactions = s.transactions
    WHEN NOT MATCHED THEN INSERT VALUES (s.[date], s.store_nbr, s.transactions);

    -- Petróleo: calendario completo con forward-fill (y back-fill del primer día)
    ;WITH cal AS (
        SELECT DATEADD(DAY, value, CAST('2013-01-01' AS DATE)) AS [date]
        FROM GENERATE_SERIES(0, DATEDIFF(DAY, '2013-01-01', '2017-08-31'))
    ), j AS (
        SELECT c.[date], o.dcoilwtico,
               LAST_VALUE(o.dcoilwtico) IGNORE NULLS OVER (ORDER BY c.[date] ROWS UNBOUNDED PRECEDING) AS ffill
        FROM cal c LEFT JOIN bronze.oil o ON o.[date] = c.[date]
    ), src AS (
        SELECT [date],
               COALESCE(ffill, FIRST_VALUE(ffill) IGNORE NULLS OVER (ORDER BY [date] ROWS BETWEEN CURRENT ROW AND UNBOUNDED FOLLOWING)) AS dcoilwtico,
               CAST(CASE WHEN dcoilwtico IS NULL THEN 1 ELSE 0 END AS BIT) AS is_imputed
        FROM j
    )
    MERGE silver.oil_prices AS t USING src AS s ON t.[date] = s.[date]
    WHEN MATCHED THEN UPDATE SET dcoilwtico = s.dcoilwtico, is_imputed = s.is_imputed
    WHEN NOT MATCHED THEN INSERT VALUES (s.[date], s.dcoilwtico, s.is_imputed);

    -- Feriados: aplica traslados, puentes y días de recuperación
    MERGE silver.holidays AS t
    USING (SELECT ROW_NUMBER() OVER (ORDER BY [date], locale, locale_name, [description]) AS holiday_id,
                  [date], [type] AS holiday_type, locale, locale_name, [description],
                  CAST(CASE WHEN transferred IN (N'True', N'1') THEN 1 ELSE 0 END AS BIT) AS transferred,
                  CAST(CASE WHEN [type] = N'Holiday' AND transferred NOT IN (N'True', N'1') THEN 1
                            WHEN [type] IN (N'Transfer', N'Bridge', N'Additional') THEN 1 ELSE 0 END AS BIT) AS is_day_off,
                  CAST(CASE WHEN [type] = N'Work Day' THEN 1 ELSE 0 END AS BIT) AS is_work_day,
                  CAST(CASE WHEN [type] = N'Event' THEN 1 ELSE 0 END AS BIT) AS is_event
           FROM bronze.holidays_events) AS s
    ON t.holiday_id = s.holiday_id
    WHEN MATCHED THEN UPDATE SET [date] = s.[date], holiday_type = s.holiday_type, locale = s.locale,
        locale_name = s.locale_name, [description] = s.[description], transferred = s.transferred,
        is_day_off = s.is_day_off, is_work_day = s.is_work_day, is_event = s.is_event
    WHEN NOT MATCHED THEN INSERT VALUES (s.holiday_id, s.[date], s.holiday_type, s.locale, s.locale_name,
        s.[description], s.transferred, s.is_day_off, s.is_work_day, s.is_event);

    COMMIT;
END;
GO
