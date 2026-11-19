import streamlit as st
from common import REPO_URL, meta
from i18n import t

m = meta()
st.title(t("me_title"))

st.subheader(t("me_arch"))
st.graphviz_chart("""
digraph {
  rankdir=LR; node [shape=box, style="rounded,filled", fillcolor="#F1EEE6", color="#8A8478", fontname="Helvetica"];
  K [label="Kaggle\\n6 CSV"]; B [label="bronze\\nCSV + linaje"]; S [label="silver\\nPK / FK"]; G [label="gold\\nestrella + KPI"];
  M [label="LightGBM\\nbacktest 3 cortes", fillcolor="#F4DED3"]; P [label="snapshot\\nParquet < 5 MB"]; A [label="Streamlit\\nES / EN", fillcolor="#F4DED3"];
  K -> B -> S -> G -> M -> P -> A; G -> P;
}""")
st.caption("DuckDB (Medallion) · scripts T-SQL equivalentes para SQL Server · Python · LightGBM · Plotly")

st.subheader(t("me_clean"))
st.markdown(t("me_clean_text"))
st.subheader(t("me_model"))
st.markdown(t("me_model_text"))
st.subheader(t("me_limits"))
st.markdown(t("me_limits_text"))
st.subheader(t("me_source"))
st.markdown(f"{t('me_source_text')}\n\n- [{m['source']['name']}]({m['source']['url']}) · [Rules]({m['source']['rules_url']})\n"
            f"- {m['source']['citation']}\n- [{t('me_repo')}]({REPO_URL})")
