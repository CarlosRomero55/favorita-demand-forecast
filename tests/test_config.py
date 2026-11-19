"""Pruebas básicas de configuración."""
from src import config


def test_lags_no_filtran_informacion():
    # Con horizonte de 16 días, ningún lag puede ser menor al horizonte
    assert min(config.LAGS) >= config.HORIZON


def test_archivos_esperados():
    assert set(config.RAW_FILES) == {
        "train.csv", "test.csv", "stores.csv", "oil.csv",
        "holidays_events.csv", "transactions.csv",
    }


def test_niveles_de_servicio():
    assert config.SERVICE_LEVELS[0.95] > config.SERVICE_LEVELS[0.90]
