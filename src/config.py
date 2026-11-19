"""Configuración central del proyecto: rutas, motor de base de datos y parámetros.

Todo lo configurable se lee de variables de entorno (archivo .env opcional),
con valores por defecto que permiten correr el proyecto sin tocar nada.
"""
from __future__ import annotations

import os
from pathlib import Path

try:  # python-dotenv es opcional
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover
    pass

ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
MODELS_DIR = ROOT / "models"
LOGS_DIR = ROOT / "logs"
SQL_DIR = ROOT / "sql"
APP_DATA = ROOT / "app" / "data"
DOCS_DIR = ROOT / "docs"

KAGGLE_COMPETITION = "store-sales-time-series-forecasting"
KAGGLE_URL = f"https://www.kaggle.com/competitions/{KAGGLE_COMPETITION}"

# Archivos esperados del dataset y su tabla bronze destino
RAW_FILES = {
    "train.csv": "train",
    "test.csv": "test",
    "stores.csv": "stores",
    "oil.csv": "oil",
    "holidays_events.csv": "holidays_events",
    "transactions.csv": "transactions",
}

# Motor: duckdb (archivo local, por defecto) o mssql (SQL Server local)
DB_ENGINE = os.getenv("DB_ENGINE", "duckdb").lower()
DUCKDB_PATH = ROOT / os.getenv("DUCKDB_PATH", "data/processed/favorita.duckdb")
MSSQL_SERVER = os.getenv("MSSQL_SERVER", "localhost")
MSSQL_DATABASE = os.getenv("MSSQL_DATABASE", "FavoritaForecast")
MSSQL_DRIVER = os.getenv("MSSQL_DRIVER", "ODBC Driver 18 for SQL Server")

# Modelado
HORIZON = 16  # días a pronosticar (igual que test.csv)
LAGS = [16, 21, 28, 35]  # lags >= horizonte para no filtrar información
N_BACKTEST_FOLDS = 3
TRAIN_START = os.getenv("TRAIN_START", "2015-07-01")  # registro estable desde jun-2015 (ADR 0004)
SERVICE_LEVELS = {0.90: 1.2816, 0.95: 1.6449, 0.98: 2.0537}  # nivel -> z
RANDOM_STATE = 42

# Terremoto del 16-abr-2016 (descripción del dataset en Kaggle)
EARTHQUAKE_DATE = "2016-04-16"
EARTHQUAKE_PROVINCES = ["Manabi", "Esmeraldas"]
