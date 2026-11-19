import math

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from common import ACC, GRY, INK, load, style
from i18n import t

Z = {0.90: 1.2816, 0.95: 1.6449, 0.98: 2.0537}  # igual que src/config.SERVICE_LEVELS

st.title(t("ex_title"))

stores, fams = load("stores"), load("families")
store_lbl = {r.store_nbr: f"{r.store_nbr} · {r.city} ({r.state}) · tipo {r.store_type}" for r in stores.itertuples()}
fam_lbl = dict(zip(fams.family_id, fams.family))
default_fam = int(fams.loc[fams.family == "GROCERY I", "family_id"].iloc[0])

c1, c2 = st.columns(2)
store = c1.selectbox(t("ex_store"), list(store_lbl), index=list(store_lbl).index(44), format_func=store_lbl.get)
fam = c2.selectbox(t("ex_family"), list(fam_lbl), index=list(fam_lbl).index(default_fam), format_func=fam_lbl.get)
c3, c4 = st.columns(2)
sl = c3.segmented_control(t("ex_service"), options=[0.90, 0.95, 0.98], default=0.95, required=True,
                          format_func=lambda x: f"{x:.0%}")
lead = c4.slider(t("ex_lead"), 1, 16, 7)

hist = load("sales_daily")
hist = hist[(hist.store_nbr == store) & (hist.family_id == fam)]
hist = hist[hist.date >= hist.date.max() - pd.Timedelta(days=119)]
fc = load("forecasts")
fc = fc[(fc.store_nbr == store) & (fc.family_id == fam)].pivot_table(
    index="date", columns="model_name", values="forecast").sort_index()
sigma = load("forecasts").query("store_nbr == @store and family_id == @fam").sigma_daily.iloc[0]
sigma = 0.0 if pd.isna(sigma) else float(sigma)
z = Z[sl]

lgbm = fc["lightgbm_global"]
fig = go.Figure()
fig.add_trace(go.Scatter(x=list(lgbm.index) + list(lgbm.index[::-1]),
                         y=list(lgbm + z * sigma) + list((lgbm - z * sigma).clip(lower=0)[::-1]),
                         fill="toself", fillcolor="rgba(180,83,42,.18)", line=dict(width=0),
                         name=t("ex_band"), hoverinfo="skip"))
fig.add_trace(go.Scatter(x=hist.date, y=hist.sales, name=t("ex_history"), line=dict(color=INK, width=1.3)))
fig.add_trace(go.Scatter(x=fc.index, y=fc["seasonal_naive"], name=t("ex_naive"), line=dict(color=GRY, dash="dot")))
fig.add_trace(go.Scatter(x=lgbm.index, y=lgbm, name=t("ex_forecast"), line=dict(color=ACC, width=3)))
fig.add_vline(x=hist.date.max(), line_dash="dash", line_color=GRY)
st.plotly_chart(style(fig, 420, f"{store_lbl[store]} · {fam_lbl[fam]}"), width="stretch")

fc_l = float(lgbm.iloc[:lead].sum())
ss = z * sigma * math.sqrt(lead)
m1, m2 = st.columns(2)
m1.metric(t("ex_fc16"), f"{lgbm.sum():,.0f} {t('units')}")
m2.metric(t("ex_fcl").format(l=lead), f"{fc_l:,.0f}")
m3, m4 = st.columns(2)
m3.metric(t("ex_ss"), f"{ss:,.0f}")
m4.metric(t("ex_target"), f"{fc_l + ss:,.0f}")
st.caption(t("ex_sigma").format(s=sigma))
if lgbm.sum() == 0:
    st.warning(t("ex_zero"))
st.info(t("ex_formula"))

with st.expander(t("ex_table")):
    promo = load("forecasts").query("store_nbr == @store and family_id == @fam and model_name == 'lightgbm_global'")
    tabla = promo.sort_values("date")[["date", "forecast", "onpromotion"]].rename(
        columns={"date": t("col_date"), "forecast": t("col_fc"), "onpromotion": t("col_promo")})
    st.dataframe(tabla, hide_index=True, column_config={t("col_fc"): st.column_config.NumberColumn(format="%.1f"),
                                                        t("col_date"): st.column_config.DateColumn(format="YYYY-MM-DD")})
