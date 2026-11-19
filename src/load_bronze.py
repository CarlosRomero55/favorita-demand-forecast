"""Carga los CSV de data/raw a las tablas bronze, tal cual, con linaje.

Idempotente: antes de insertar borra las filas que vinieron del mismo archivo,
así que correrlo dos veces deja el mismo número de filas.
En DuckDB se usa read_csv (equivalente a BULK INSERT). Con SQL Server se
usaría bronze.usp_load_csv o pandas con fast_executemany=True (ver ADR 0001).
"""
from __future__ import annotations

import uuid
from datetime import datetime

from src import config, db

# Tipos explícitos para que bronze no dependa de la inferencia
COLUMNS = {
    "train": "{'id':'BIGINT','date':'DATE','store_nbr':'INTEGER','family':'VARCHAR','sales':'DOUBLE','onpromotion':'INTEGER'}",
    "test": "{'id':'BIGINT','date':'DATE','store_nbr':'INTEGER','family':'VARCHAR','onpromotion':'INTEGER'}",
    "stores": "{'store_nbr':'INTEGER','city':'VARCHAR','state':'VARCHAR','type':'VARCHAR','cluster':'INTEGER'}",
    "oil": "{'date':'DATE','dcoilwtico':'DOUBLE'}",
    "holidays_events": "{'date':'DATE','type':'VARCHAR','locale':'VARCHAR','locale_name':'VARCHAR','description':'VARCHAR','transferred':'BOOLEAN'}",
    "transactions": "{'date':'DATE','store_nbr':'INTEGER','transactions':'INTEGER'}",
}


def load(con) -> dict[str, int]:
    batch_id = datetime.now().strftime("%Y%m%d%H%M%S") + "-" + uuid.uuid4().hex[:6]
    for f in ["00_schemas.sql", "01_bronze.sql"]:
        db.run_sql_file(con, config.SQL_DIR / "duckdb" / f)

    conteos = {}
    for archivo, tabla in config.RAW_FILES.items():
        ruta = (config.DATA_RAW / archivo).as_posix()
        con.execute("BEGIN")
        con.execute(f"DELETE FROM bronze.{tabla} WHERE source_file = ?", [archivo])
        con.execute(
            f"""INSERT INTO bronze.{tabla}
                SELECT *, ? AS source_file, current_localtimestamp() AS loaded_at, ? AS batch_id
                FROM read_csv('{ruta}', header = true, columns = {COLUMNS[tabla]})""",
            [archivo, batch_id],
        )
        con.execute("COMMIT")
        conteos[tabla] = con.execute(f"SELECT count(*) FROM bronze.{tabla}").fetchone()[0]
    return conteos


if __name__ == "__main__":
    with db.connect() as con:
        for t, n in load(con).items():
            print(f"bronze.{t}: {n:,} filas")
