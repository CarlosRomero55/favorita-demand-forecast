# ADR 0001 · DuckDB como motor de ejecución, con scripts T-SQL equivalentes

- **Fecha:** 2026-11-19
- **Estado:** aceptado

## Contexto
El diseño original usa SQL Server 2022 local con autenticación de Windows. El proyecto se construyó en un entorno Linux en la nube donde no se puede instalar SQL Server (el registro de imágenes de Microsoft no es accesible).

## Decisión
- El pipeline se ejecuta sobre **DuckDB** (un archivo `data/processed/favorita.duckdb`), con la misma arquitectura Medallion: esquemas `bronze`, `silver` y `gold`, los mismos nombres de tablas y las mismas reglas.
- El SQL que ejecuta el pipeline vive en `sql/duckdb/`.
- `sql/00_database.sql` a `sql/03_gold.sql` contienen la versión **T-SQL** para SQL Server (idempotente, con `CREATE OR ALTER`, `IF NOT EXISTS` y `MERGE`), lista para `sqlcmd -i`. Esos scripts no se ejecutaron en este entorno.
- `src/db.py` deja preparada la conexión `mssql+pyodbc` con `Trusted_Connection=yes;TrustServerCertificate=yes`.

## Consecuencias
- Cualquiera puede clonar y correr el proyecto sin instalar un servidor.
- La carga hacia bronze usa `read_csv` de DuckDB (equivalente a `BULK INSERT`).
- Para migrar a SQL Server: `sqlcmd -S localhost -E -i sql/00_database.sql` (y 01–03), cargar bronze con pandas `fast_executemany=True`, y ejecutar `EXEC silver.usp_build; EXEC gold.usp_build;`.
