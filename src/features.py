"""Construcción de variables para el modelo global.

Regla de oro: todo lo que mira ventas pasadas usa un desfase de al menos
HORIZON (16) días. Así, un único modelo sirve para los 16 días del horizonte
sin usar información que no existiría al momento de pronosticar.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src import config

CAT_FEATURES = ["store_nbr", "family_id", "store_type", "cluster", "city_code", "state_code"]


def load_panel(con, start: str | None = None) -> pd.DataFrame:
    """Panel diario tienda–familia: train (con ventas) + test (sin ventas), con calendario completo.

    Los 25 de diciembre no existen en los datos: se insertan con ventas 0 y
    `is_closed = 1` para que los lags por posición sean lags por fecha, y luego
    se excluyen del entrenamiento y la evaluación.
    """
    start = pd.Timestamp(start or config.TRAIN_START)
    buffer = start - pd.Timedelta(days=max(config.LAGS) + 70)
    df = con.execute(f"""
        SELECT date, store_nbr, family_id, sales, onpromotion FROM gold.fact_sales WHERE date >= DATE '{buffer.date()}'
        UNION ALL
        SELECT date, store_nbr, family_id, NULL AS sales, onpromotion FROM silver.forecast_requests""").df()
    df["date"] = pd.to_datetime(df["date"])

    fechas = pd.date_range(df.date.min(), df.date.max(), freq="D")
    series = df[["store_nbr", "family_id"]].drop_duplicates()
    grid = series.merge(pd.DataFrame({"date": fechas}), how="cross")
    df = grid.merge(df, on=["store_nbr", "family_id", "date"], how="left")
    navidad = (df.date.dt.month == 12) & (df.date.dt.day == 25)
    df["is_closed"] = navidad.astype("int8")
    df.loc[navidad, ["sales", "onpromotion"]] = 0
    df["onpromotion"] = df.onpromotion.fillna(0)
    df["is_test"] = (df.date > pd.Timestamp("2017-08-15")).astype("int8")

    cal = con.execute("""
        SELECT d.date, d.day_of_week, d.day, d.month, d.week_of_year, d.is_payday, d.days_to_payday,
               d.days_since_payday, d.is_holiday_national, d.is_national_event, d.is_work_day, d.oil_price,
               coalesce(h.add_, false) AS is_christmas_eve_period
        FROM gold.dim_date d
        LEFT JOIN (SELECT date, bool_or(holiday_type = 'Additional') AS add_ FROM silver.holidays
                   WHERE locale = 'National' GROUP BY date) h USING (date)""").df()
    cal["date"] = pd.to_datetime(cal["date"])
    df = df.merge(cal, on="date", how="left")

    loc = con.execute("SELECT date, store_nbr, is_holiday_local_for_store FROM gold.v_store_holiday").df()
    loc["date"] = pd.to_datetime(loc["date"])
    df = df.merge(loc, on=["date", "store_nbr"], how="left")

    stores = con.execute("SELECT store_nbr, city, state, store_type, cluster FROM gold.dim_store").df()
    stores["city_code"] = stores.city.astype("category").cat.codes
    stores["state_code"] = stores.state.astype("category").cat.codes
    stores["store_type"] = stores.store_type.astype("category").cat.codes
    df = df.merge(stores.drop(columns=["city", "state"]), on="store_nbr", how="left")
    return df.sort_values(["store_nbr", "family_id", "date"]).reset_index(drop=True)


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """Lags, promedios móviles y variables de promoción y calendario."""
    df = df.copy()
    df["y"] = np.log1p(df.sales)
    g = df.groupby(["store_nbr", "family_id"], sort=False)

    for lag in config.LAGS:
        df[f"lag_{lag}"] = g.y.shift(lag)
    # Mismo día de la semana: lags múltiplos de 7 a partir del horizonte
    df["lag_42"] = g.y.shift(42)
    df["dow_mean_4w"] = df[["lag_21", "lag_28", "lag_35", "lag_42"]].mean(axis=1)

    base = g.y.shift(config.HORIZON)  # último dato conocido al pronosticar
    gb = base.groupby([df.store_nbr, df.family_id], sort=False)
    for w in (7, 14, 28, 56, 112):
        df[f"roll_mean_{w}"] = gb.transform(lambda s, w=w: s.rolling(w, min_periods=1).mean())
    df["roll_std_28"] = gb.transform(lambda s: s.rolling(28, min_periods=7).std())
    df["zero_share_28"] = (base == 0).astype(float).groupby([df.store_nbr, df.family_id], sort=False).transform(
        lambda s: s.rolling(28, min_periods=1).mean())

    # Promoción: la cantidad en promoción del día se conoce de antemano (está en test.csv)
    df["promo_log"] = np.log1p(df.onpromotion)
    promo_base = g.onpromotion.shift(config.HORIZON)
    df["promo_roll_28"] = promo_base.groupby([df.store_nbr, df.family_id], sort=False).transform(
        lambda s: s.rolling(28, min_periods=1).mean())
    df["promo_vs_usual"] = df.onpromotion - df.promo_roll_28

    # Petróleo con desfase del horizonte (no conoceríamos el precio futuro)
    oil = df[["date", "oil_price"]].drop_duplicates("date").set_index("date").oil_price
    df["oil_lag16"] = df.date.map(oil.shift(config.HORIZON))

    for c in ["is_payday", "is_holiday_national", "is_national_event", "is_work_day",
              "is_christmas_eve_period", "is_holiday_local_for_store"]:
        df[c] = df[c].fillna(False).astype("int8")
    df["day_of_year"] = df.date.dt.day_of_year
    return df


FEATURES = (
    CAT_FEATURES
    + [f"lag_{lag}" for lag in config.LAGS] + ["lag_42", "dow_mean_4w"]
    + [f"roll_mean_{w}" for w in (7, 14, 28, 56, 112)] + ["roll_std_28", "zero_share_28"]
    + ["onpromotion", "promo_log", "promo_roll_28", "promo_vs_usual"]
    + ["day_of_week", "day", "month", "week_of_year", "day_of_year",
       "is_payday", "days_to_payday", "days_since_payday",
       "is_holiday_national", "is_holiday_local_for_store", "is_national_event", "is_work_day",
       "is_christmas_eve_period", "oil_lag16"]
)
