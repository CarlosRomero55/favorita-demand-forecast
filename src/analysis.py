"""Cálculos del EDA reutilizables (notebook, snapshot de la app y pruebas).

Todos los "efectos" son asociaciones observadas: comparan días o filas con
y sin la condición dentro del mismo año–mes–día de semana (o tienda–familia–mes),
pero no controlan todas las causas posibles. No son efectos causales probados.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src import config


def daily_totals(con) -> pd.DataFrame:
    """Ventas totales por día con calendario (sin 1 de enero, casi todo cerrado)."""
    df = con.execute("""
        SELECT k.date, d.year, d.month, d.day_of_week, d.is_payday, d.days_since_payday,
               d.days_to_payday, d.is_national_event, d.oil_price, k.sales, k.items_on_promo,
               coalesce(h.main_, false) AS is_holiday_main, coalesce(h.add_, false) AS is_holiday_additional
        FROM gold.v_kpi_daily k
        JOIN gold.dim_date d USING (date)
        LEFT JOIN (SELECT date,
                          bool_or(holiday_type IN ('Holiday', 'Transfer', 'Bridge') AND is_day_off) AS main_,
                          bool_or(holiday_type = 'Additional') AS add_
                   FROM silver.holidays WHERE locale = 'National' GROUP BY date) h USING (date)
        WHERE NOT (d.month = 1 AND d.day = 1)
        ORDER BY k.date""").df()
    df["date"] = pd.to_datetime(df["date"])
    df["is_normal"] = ~(df.is_holiday_main | df.is_holiday_additional | df.is_national_event)
    base = df[df.is_normal].groupby(["year", "month", "day_of_week"]).sales.mean().rename("base")
    df = df.join(base, on=["year", "month", "day_of_week"])
    df["ratio"] = df.sales / df.base  # venta del día / día normal comparable
    return df


def yearly(con) -> pd.DataFrame:
    return con.execute("SELECT * FROM gold.v_kpi_yearly ORDER BY year").df()


def seasonality(daily: pd.DataFrame) -> dict[str, pd.Series]:
    """Índices de estacionalidad: 1.0 = promedio."""
    full = daily[daily.year <= 2016].copy()
    full["idx"] = full.sales / full.groupby("year").sales.transform("mean")
    d = daily.copy()
    d["idx"] = d.sales / d.groupby(["year", "month"]).sales.transform("mean")
    return {
        "month": full.groupby("month").idx.mean(),
        "dow": d.groupby("day_of_week").idx.mean(),
    }


def holiday_effects(daily: pd.DataFrame) -> pd.DataFrame:
    """Efecto % de feriados nacionales frente a días normales comparables."""
    filas = [
        ("national_holiday", daily[daily.is_holiday_main]),
        ("christmas_additional", daily[daily.is_holiday_additional & ~daily.is_holiday_main]),
        ("national_event", daily[daily.is_national_event & ~daily.is_holiday_main]),
    ]
    return pd.DataFrame([
        {"effect": n, "mean_pct": g.ratio.mean() - 1, "median_pct": g.ratio.median() - 1, "n_days": len(g)}
        for n, g in filas
    ])


def local_holiday_effect(con) -> dict:
    """Efecto de feriados locales/regionales en la tienda afectada vs sus días normales."""
    l = con.execute("""
        WITH st AS (SELECT date, store_nbr, sum(sales) AS s FROM gold.fact_sales GROUP BY ALL)
        SELECT st.*, d.year, d.month, d.day_of_week,
               v.is_holiday_local_for_store AS is_local, d.is_holiday_national AS is_nat
        FROM st JOIN gold.dim_date d USING (date)
        JOIN gold.v_store_holiday v USING (date, store_nbr)
        WHERE st.s > 0""").df()
    base = l[~l.is_local & ~l.is_nat].groupby(["store_nbr", "year", "month", "day_of_week"]).s.mean().rename("base")
    l = l.join(base, on=["store_nbr", "year", "month", "day_of_week"])
    g = l[l.is_local & ~l.is_nat]
    r = g.s / g.base
    return {"mean_pct": r.mean() - 1, "median_pct": r.median() - 1, "n_store_days": int(r.notna().sum())}


def payday_profile(daily: pd.DataFrame) -> pd.DataFrame:
    """Venta relativa según días desde el último pago (0 = día 15 o fin de mes)."""
    n = daily[daily.is_normal]
    return n.groupby("days_since_payday").ratio.agg(["mean", "count"]).reset_index()


def payday_effect(daily: pd.DataFrame, window: tuple[int, int] = (1, 3)) -> float:
    """Efecto % de los días 1–3 posteriores al pago frente al resto de días normales."""
    n = daily[daily.is_normal]
    dentro = n.days_since_payday.between(*window)
    return n[dentro].ratio.mean() / n[~dentro].ratio.mean() - 1


def promo_lift(con, desde: str = "2014-04-01") -> pd.DataFrame:
    """Lift de promoción por familia: ingenuo vs estratificado.

    - naive: venta media con promo / sin promo, mezclando tiendas y meses.
    - stratified: mediana del cociente dentro de cada tienda–familia–mes, que
      quita parte del sesgo (las promos crecieron con el tiempo y se concentran
      en tiendas grandes). Sigue siendo una asociación, no un efecto causal.
    Las promociones aparecen en los datos desde abril de 2014.
    """
    p = con.execute(f"""
        SELECT fam.family, f.store_nbr, year(date) AS y, month(date) AS m,
               f.onpromotion > 0 AS promo, avg(sales) AS s, count(*) AS n, sum(sales) AS tot
        FROM gold.fact_sales f JOIN gold.dim_family fam USING (family_id)
        WHERE date >= '{desde}' GROUP BY ALL""").df()
    naive = p.groupby(["family", "promo"])[["tot", "n"]].sum()
    naive = (naive.tot / naive.n).unstack()
    naive_lift = naive[True] / naive[False] - 1
    w = p.pivot_table(index=["family", "store_nbr", "y", "m"], columns="promo", values="s").dropna()
    w = w[(w[False] > 0) & (w[True] > 0)]
    strat = np.exp(np.log(w[True] / w[False]).groupby("family").median()) - 1
    n_cells = w.groupby("family").size()
    sales = p.groupby("family").tot.sum()
    out = pd.DataFrame({"naive_lift": naive_lift, "stratified_lift": strat, "n_cells": n_cells, "sales": sales})
    return out.dropna(subset=["stratified_lift"]).sort_values("sales", ascending=False).reset_index()


def earthquake(con, dias: int = 28) -> dict:
    """Ventas 4 semanas después del terremoto vs 4 semanas antes, zona afectada vs resto.

    Se compara con la misma ventana de 2015 para descontar la estacionalidad.
    Solo cuenta tiendas que ya vendían antes de la ventana (la tienda 52 de Manta abrió en 2017).
    """
    eq = pd.Timestamp(config.EARTHQUAKE_DATE)

    def ventana(fecha: pd.Timestamp) -> pd.DataFrame:
        pre_ini, post_fin = fecha - pd.Timedelta(days=dias), fecha + pd.Timedelta(days=dias - 1)
        return con.execute(f"""
            SELECT s.is_earthquake_zone AS zone, f.date >= DATE '{fecha.date()}' AS post, sum(sales) / {dias} AS avg_daily
            FROM gold.fact_sales f JOIN gold.dim_store s USING (store_nbr)
            WHERE f.date BETWEEN DATE '{pre_ini.date()}' AND DATE '{post_fin.date()}'
              AND f.store_nbr IN (SELECT store_nbr FROM gold.fact_sales GROUP BY 1
                                  HAVING min(CASE WHEN sales > 0 THEN date END) < DATE '{pre_ini.date()}')
            GROUP BY ALL""").df().pivot(index="zone", columns="post", values="avg_daily")

    v16, v15 = ventana(eq), ventana(eq - pd.DateOffset(years=1))
    chg16, chg15 = v16[True] / v16[False] - 1, v15[True] / v15[False] - 1
    weekly = con.execute("""
        SELECT date_trunc('week', date) AS week, s.is_earthquake_zone AS zone, sum(sales) / count(DISTINCT date) AS avg_daily
        FROM gold.fact_sales f JOIN gold.dim_store s USING (store_nbr)
        WHERE date BETWEEN '2016-02-01' AND '2016-07-31' AND store_nbr <> 52
        GROUP BY ALL ORDER BY 1""").df()
    return {
        "zone_change_2016": chg16.get(True), "rest_change_2016": chg16.get(False),
        "zone_change_2015": chg15.get(True), "rest_change_2015": chg15.get(False),
        "weekly": weekly,
    }


def oil_correlation(con) -> dict:
    m = con.execute("""
        SELECT date_trunc('month', k.date) AS month, sum(k.sales) / count(DISTINCT k.date) AS sales, avg(d.oil_price) AS oil
        FROM gold.v_kpi_daily k JOIN gold.dim_date d USING (date) GROUP BY 1 ORDER BY 1""").df()
    return {
        "monthly": m,
        "corr_level": m.sales.corr(m.oil),
        "corr_yoy": m.sales.pct_change(12).corr(m.oil.pct_change(12)),
    }
