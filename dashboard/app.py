import os
import sqlite3

import pandas as pd
import streamlit as st

DB = os.getenv("EVAL_DB", "eval_runs.db")
CORE = ["correctness", "faithfulness", "relevance", "must_contain"]

st.set_page_config(page_title="LLM Eval Dashboard", layout="wide")
st.title("LLM Eval Dashboard")

conn = sqlite3.connect(DB)
runs = pd.read_sql_query("SELECT * FROM runs ORDER BY created_at", conn)
if runs.empty:
    st.warning("No runs yet. Run: uv run python -m evalkit run --target ...")
    st.stop()

scores = pd.read_sql_query("SELECT * FROM scores", conn)
cases = pd.read_sql_query("SELECT * FROM case_results", conn)
dataset = st.sidebar.selectbox("Dataset", sorted(runs["dataset"].unique()))
runs = runs[runs["dataset"] == dataset].reset_index(drop=True)
runs["label"] = [f"{i + 1:02d} {n} ({r})" for i, (n, r) in enumerate(zip(runs["name"], runs["id"]))]

by_metric = scores.groupby(["run_id", "metric"])["score"].mean().unstack()
by_metric = by_metric.reindex(runs["id"])
core_cols = [m for m in CORE if m in by_metric.columns]
quality = by_metric[core_cols].mean(axis=1) if core_cols else by_metric.mean(axis=1)

lat = cases.groupby("run_id")["latency_s"].agg(p50="median", p95=lambda s: s.quantile(0.95))
cost = cases.groupby("run_id")["cost_usd"].sum().rename("cost_usd")

overview = (
    runs.set_index("id")[["label", "tag", "created_at"]]
    .join(quality.rename("quality"))
    .join(lat)
    .join(cost)
)

st.subheader("Runs")
st.dataframe(overview.round(4))

chart_df = overview.set_index("label")
c1, c2, c3 = st.columns(3)
c1.markdown("**Quality by run**")
c1.line_chart(chart_df["quality"])
c2.markdown("**Latency p95 (s)**")
c2.line_chart(chart_df["p95"])
c3.markdown("**Cost per run (USD)**")
c3.bar_chart(chart_df["cost_usd"])

st.subheader("Metrics by run")
metric_chart = by_metric.join(runs.set_index("id")["label"]).set_index("label")
st.line_chart(metric_chart)

st.subheader("Worst cases")
label = st.selectbox("Run", runs["label"].tolist()[::-1])
rid = runs.loc[runs["label"] == label, "id"].iloc[0]
rs = scores[scores["run_id"] == rid]
rs_core = rs[rs["metric"].isin(CORE)]
rs_core = rs_core if len(rs_core) else rs
per_case = rs_core.groupby("case_id")["score"].mean().rename("score").reset_index()
detail = (
    per_case.merge(
        cases[cases["run_id"] == rid][["case_id", "input", "expected", "output"]],
        on="case_id",
    )
    .sort_values("score")
    .head(10)
)
st.dataframe(detail)

if len(detail):
    pick = st.selectbox("Inspect case", detail["case_id"].tolist())
    st.dataframe(rs[rs["case_id"] == pick][["metric", "score", "reason"]])