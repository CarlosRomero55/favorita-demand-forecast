"""Utilidades compartidas por las páginas: carga de datos en caché y estilo de gráficos."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

DATA = Path(__file__).resolve().parent / "data"
ACC, GRY, BLU, INK = "#B4532A", "#8A8478", "#2F5D7C", "#2A2723"
REPO_URL = "https://github.com/CarlosRomero55/favorita-demand-forecast"


@st.cache_data
def load(name: str) -> pd.DataFrame:
    df = pd.read_parquet(DATA / f"{name}.parquet")
    for c in ("date", "week", "month"):
        if c in df.columns and not pd.api.types.is_integer_dtype(df[c]):
            df[c] = pd.to_datetime(df[c])
    return df


@st.cache_data
def meta() -> dict:
    return json.loads((DATA / "metadata.json").read_text(encoding="utf-8"))


def style(fig: go.Figure, height: int = 360, title: str | None = None) -> go.Figure:
    fig.update_layout(
        height=height, title=title, margin=dict(l=10, r=10, t=50 if title else 20, b=40),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color=INK),
        legend=dict(orientation="h", yanchor="top", y=-0.12, x=0), hovermode="x unified",
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="rgba(0,0,0,.08)")
    return fig
