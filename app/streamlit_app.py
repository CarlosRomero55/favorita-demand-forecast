"""Punto de entrada de la app (Streamlit Community Cloud: archivo principal app/streamlit_app.py)."""
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
from i18n import t  # noqa: E402

st.set_page_config(page_title="Favorita Demand Forecast", page_icon="🛒", layout="wide")

with st.sidebar:
    st.segmented_control(
        "Idioma / Language", options=["es", "en"], default="es", key="lang",
        format_func=lambda x: {"es": "Español", "en": "English"}[x], required=True,
    )

pages = [
    st.Page("pages/1_resumen.py", title=t("nav_overview"), icon="📊", default=True),
    st.Page("pages/2_drivers.py", title=t("nav_drivers"), icon="🧭"),
    st.Page("pages/3_explorador.py", title=t("nav_explorer"), icon="🔮"),
    st.Page("pages/4_calidad.py", title=t("nav_quality"), icon="✅"),
    st.Page("pages/5_metodologia.py", title=t("nav_method"), icon="🧱"),
]
st.navigation(pages).run()
st.sidebar.caption(t("source_caption"))
