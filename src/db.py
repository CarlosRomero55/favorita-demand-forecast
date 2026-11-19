"""Acceso a la base de datos.

Por defecto usa DuckDB (un archivo local, sin servidor). Con DB_ENGINE=mssql
se conecta a SQL Server local con autenticación de Windows mediante SQLAlchemy.
Ver docs/adr/0001-duckdb-en-lugar-de-sql-server.md.
"""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

import pandas as pd

from src import config


def _duckdb_connect(path: Path | None = None):
    import duckdb

    path = path or config.DUCKDB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(path))


def mssql_engine():
    """Engine de SQLAlchemy para SQL Server (Trusted_Connection, sin contraseñas)."""
    from urllib.parse import quote_plus

    from sqlalchemy import create_engine

    odbc = (
        f"DRIVER={{{config.MSSQL_DRIVER}}};SERVER={config.MSSQL_SERVER};"
        f"DATABASE={config.MSSQL_DATABASE};Trusted_Connection=yes;TrustServerCertificate=yes"
    )
    return create_engine(
        f"mssql+pyodbc:///?odbc_connect={quote_plus(odbc)}", fast_executemany=True
    )


@contextmanager
def connect(path: Path | None = None):
    """Conexión DuckDB que se cierra sola al salir del bloque."""
    if config.DB_ENGINE != "duckdb":
        raise RuntimeError(
            "connect() es para DuckDB. Con SQL Server usa mssql_engine() y los scripts de sql/."
        )
    con = _duckdb_connect(path)
    try:
        yield con
    finally:
        con.close()


def query(sql: str, path: Path | None = None) -> pd.DataFrame:
    """Ejecuta una consulta y devuelve un DataFrame."""
    with connect(path) as con:
        return con.sql(sql).df()


def run_sql_file(con, file: Path) -> None:
    """Ejecuta un script .sql completo (varias sentencias separadas por ';')."""
    con.execute(file.read_text(encoding="utf-8"))
