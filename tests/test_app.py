"""Todas las páginas de la app cargan sin errores, en español y en inglés."""
import pytest
from streamlit.testing.v1 import AppTest

from src import config

MAIN = str(config.ROOT / "app" / "streamlit_app.py")
PAGES = ["pages/1_resumen.py", "pages/2_drivers.py", "pages/3_explorador.py",
         "pages/4_calidad.py", "pages/5_metodologia.py"]

pytestmark = pytest.mark.skipif(not (config.APP_DATA / "metadata.json").exists(), reason="snapshot no generado")


@pytest.mark.parametrize("page", PAGES)
@pytest.mark.parametrize("lang", ["es", "en"])
def test_pagina_carga(page, lang):
    at = AppTest.from_file(MAIN, default_timeout=60)
    at.session_state["lang"] = lang
    at.run()
    at.switch_page(page).run()
    assert not at.exception, at.exception


def test_explorador_interactivo():
    at = AppTest.from_file(MAIN, default_timeout=60)
    at.run()
    at.switch_page("pages/3_explorador.py").run()
    at.selectbox[0].set_value(1).run()
    at.slider[0].set_value(14).run()
    assert not at.exception
    assert len(at.metric) == 4
