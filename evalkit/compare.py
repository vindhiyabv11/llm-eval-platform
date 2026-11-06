import pandas as pd

CORE = {"correctness", "faithfulness", "relevance", "must_contain"}


def scores_df(conn, run_id):
    return pd.read_sql_query(
        "SELECT case_id, metric, score, reason FROM scores WHERE run_id=?",
        conn,
        params=(run_id,),
    )


def _core(df):
    sub = df[df["metric"].isin(CORE)]
    return sub if len(sub) else df


def summarize(conn, run_id):
    s = _core(scores_df(conn, run_id))
    metrics = s.groupby("metric")["score"].mean().to_dict() if len(s) else {}
    quality = sum(metrics.values()) / len(metrics) if metrics else 0.0
    c = pd.read_sql_query(
        "SELECT latency_s, cost_usd FROM case_results WHERE run_id=?",
        conn,
        params=(run_id,),
    )
    has = len(c) > 0
    return {
        "metrics": metrics,
        "quality": float(quality),
        "n_cases": len(c),
        "p50": float(c["latency_s"].median()) if has else 0.0,
        "p95": float(c["latency_s"].quantile(0.95)) if has else 0.0,
        "cost": float(c["cost_usd"].sum()) if has else 0.0,
    }


def compare_runs(conn, run_a, run_b, case_drop=0.25):
    sa, sb = summarize(conn, run_a), summarize(conn, run_b)
    names = set(sa["metrics"]) | set(sb["metrics"])
    deltas = {m: sb["metrics"].get(m, 0.0) - sa["metrics"].get(m, 0.0) for m in names}
    ca = _core(scores_df(conn, run_a)).groupby("case_id")["score"].mean()
    cb = _core(scores_df(conn, run_b)).groupby("case_id")["score"].mean()
    joined = pd.concat([ca.rename("a"), cb.rename("b")], axis=1).dropna()
    joined["delta"] = joined["b"] - joined["a"]
    worse = joined[joined["delta"] <= -case_drop].sort_values("delta")
    return sa, sb, deltas, worse


def print_summary(run_id, s):
    print(f"\nRun {run_id}: quality={s['quality']:.3f} cases={s['n_cases']}")
    for m, v in sorted(s["metrics"].items()):
        print(f"  {m:<14} {v:.3f}")
    print(f"  latency p50={s['p50']:.2f}s p95={s['p95']:.2f}s cost=${s['cost']:.5f}")