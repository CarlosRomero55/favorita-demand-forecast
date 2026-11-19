import plotly.graph_objects as go
import streamlit as st
from common import ACC, BLU, GRY, load, meta, style
from i18n import t

k = meta()["kpis"]
st.title(t("dr_title"))
st.caption(t("assoc_note"))

tabs = st.tabs([t("tab_hol"), t("tab_promo"), t("tab_pay"), t("tab_eq"), t("tab_season")])

with tabs[0]:
    h = load("effect_holidays").set_index("effect")
    labels = {"national_holiday": t("hol_national"), "christmas_additional": t("hol_christmas"),
              "national_event": t("hol_event"), "local_holiday": t("hol_local")}
    orden = ["local_holiday", "national_event", "national_holiday", "christmas_additional"]
    vals = h.loc[orden, "median_pct"] * 100
    fig = go.Figure(go.Bar(x=vals.values, y=[labels[o] for o in orden], orientation="h",
                           marker_color=[BLU, GRY, ACC, ACC], text=[f"{v:+.1f}%" for v in vals], textposition="outside",
                           hovertemplate="%{y}: %{x:+.1f}%<extra></extra>"))
    fig.update_traces(cliponaxis=False)
    fig.update_layout(xaxis_title=t("hol_axis"), hovermode="closest",
                      xaxis_range=[min(vals.min(), 0) * 1.4, vals.max() * 1.2])
    st.plotly_chart(style(fig, 300), width="stretch")
    st.markdown(t("hol_text").format(n=k["national_holiday_median_pct"], c=k["christmas_eve_median_pct"],
                                     l=k["local_holiday_median_pct"]))

with tabs[1]:
    p = load("effect_promo").head(12).iloc[::-1]
    fig = go.Figure([
        go.Bar(y=p.family, x=p.naive_lift * 100, orientation="h", name=t("promo_naive"), marker_color=GRY),
        go.Bar(y=p.family, x=p.stratified_lift * 100, orientation="h", name=t("promo_strat"), marker_color=ACC),
    ])
    fig.update_layout(barmode="group", xaxis_title=t("promo_axis"), hovermode="closest")
    st.plotly_chart(style(fig, 520), width="stretch")
    g = load("effect_promo").set_index("family").loc["GROCERY I"]
    st.markdown(t("promo_text").format(gn=g.naive_lift, gs=g.stratified_lift, w=k["promo_lift_weighted_stratified"]))

with tabs[2]:
    pp = load("effect_payday")
    fig = go.Figure(go.Bar(x=pp.days_since_payday, y=pp["mean"],
                           marker_color=[ACC if 1 <= d <= 6 else GRY for d in pp.days_since_payday],
                           hovertemplate="%{x}: %{y:.3f}<extra></extra>"))
    fig.add_hline(y=1, line_color="black", line_width=1)
    fig.update_layout(xaxis_title=t("pay_axis"), yaxis_title=t("pay_y"), yaxis_range=[0.85, 1.12])
    st.plotly_chart(style(fig), width="stretch")
    st.markdown(t("pay_text").format(p=k["payday_post_1_3_pct"]))

with tabs[3]:
    e = load("effect_earthquake").pivot(index="week", columns="zone", values="avg_daily")
    base = e.loc[:"2016-04-10"].mean()
    fig = go.Figure([
        go.Scatter(x=e.index, y=e[True] / base[True], name=t("eq_zone"), line=dict(color=ACC, width=3), mode="lines+markers"),
        go.Scatter(x=e.index, y=e[False] / base[False], name=t("eq_rest"), line=dict(color=GRY, width=2), mode="lines+markers"),
    ])
    fig.add_vline(x="2016-04-16", line_dash="dash", line_color="black")
    fig.add_hline(y=1, line_color="black", line_width=.5)
    fig.update_layout(yaxis_title=t("eq_y"))
    st.plotly_chart(style(fig), width="stretch")
    st.markdown(t("eq_text").format(z=k["earthquake_zone_change"], r=k["earthquake_rest_change"],
                                    z15=k["earthquake_zone_change_2015"], r15=k["earthquake_rest_change_2015"]))

with tabs[4]:
    s = load("effect_seasonality")
    c1, c2 = st.columns(2)
    dw = s[s.kind == "dow"]
    f1 = go.Figure(go.Bar(x=t("dows").split(","), y=dw["index"], marker_color=[GRY] * 5 + [ACC] * 2))
    f1.add_hline(y=1, line_color="black", line_width=1)
    c1.plotly_chart(style(f1, 300, t("season_dow")), width="stretch")
    mo = s[s.kind == "month"]
    f2 = go.Figure(go.Bar(x=t("months").split(","), y=mo["index"], marker_color=[GRY] * 11 + [ACC]))
    f2.add_hline(y=1, line_color="black", line_width=1)
    c2.plotly_chart(style(f2, 300, t("season_month")), width="stretch")
    st.markdown(t("season_text").format(s=k["sunday_index"] - 1, d=k["december_index"] - 1,
                                        ol=k["oil_corr_level"], oy=k["oil_corr_yoy"]))
