"""Pruebas de métricas, ventanas de validación, baselines, variables sin fuga e inventario."""
import math

import numpy as np
import pandas as pd
import pytest

from src import config, features, inventory, model


def test_metricas_basicas():
    y = np.array([10.0, 0.0, 5.0])
    assert model.rmsle(y, y) == 0
    assert model.wape(np.array([10.0, 10.0]), np.array([12.0, 8.0])) == pytest.approx(0.2)
    assert model.bias(np.array([10.0, 10.0]), np.array([11.0, 11.0])) == pytest.approx(0.1)


def test_ventanas_de_backtest():
    v = model.fold_windows()
    assert len(v) == config.N_BACKTEST_FOLDS
    assert v[-1][1] == model.LAST_TRAIN_DATE
    for ini, fin in v:
        assert (fin - ini).days + 1 == config.HORIZON
    # sin solapamiento y consecutivas
    for (a_ini, a_fin), (b_ini, _) in zip(v, v[1:]):
        assert b_ini == a_fin + pd.Timedelta(days=1)


def _panel_sintetico(n_dias=120):
    fechas = pd.date_range("2017-01-01", periods=n_dias, freq="D")
    df = pd.DataFrame({"date": fechas, "store_nbr": 1, "family_id": 1,
                       "sales": np.arange(n_dias, dtype=float), "onpromotion": 0})
    df["is_closed"], df["oil_price"] = 0, 50.0
    df["day_of_week"] = df.date.dt.day_of_week
    for c in ["is_payday", "is_holiday_national", "is_national_event", "is_work_day",
              "is_christmas_eve_period", "is_holiday_local_for_store"]:
        df[c] = False
    return df


def test_lags_no_usan_informacion_del_horizonte():
    df = features.add_features(_panel_sintetico())
    fila = df.iloc[100]  # la venta del día t-16 es 84
    assert np.expm1(fila.lag_16) == pytest.approx(84)
    # el promedio móvil de 7 días termina en t-16: ventas 78..84
    assert fila.roll_mean_7 == pytest.approx(np.log1p(np.arange(78, 85)).mean())


def test_baseline_naive_estacional():
    df = _panel_sintetico()
    ini, fin = pd.Timestamp("2017-04-01"), pd.Timestamp("2017-04-16")
    p = model.baseline_seasonal_naive(df, ini, fin)
    obj = df[(df.date >= ini) & (df.date <= fin)]
    corte = ini - pd.Timedelta(days=1)
    # cada día recibe la venta del mismo día de semana en la última semana antes del corte
    for i, row in obj.iterrows():
        ref = df[(df.date <= corte) & (df.date > corte - pd.Timedelta(days=7)) & (df.day_of_week == row.day_of_week)]
        assert p.loc[i] == ref.sales.iloc[0]


def test_inventario():
    assert inventory.safety_stock(10, 4, 0.95) == pytest.approx(1.6449 * 10 * 2)
    assert inventory.target_stock(100, 10, 4, 0.90) == pytest.approx(100 + 1.2816 * 20)
    assert inventory.safety_stock(float("nan"), 7, 0.98) == 0
    assert inventory.safety_stock(5, 7, 0.98) > inventory.safety_stock(5, 7, 0.95)
    with pytest.raises(ValueError):
        inventory.z_for(0.5)
    assert math.isclose(inventory.z_for(0.95), 1.6449)
