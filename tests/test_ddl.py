"""El DDL de DuckDB se ejecuta sin errores y es idempotente (se puede correr dos veces)."""
import duckdb

from src import config

DDL = ["00_schemas.sql", "01_bronze.sql", "02_silver.sql", "03_gold.sql"]


def _apply(con):
    for f in DDL:
        con.execute((config.SQL_DIR / "duckdb" / f).read_text(encoding="utf-8"))


def test_ddl_idempotente():
    con = duckdb.connect()
    _apply(con)
    _apply(con)  # segunda vez no debe fallar
    tablas = {
        f"{s}.{t}"
        for s, t in con.sql(
            "select table_schema, table_name from information_schema.tables"
        ).fetchall()
    }
    for esperado in [
        "bronze.train", "silver.daily_sales", "silver.holidays", "silver.oil_prices",
        "gold.fact_sales", "gold.dim_date", "gold.fact_forecast", "gold.fact_backtest_metrics",
        "gold.v_store_holiday", "gold.v_kpi_yearly",
    ]:
        assert esperado in tablas


def test_tsql_existe_para_sql_server():
    for f in ["00_database.sql", "01_bronze.sql", "02_silver.sql", "03_gold.sql"]:
        txt = (config.SQL_DIR / f).read_text(encoding="utf-8")
        assert "FavoritaForecast" in txt or "CREATE" in txt
