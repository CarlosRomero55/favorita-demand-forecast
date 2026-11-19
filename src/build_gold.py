"""Construye la capa gold (modelo estrella y vistas de KPI) desde silver."""
from __future__ import annotations

from src import config, db

GOLD_TABLES = ["dim_date", "dim_store", "dim_family", "fact_sales"]


def build(con) -> dict[str, int]:
    db.run_sql_file(con, config.SQL_DIR / "duckdb" / "03_gold.sql")
    db.run_sql_file(con, config.SQL_DIR / "duckdb" / "build_gold.sql")
    return {t: con.execute(f"SELECT count(*) FROM gold.{t}").fetchone()[0] for t in GOLD_TABLES}


if __name__ == "__main__":
    with db.connect() as con:
        for t, n in build(con).items():
            print(f"gold.{t}: {n:,} filas")
