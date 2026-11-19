"""Pipeline bronze → silver → gold sobre un mini-dataset sintético (rápido, sin los CSV reales)."""
from datetime import date, timedelta

import duckdb
import pandas as pd
import pytest

from src import build_gold, build_silver, config, load_bronze, quality


@pytest.fixture()
def mini_raw(tmp_path, monkeypatch):
    raw = tmp_path / "raw"
    raw.mkdir()
    dias = [date(2017, 7, 1) + timedelta(days=i) for i in range(20)]
    train = pd.DataFrame(
        [(d, s, f, float(i % 7), i % 2) for i, (d, s, f) in enumerate(
            (d, s, f) for d in dias for s in (1, 2) for f in ("BREAD", "DAIRY"))],
        columns=["date", "store_nbr", "family", "sales", "onpromotion"],
    )
    train.insert(0, "id", range(len(train)))
    train.to_csv(raw / "train.csv", index=False)
    test = train.head(4).drop(columns="sales").assign(id=range(1000, 1004), date=date(2017, 8, 16))
    test.to_csv(raw / "test.csv", index=False)
    pd.DataFrame({"store_nbr": [1, 2], "city": ["Quito", "Manta"], "state": ["Pichincha", "Manabi"],
                  "type": ["D", "A"], "cluster": [13, 5]}).to_csv(raw / "stores.csv", index=False)
    pd.DataFrame({"date": ["2013-01-01", "2013-01-02", "2017-07-03"], "dcoilwtico": [None, 93.1, 46.0]}).to_csv(
        raw / "oil.csv", index=False)
    pd.DataFrame({"date": ["2017-07-03", "2017-07-05", "2017-07-04"], "type": ["Holiday", "Transfer", "Holiday"],
                  "locale": ["National", "National", "Local"], "locale_name": ["Ecuador", "Ecuador", "Manta"],
                  "description": ["X", "Traslado X", "Fundacion de Manta"],
                  "transferred": [True, False, False]}).to_csv(raw / "holidays_events.csv", index=False)
    pd.DataFrame({"date": dias, "store_nbr": 1, "transactions": 100}).to_csv(raw / "transactions.csv", index=False)
    monkeypatch.setattr(config, "DATA_RAW", raw)
    return raw


def _run(con):
    conteos = load_bronze.load(con)
    conteos |= build_silver.build(con)
    conteos |= build_gold.build(con)
    return conteos


def test_pipeline_idempotente_y_reglas(mini_raw):
    con = duckdb.connect()
    primera, segunda = _run(con), _run(con)
    assert primera == segunda  # no se duplican filas
    assert primera["daily_sales"] == 80
    assert all(c.ok for c in quality.run_checks(con))

    # Traslado: el feriado trasladado no es libre; el día de Transfer sí
    off = dict(con.execute("SELECT date, is_holiday_national FROM gold.dim_date "
                           "WHERE date IN ('2017-07-03','2017-07-05')").fetchall())
    assert off[date(2017, 7, 3)] is False and off[date(2017, 7, 5)] is True

    # Feriado local solo aplica a la tienda de esa ciudad
    loc = dict(con.execute("SELECT store_nbr, is_holiday_local_for_store FROM gold.v_store_holiday "
                           "WHERE date = '2017-07-04'").fetchall())
    assert loc == {1: False, 2: True}

    # Petróleo: back-fill del primer día y marca de imputado
    oil = con.execute("SELECT dcoilwtico, is_imputed FROM silver.oil_prices WHERE date = '2013-01-01'").fetchone()
    assert oil == (93.1, True)

    # Quincena
    pay = dict(con.execute("SELECT date, is_payday FROM gold.dim_date "
                           "WHERE date IN ('2017-07-15','2017-07-31','2017-07-16')").fetchall())
    assert pay == {date(2017, 7, 15): True, date(2017, 7, 31): True, date(2017, 7, 16): False}
    dtp = con.execute("SELECT days_to_payday FROM gold.dim_date WHERE date = '2017-07-10'").fetchone()[0]
    assert dtp == 5
