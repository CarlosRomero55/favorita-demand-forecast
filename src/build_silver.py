"""Construye la capa silver desde bronze (tablas limpias con PK y FK)."""
from __future__ import annotations

from src import config, db

SILVER_TABLES = [
    "stores", "product_families", "daily_sales", "forecast_requests",
    "transactions", "oil_prices", "holidays",
]


def build(con) -> dict[str, int]:
    db.run_sql_file(con, config.SQL_DIR / "duckdb" / "02_silver.sql")
    db.run_sql_file(con, config.SQL_DIR / "duckdb" / "build_silver.sql")
    return {t: con.execute(f"SELECT count(*) FROM silver.{t}").fetchone()[0] for t in SILVER_TABLES}


if __name__ == "__main__":
    with db.connect() as con:
        for t, n in build(con).items():
            print(f"silver.{t}: {n:,} filas")
