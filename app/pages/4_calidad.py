import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from common import ACC, BLU, GRY, INK, load, style
from i18n import t

st.title(t("q_title"))
st.markdown(t("q_intro"))

names = {"lightgbm_global": t("m_lgbm"), "seasonal_naive": t("m_naive"), "moving_avg_14": t("m_ma")}
colors = {"lightgbm_global": ACC, "seasonal_naive": GRY, "moving_avg_14": BLU}
met = load("backtest_metrics")
allm = met[met.segment == "ALL"]
res = allm.groupby("model_name")[["rmsle", "wape", "bias"]].mean().sort_values("rmsle")
tabla = pd.DataFrame({t("q_model"): [names[i] for i in res.index], "RMSLE": res.rmsle.round(3),
                      "WAPE": res.wape.map("{:.1%}".format), t("q_bias"): res.bias.map("{:+.1%}".format)})
st.dataframe(tabla, hide_index=True)

c1, c2 = st.columns(2)
for col, metric in ((c1, "rmsle"), (c2, "wape")):
    fig = go.Figure([go.Bar(x=[f"{t('q_fold')} {f}" for f in g.fold], y=g[metric], name=names[m], marker_color=colors[m])
                     for m, g in allm.groupby("model_name")])
    fig.update_layout(barmode="group", hovermode="closest")
    col.plotly_chart(style(fig, 300, metric.upper()), width="stretch")

bt = load("backtest_daily").groupby("date")[["sales", "lightgbm_global", "seasonal_naive"]].sum() / 1e3
fig = go.Figure([
    go.Scatter(x=bt.index, y=bt.sales, name=t("q_real"), line=dict(color=INK, width=2)),
    go.Scatter(x=bt.index, y=bt.lightgbm_global, name=names["lightgbm_global"], line=dict(color=ACC, width=2)),
    go.Scatter(x=bt.index, y=bt.seasonal_naive, name=names["seasonal_naive"], line=dict(color=GRY, dash="dot")),
])
st.plotly_chart(style(fig, 340, t("q_agg") + f" ({t('units_k')})"), width="stretch")

fam = met[met.segment != "ALL"].groupby(["segment", "model_name"]).wape.mean().unstack()
vol = load("kpi_family").set_index("family").sales
fam = fam.join(vol).sort_values("sales", ascending=False).head(15).iloc[::-1]
fig = go.Figure([go.Bar(y=fam.index, x=fam[m] * 100, orientation="h", name=names[m], marker_color=colors[m])
                 for m in ["seasonal_naive", "lightgbm_global"]])
fig.update_layout(barmode="group", hovermode="closest", xaxis_title="WAPE %")
st.plotly_chart(style(fig, 560, t("q_family")), width="stretch")

imp = load("feature_importance").head(12).iloc[::-1]
fig = go.Figure(go.Bar(y=imp.feature, x=imp.gain_share * 100, orientation="h", marker_color=ACC))
fig.update_layout(hovermode="closest")
st.plotly_chart(style(fig, 420, t("q_imp")), width="stretch")
st.markdown(t("q_imp_text"))
