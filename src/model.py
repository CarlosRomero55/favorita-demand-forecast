"""Entrenamiento, backtest y pronóstico.

- Baselines: naive estacional (último valor observado del mismo día de la semana)
  y promedio móvil de 14 días.
- Modelo global LightGBM sobre log1p(sales) para las 1,782 series tienda–familia.
- Validación temporal: 3 cortes de 16 días al final del periodo de entrenamiento.
- Pronóstico de los 16 días de test.csv → gold.fact_forecast.

Uso: python -m src.model
"""
from __future__ import annotations

import json
import logging
import time
from datetime import datetime

import lightgbm as lgb
import numpy as np
import pandas as pd

from src import config, db, features

log = logging.getLogger("model")
MODEL_NAME = "lightgbm_global"
MODEL_VERSION = "v1"
LAST_TRAIN_DATE = pd.Timestamp("2017-08-15")

PARAMS = {
    "objective": "regression",
    "metric": "rmse",  # RMSE sobre log1p = RMSLE
    "learning_rate": 0.05,
    "num_leaves": 255,
    "min_data_in_leaf": 100,
    "feature_fraction": 0.8,
    "bagging_fraction": 0.8,
    "bagging_freq": 1,
    "lambda_l2": 1.0,
    "verbose": -1,
    "seed": config.RANDOM_STATE,
    "num_threads": 0,
}
MAX_ROUNDS = 1500


# ---------------------------------------------------------------- métricas
def rmsle(y: np.ndarray, p: np.ndarray) -> float:
    return float(np.sqrt(np.mean((np.log1p(p) - np.log1p(y)) ** 2)))


def wape(y: np.ndarray, p: np.ndarray) -> float:
    return float(np.abs(y - p).sum() / y.sum())


def bias(y: np.ndarray, p: np.ndarray) -> float:
    return float((p - y).sum() / y.sum())


def metrics(y, p) -> dict:
    y, p = np.asarray(y, float), np.asarray(p, float)
    return {"rmsle": rmsle(y, p), "wape": wape(y, p), "bias": bias(y, p), "n_rows": int(len(y))}


# ---------------------------------------------------------------- folds
def fold_windows(n_folds: int = config.N_BACKTEST_FOLDS) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    """Ventanas de validación de 16 días, de la más antigua a la más reciente."""
    ventanas = []
    for k in range(n_folds, 0, -1):
        fin = LAST_TRAIN_DATE - pd.Timedelta(days=config.HORIZON * (k - 1))
        ventanas.append((fin - pd.Timedelta(days=config.HORIZON - 1), fin))
    return ventanas


# ---------------------------------------------------------------- baselines
def baseline_seasonal_naive(df: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.Series:
    """Para cada día del horizonte, la venta del mismo día de la semana en la última semana observada."""
    cutoff = start - pd.Timedelta(days=1)
    ultima = df[(df.date > cutoff - pd.Timedelta(days=7)) & (df.date <= cutoff)]
    ref = ultima.set_index(["store_nbr", "family_id", "day_of_week"]).sales
    obj = df[(df.date >= start) & (df.date <= end)]
    idx = pd.MultiIndex.from_frame(obj[["store_nbr", "family_id", "day_of_week"]])
    return pd.Series(ref.reindex(idx).to_numpy(), index=obj.index).fillna(0)


def baseline_moving_average(df: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp, window: int = 14) -> pd.Series:
    cutoff = start - pd.Timedelta(days=1)
    hist = df[(df.date > cutoff - pd.Timedelta(days=window)) & (df.date <= cutoff) & (df.is_closed == 0)]
    ref = hist.groupby(["store_nbr", "family_id"]).sales.mean()
    obj = df[(df.date >= start) & (df.date <= end)]
    idx = pd.MultiIndex.from_frame(obj[["store_nbr", "family_id"]])
    return pd.Series(ref.reindex(idx).to_numpy(), index=obj.index).fillna(0)


# ---------------------------------------------------------------- LightGBM
def _train_rows(df: pd.DataFrame, hasta: pd.Timestamp) -> pd.DataFrame:
    return df[(df.date >= pd.Timestamp(config.TRAIN_START)) & (df.date <= hasta)
              & (df.is_closed == 0) & df.y.notna()]


def _dataset(d: pd.DataFrame, ref: lgb.Dataset | None = None) -> lgb.Dataset:
    return lgb.Dataset(d[features.FEATURES], label=d.y, categorical_feature=features.CAT_FEATURES,
                       reference=ref, free_raw_data=False)


def dead_series(df: pd.DataFrame, cutoff: pd.Timestamp, days: int = 28) -> pd.Index:
    """Series sin ventas en los últimos `days` días antes del corte: se pronostican en cero."""
    h = df[(df.date > cutoff - pd.Timedelta(days=days)) & (df.date <= cutoff)]
    s = h.groupby(["store_nbr", "family_id"]).sales.sum()
    return s[s == 0].index


def predict(model: lgb.Booster, df: pd.DataFrame, rows: pd.DataFrame, cutoff: pd.Timestamp) -> np.ndarray:
    p = np.clip(np.expm1(model.predict(rows[features.FEATURES], num_threads=0)), 0, None)
    muertas = dead_series(df, cutoff)
    mask = pd.MultiIndex.from_frame(rows[["store_nbr", "family_id"]]).isin(muertas)
    p[mask] = 0.0
    return p


def backtest(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, list[int]]:
    """Devuelve (predicciones de backtest, métricas, mejores iteraciones por corte)."""
    preds, filas, best_iters = [], [], []
    for fold, (ini, fin) in enumerate(fold_windows(), start=1):
        t0 = time.time()
        cutoff = ini - pd.Timedelta(days=1)
        # Early stopping con los 16 días previos al corte (holdout interno), nunca con la ventana evaluada
        inner_ini = cutoff - pd.Timedelta(days=config.HORIZON - 1)
        tr = _train_rows(df, inner_ini - pd.Timedelta(days=1))
        inner = _train_rows(df, cutoff)
        inner = inner[inner.date >= inner_ini]
        va = df[(df.date >= ini) & (df.date <= fin) & (df.is_closed == 0)]
        dtr = _dataset(tr)
        model = lgb.train(PARAMS, dtr, MAX_ROUNDS, valid_sets=[_dataset(inner, dtr)],
                          callbacks=[lgb.early_stopping(50, verbose=False)])
        best_iters.append(model.best_iteration)
        out = va[["date", "store_nbr", "family_id", "sales", "onpromotion"]].copy()
        out["fold"], out["cutoff_date"] = fold, cutoff
        out[MODEL_NAME] = predict(model, df, va, cutoff)
        out["seasonal_naive"] = baseline_seasonal_naive(df, ini, fin).loc[va.index].to_numpy()
        out["moving_avg_14"] = baseline_moving_average(df, ini, fin).loc[va.index].to_numpy()
        preds.append(out)
        for m in [MODEL_NAME, "seasonal_naive", "moving_avg_14"]:
            filas.append({"model_name": m, "fold": fold, "cutoff_date": cutoff.date(), "segment": "ALL",
                          **metrics(out.sales, out[m])})
        log.info("corte %d (%s a %s): %d filas train, best_iter=%d, RMSLE=%.4f, %.0fs",
                 fold, ini.date(), fin.date(), len(tr), model.best_iteration, filas[-3]["rmsle"], time.time() - t0)
    return pd.concat(preds, ignore_index=True), pd.DataFrame(filas), best_iters


def family_metrics(preds: pd.DataFrame, fam: pd.DataFrame) -> pd.DataFrame:
    p = preds.merge(fam, on="family_id")
    filas = []
    for (fold, family), g in p.groupby(["fold", "family"]):
        for m in [MODEL_NAME, "seasonal_naive", "moving_avg_14"]:
            if g.sales.sum() > 0:
                filas.append({"model_name": m, "fold": fold, "cutoff_date": g.cutoff_date.iloc[0].date(),
                              "segment": family, **metrics(g.sales, g[m])})
    return pd.DataFrame(filas)


def residual_sigma(preds: pd.DataFrame) -> pd.DataFrame:
    """Desviación estándar del error diario del backtest por serie (unidades), para el stock de seguridad."""
    e = preds.assign(err=preds.sales - preds[MODEL_NAME])
    return e.groupby(["store_nbr", "family_id"]).err.agg(sigma_daily="std", mean_error="mean").reset_index()


def train_final(df: pd.DataFrame, n_rounds: int) -> lgb.Booster:
    tr = _train_rows(df, LAST_TRAIN_DATE)
    return lgb.train(PARAMS, _dataset(tr), n_rounds)


# ---------------------------------------------------------------- persistencia
def save_to_gold(con, forecast: pd.DataFrame, metricas: pd.DataFrame) -> None:
    ahora = datetime.now()
    con.execute("DELETE FROM gold.fact_forecast WHERE model_version = ?", [MODEL_VERSION])
    f = forecast.assign(model_version=MODEL_VERSION, created_at=ahora)[
        ["date", "store_nbr", "family_id", "model_name", "model_version", "forecast", "onpromotion", "created_at"]]
    con.register("f_tmp", f)
    con.execute("INSERT INTO gold.fact_forecast SELECT * FROM f_tmp")
    con.execute("DELETE FROM gold.fact_backtest_metrics WHERE model_version = ?", [MODEL_VERSION])
    m = metricas.assign(model_version=MODEL_VERSION, created_at=ahora)[
        ["model_name", "model_version", "fold", "cutoff_date", "segment", "rmsle", "wape", "bias", "n_rows", "created_at"]]
    con.register("m_tmp", m)
    con.execute("INSERT INTO gold.fact_backtest_metrics SELECT * FROM m_tmp")


def run() -> dict:
    t0 = time.time()
    for d in (config.MODELS_DIR, config.DATA_PROCESSED, config.LOGS_DIR):
        d.mkdir(parents=True, exist_ok=True)
    with db.connect() as con:
        db.run_sql_file(con, config.SQL_DIR / "duckdb" / "03_gold.sql")
        df = features.add_features(features.load_panel(con))
        fam = con.execute("SELECT family_id, family FROM gold.dim_family").df()

        preds, met, best_iters = backtest(df)
        met_fam = family_metrics(preds, fam)
        n_rounds = int(np.mean(best_iters) * 1.05)
        log.info("entrenando modelo final con %d iteraciones", n_rounds)
        model = train_final(df, n_rounds)
        model.save_model(str(config.MODELS_DIR / f"{MODEL_NAME}_{MODEL_VERSION}.txt"))

        test = df[df.is_test == 1]
        fc = test[["date", "store_nbr", "family_id", "onpromotion"]].copy()
        fc["forecast"] = predict(model, df, test, LAST_TRAIN_DATE)
        fc["model_name"] = MODEL_NAME
        sn = test[["date", "store_nbr", "family_id", "onpromotion"]].copy()
        sn["forecast"] = baseline_seasonal_naive(df, test.date.min(), test.date.max()).loc[test.index].to_numpy()
        sn["model_name"] = "seasonal_naive"
        forecast = pd.concat([fc, sn], ignore_index=True)
        save_to_gold(con, forecast, pd.concat([met, met_fam], ignore_index=True))

        # Archivo para Kaggle (opcional)
        req = con.execute("SELECT id, date, store_nbr, family_id FROM silver.forecast_requests").df()
        req["date"] = pd.to_datetime(req.date)
        sub = req.merge(fc, on=["date", "store_nbr", "family_id"])[["id", "forecast"]].rename(columns={"forecast": "sales"})
        sub.sort_values("id").to_csv(config.ROOT / "submission.csv", index=False)

    # Artefactos para el notebook y el snapshot
    preds.to_parquet(config.DATA_PROCESSED / "backtest_predictions.parquet", index=False)
    residual_sigma(preds).to_parquet(config.DATA_PROCESSED / "residual_sigma.parquet", index=False)
    imp = pd.DataFrame({"feature": model.feature_name(),
                        "gain": model.feature_importance("gain"),
                        "split": model.feature_importance("split")})
    imp["gain_share"] = imp.gain / imp.gain.sum()
    imp.sort_values("gain", ascending=False).to_parquet(config.DATA_PROCESSED / "feature_importance.parquet", index=False)

    resumen = met[met.segment == "ALL"].groupby("model_name")[["rmsle", "wape", "bias"]].mean().round(4)
    info = {
        "model_name": MODEL_NAME, "model_version": MODEL_VERSION, "train_start": config.TRAIN_START,
        "last_train_date": str(LAST_TRAIN_DATE.date()), "best_iterations": best_iters, "final_rounds": n_rounds,
        "folds": [[str(a.date()), str(b.date())] for a, b in fold_windows()],
        "backtest_mean": resumen.to_dict(orient="index"), "n_features": len(features.FEATURES),
        "n_series": int(df[["store_nbr", "family_id"]].drop_duplicates().shape[0]),
        "n_train_rows_final": int(len(_train_rows(df, LAST_TRAIN_DATE))),
        "runtime_minutes": round((time.time() - t0) / 60, 1), "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    (config.DATA_PROCESSED / "model_info.json").write_text(json.dumps(info, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info("listo en %.1f min\n%s", info["runtime_minutes"], resumen)
    return info


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[logging.StreamHandler(),
                                  logging.FileHandler(config.LOGS_DIR / "model.log", encoding="utf-8")])
    run()
