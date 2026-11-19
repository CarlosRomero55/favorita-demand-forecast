"""Exporta a app/data/*.parquet los resúmenes que necesita la app de Streamlit.

La app no se conecta a la base ni usa LightGBM: lee solo estos archivos agregados
(cada uno < 5 MB), así se puede publicar gratis en Streamlit Community Cloud.

Uso: python -m src.export_snapshot
"""
from __future__ import annotations

import json
from datetime import datetime

import pandas as pd

from src import analysis, config, db

MAX_MB = 5.0


def _save(df: pd.DataFrame, name: str) -> float:
    path = config.APP_DATA / f"{name}.parquet"
    df.to_parquet(path, index=False, compression="zstd")
    mb = path.stat().st_size / 1e6
    if mb >= MAX_MB:
        raise ValueError(f"{name}.parquet pesa {mb:.1f} MB (límite {MAX_MB} MB)")
    return mb


def export() -> dict[str, float]:
    config.APP_DATA.mkdir(parents=True, exist_ok=True)
    sizes: dict[str, float] = {}
    with db.connect() as con:
        # 1) Ventas diarias por tienda–familia desde 2016 (tipos compactos)
        d = con.execute("""
            SELECT date, store_nbr, family_id, sales, onpromotion FROM gold.fact_sales
            WHERE date >= '2016-01-01' ORDER BY store_nbr, family_id, date""").df()
        d = d.astype({"store_nbr": "int8", "family_id": "int8", "sales": "float32", "onpromotion": "int16"})
        sizes["sales_daily"] = _save(d, "sales_daily")

        # 2) Dimensiones
        sizes["stores"] = _save(con.execute("SELECT * FROM gold.dim_store ORDER BY store_nbr").df(), "stores")
        sizes["families"] = _save(con.execute("SELECT * FROM gold.dim_family ORDER BY family_id").df(), "families")

        # 3) Agregados por provincia y totales diarios
        prov = con.execute("""
            SELECT f.date, s.state, sum(f.sales) AS sales FROM gold.fact_sales f
            JOIN gold.dim_store s USING (store_nbr) GROUP BY ALL ORDER BY 1, 2""").df()
        sizes["sales_province_daily"] = _save(prov, "sales_province_daily")
        daily = analysis.daily_totals(con)
        estables = analysis.stable_families(con)
        daily_st = analysis.daily_totals(con, estables)
        sizes["sales_stable_daily"] = _save(daily_st[["date", "sales"]], "sales_stable_daily")
        sizes["sales_total_daily"] = _save(
            daily[["date", "year", "month", "day_of_week", "sales", "ratio", "is_holiday_main",
                   "is_holiday_additional", "is_national_event", "days_since_payday", "items_on_promo"]],
            "sales_total_daily")

        # 4) Pronósticos con σ del error de backtest por serie
        fc = con.execute("""
            SELECT date, store_nbr, family_id, model_name, forecast, onpromotion FROM gold.fact_forecast
            WHERE model_version = 'v1'""").df()
        sig = pd.read_parquet(config.DATA_PROCESSED / "residual_sigma.parquet")
        fc = fc.merge(sig, on=["store_nbr", "family_id"], how="left")
        sizes["forecasts"] = _save(fc, "forecasts")

        # 5) Métricas de backtest y real vs. pronóstico agregado
        sizes["backtest_metrics"] = _save(
            con.execute("SELECT * EXCLUDE (created_at) FROM gold.fact_backtest_metrics").df(), "backtest_metrics")
        bt = pd.read_parquet(config.DATA_PROCESSED / "backtest_predictions.parquet")
        sizes["backtest_daily"] = _save(
            bt.groupby(["date", "fold"])[["sales", "lightgbm_global", "seasonal_naive", "moving_avg_14"]].sum().reset_index(),
            "backtest_daily")
        sizes["feature_importance"] = _save(pd.read_parquet(config.DATA_PROCESSED / "feature_importance.parquet"),
                                            "feature_importance")

        # 6) Efectos estimados (asociaciones observadas)
        s = analysis.seasonality(daily)
        s["month"] = analysis.seasonality(daily_st)["month"]  # entre meses: solo familias estables (ADR 0004)
        sizes["effect_seasonality"] = _save(pd.concat([
            pd.DataFrame({"kind": "month", "key": s["month"].index, "index": s["month"].values}),
            pd.DataFrame({"kind": "dow", "key": s["dow"].index, "index": s["dow"].values})]), "effect_seasonality")
        hol = analysis.holiday_effects(daily)
        loc = analysis.local_holiday_effect(con)
        hol = pd.concat([hol, pd.DataFrame([{"effect": "local_holiday", "mean_pct": loc["mean_pct"],
                                             "median_pct": loc["median_pct"], "n_days": loc["n_store_days"]}])])
        sizes["effect_holidays"] = _save(hol, "effect_holidays")
        sizes["effect_payday"] = _save(analysis.payday_profile(daily), "effect_payday")
        promo = analysis.promo_lift(con)
        sizes["effect_promo"] = _save(promo, "effect_promo")
        eq = analysis.earthquake(con)
        sizes["effect_earthquake"] = _save(eq["weekly"], "effect_earthquake")
        oil = analysis.oil_correlation(con)
        sizes["oil_monthly"] = _save(oil["monthly"], "oil_monthly")
        yearly = analysis.yearly(con)
        sizes["kpi_yearly"] = _save(yearly, "kpi_yearly")
        comparable = analysis.yearly_comparable(daily_st).set_index("year")
        sizes["kpi_family"] = _save(con.execute("SELECT * FROM gold.v_kpi_family ORDER BY sales DESC").df(), "kpi_family")
        sizes["kpi_store"] = _save(con.execute("SELECT * FROM gold.v_kpi_store ORDER BY sales DESC").df(), "kpi_store")

        n_rows_gold, min_date, max_date = con.execute(
            "SELECT count(*), min(date), max(date) FROM gold.fact_sales").fetchone()

    info = json.loads((config.DATA_PROCESSED / "model_info.json").read_text(encoding="utf-8"))
    met = info["backtest_mean"]
    peso = float((promo.stratified_lift * promo.sales).sum() / promo.sales.sum())
    meta = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source": {"name": "Store Sales - Time Series Forecasting (Kaggle)", "url": config.KAGGLE_URL,
                   "rules_url": f"{config.KAGGLE_URL}/rules",
                   "citation": "Alexis Cook, DanB, inversion, Ryan Holbrook. (2021). Store Sales - Time Series Forecasting. Kaggle."},
        "period": {"start": str(min_date), "end": str(max_date),
                   "forecast_start": "2017-08-16", "forecast_end": "2017-08-31"},
        "counts": {"stores": 54, "families": 33, "series": info["n_series"], "gold_fact_sales_rows": int(n_rows_gold)},
        "kpis": {
            "total_sales": float(yearly.sales.sum()),
            "avg_daily_sales_2017": float(yearly.set_index("year").loc[2017, "avg_daily_sales"]),
            "growth_2017_comparable": float(comparable.loc[2017, "growth"]),
            "growth_2016_comparable": float(comparable.loc[2016, "growth"]),
            "stable_families": len(estables),
            "stable_share": float(daily_st.sales.sum() / daily.sales.sum()),
            "national_holiday_median_pct": float(hol.set_index("effect").loc["national_holiday", "median_pct"]),
            "christmas_eve_median_pct": float(hol.set_index("effect").loc["christmas_additional", "median_pct"]),
            "local_holiday_median_pct": float(loc["median_pct"]),
            "payday_post_1_3_pct": float(analysis.payday_effect(daily)),
            "promo_lift_weighted_stratified": peso,
            "earthquake_zone_change": float(eq["zone_change_2016"]),
            "earthquake_rest_change": float(eq["rest_change_2016"]),
            "earthquake_zone_change_2015": float(eq["zone_change_2015"]),
            "earthquake_rest_change_2015": float(eq["rest_change_2015"]),
            "oil_corr_level": float(oil["corr_level"]), "oil_corr_yoy": float(oil["corr_yoy"]),
            "sunday_index": float(s["dow"].loc[6]), "december_index": float(s["month"].loc[12]),
        },
        "model": {"name": info["model_name"], "version": info["model_version"], "folds": info["folds"],
                  "rmsle": met["lightgbm_global"]["rmsle"], "wape": met["lightgbm_global"]["wape"],
                  "bias": met["lightgbm_global"]["bias"],
                  "baseline_rmsle": met["seasonal_naive"]["rmsle"], "baseline_wape": met["seasonal_naive"]["wape"],
                  "ma14_rmsle": met["moving_avg_14"]["rmsle"], "ma14_wape": met["moving_avg_14"]["wape"]},
        "files_mb": {k: round(v, 3) for k, v in sizes.items()},
    }
    (config.APP_DATA / "metadata.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    return sizes


if __name__ == "__main__":
    for k, v in export().items():
        print(f"{k:24s} {v:6.2f} MB")
