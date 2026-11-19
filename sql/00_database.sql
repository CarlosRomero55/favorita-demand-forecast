/* =====================================================================
   00_database.sql  ·  SQL Server 2022 (T-SQL)
   Crea la base FavoritaForecast y los esquemas Medallion. Idempotente.
   Uso: sqlcmd -S localhost -E -i sql/00_database.sql
   ===================================================================== */
IF DB_ID(N'FavoritaForecast') IS NULL
    CREATE DATABASE FavoritaForecast;
GO
USE FavoritaForecast;
GO
IF SCHEMA_ID(N'bronze') IS NULL EXEC (N'CREATE SCHEMA bronze');
IF SCHEMA_ID(N'silver') IS NULL EXEC (N'CREATE SCHEMA silver');
IF SCHEMA_ID(N'gold')   IS NULL EXEC (N'CREATE SCHEMA gold');
GO
