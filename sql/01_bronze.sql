/* =====================================================================
   01_bronze.sql  ·  SQL Server 2022 (T-SQL)
   Tablas bronze: CSV tal cual + linaje (source_file, loaded_at, batch_id).
   La carga se intenta con BULK INSERT (procedimiento bronze.usp_load_csv);
   si el servicio de SQL Server no puede leer la ruta, se usa pandas con
   fast_executemany=True (src/load_bronze.py). Idempotente.
   ===================================================================== */
USE FavoritaForecast;
GO
IF OBJECT_ID(N'bronze.train') IS NULL
CREATE TABLE bronze.train (
    id BIGINT, [date] DATE, store_nbr INT, family NVARCHAR(60), sales FLOAT, onpromotion INT,
    source_file NVARCHAR(260), loaded_at DATETIME2 DEFAULT SYSDATETIME(), batch_id NVARCHAR(40));
IF OBJECT_ID(N'bronze.test') IS NULL
CREATE TABLE bronze.test (
    id BIGINT, [date] DATE, store_nbr INT, family NVARCHAR(60), onpromotion INT,
    source_file NVARCHAR(260), loaded_at DATETIME2 DEFAULT SYSDATETIME(), batch_id NVARCHAR(40));
IF OBJECT_ID(N'bronze.stores') IS NULL
CREATE TABLE bronze.stores (
    store_nbr INT, city NVARCHAR(60), [state] NVARCHAR(60), [type] NVARCHAR(5), cluster INT,
    source_file NVARCHAR(260), loaded_at DATETIME2 DEFAULT SYSDATETIME(), batch_id NVARCHAR(40));
IF OBJECT_ID(N'bronze.oil') IS NULL
CREATE TABLE bronze.oil (
    [date] DATE, dcoilwtico FLOAT,
    source_file NVARCHAR(260), loaded_at DATETIME2 DEFAULT SYSDATETIME(), batch_id NVARCHAR(40));
IF OBJECT_ID(N'bronze.holidays_events') IS NULL
CREATE TABLE bronze.holidays_events (
    [date] DATE, [type] NVARCHAR(20), locale NVARCHAR(20), locale_name NVARCHAR(60),
    [description] NVARCHAR(200), transferred NVARCHAR(10),
    source_file NVARCHAR(260), loaded_at DATETIME2 DEFAULT SYSDATETIME(), batch_id NVARCHAR(40));
IF OBJECT_ID(N'bronze.transactions') IS NULL
CREATE TABLE bronze.transactions (
    [date] DATE, store_nbr INT, transactions INT,
    source_file NVARCHAR(260), loaded_at DATETIME2 DEFAULT SYSDATETIME(), batch_id NVARCHAR(40));
GO

/* Carga genérica con BULK INSERT a una tabla de staging del mismo esquema.
   Ejemplo: EXEC bronze.usp_load_csv N'oil', N'D:\favorita-demand-forecast\data\raw\oil.csv', N'2026-11-19-01'; */
CREATE OR ALTER PROCEDURE bronze.usp_load_csv
    @table SYSNAME, @path NVARCHAR(400), @batch_id NVARCHAR(40)
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @file NVARCHAR(260) = RIGHT(@path, CHARINDEX(N'\', REVERSE(@path) + N'\') - 1);
    DECLARE @cols NVARCHAR(MAX) = (
        SELECT STRING_AGG(QUOTENAME(name), N',') WITHIN GROUP (ORDER BY column_id)
        FROM sys.columns WHERE object_id = OBJECT_ID(N'bronze.' + @table)
          AND name NOT IN (N'source_file', N'loaded_at', N'batch_id'));
    DECLARE @sql NVARCHAR(MAX) = N'
        DELETE FROM bronze.' + QUOTENAME(@table) + N' WHERE source_file = @file;
        SELECT TOP 0 ' + @cols + N' INTO #stg FROM bronze.' + QUOTENAME(@table) + N';
        BULK INSERT #stg FROM ''' + REPLACE(@path, N'''', N'''''') + N'''
            WITH (FORMAT = ''CSV'', FIRSTROW = 2, FIELDTERMINATOR = '','', ROWTERMINATOR = ''0x0a'', TABLOCK);
        INSERT INTO bronze.' + QUOTENAME(@table) + N' (' + @cols + N', source_file, batch_id)
        SELECT ' + @cols + N', @file, @batch_id FROM #stg;';
    EXEC sp_executesql @sql, N'@file NVARCHAR(260), @batch_id NVARCHAR(40)', @file, @batch_id;
END;
GO
