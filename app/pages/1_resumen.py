import plotly.graph_objects as go
import streamlit as st
from common import ACC, GRY, load, meta, style
from i18n import t

m = meta()
k, mod = m["kpis"], m["model"]

st.title(t("ov_title"))
st.markdown(t("ov_sub"))

c1, c2 = st.columns(2)
c1.metric(t("kpi_total"), f"{k['total_sales'] / 1e6:,.0f} M")
c2.metric(t("kpi_daily"), f"{k['avg_daily_sales_2017'] / 1e3:,.0f} k")
c3, c4 = st.columns(2)
c3.metric(t("kpi_growth"), f"{k['growth_2017_comparable']:+.1%}", help=t("kpi_growth_help"))
c4.metric(t("kpi_wape"), f"{mod['wape']:.1%}",
          t("kpi_wape_delta").format(d=(mod["wape"] - mod["baseline_wape"]) * 100), delta_color="inverse")

st.subheader(t("ov_headline"))
st.info(t("ov_headline_text").format(b=mod["baseline_wape"], m=mod["wape"], sun=k["sunday_index"] - 1,
                                     pay=k["payday_post_1_3_pct"], hol=k["national_holiday_median_pct"]))

d = load("sales_total_daily").set_index("date").sales.resample("MS").mean() / 1e3
ds = load("sales_stable_daily").set_index("date").sales.resample("MS").mean() / 1e3
fig = go.Figure([
    go.Scatter(x=d.index, y=d.values, mode="lines", name=t("ov_all"), line=dict(color=GRY, width=2),
               hovertemplate="%{x|%b %Y}: %{y:,.0f}k<extra></extra>"),
    go.Scatter(x=ds.index, y=ds.values, mode="lines", name=t("ov_stable").format(n=k["stable_families"]),
               line=dict(color=ACC, width=2.5), hovertemplate="%{x|%b %Y}: %{y:,.0f}k<extra></extra>"),
])
st.plotly_chart(style(fig, title=t("ov_chart")), width="stretch")
st.caption(t("ov_reg_note").format(s=k["stable_share"]))
st.markdown(t("ov_more"))
st.caption(f"{t('source_caption')} [{m['source']['url']}]({m['source']['url']})")
