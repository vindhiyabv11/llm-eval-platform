import argparse
import os
import sqlite3

import pandas as pd

DB = os.getenv("EVAL_DB", "eval_runs.db")


def export(run_id, n):
    conn = sqlite3.connect(DB)
    q = """
    SELECT c.case_id, c.input, c.expected, c.output, s.score AS judge_score
    FROM case_results c
    JOIN scores s ON s.run_id = c.run_id AND s.case_id = c.case_id
    WHERE c.run_id = ? AND s.metric = 'correctness'
    """
    df = pd.read_sql_query(q, conn, params=(run_id,))
    df = df.sample(min(n, len(df)), random_state=42)
    df["human_pass"] = ""
    df.to_csv("labels.csv", index=False)
    print(f"Wrote labels.csv with {len(df)} rows. Fill human_pass with 1 (correct) or 0 (wrong).")


def score():
    df = pd.read_csv("labels.csv").dropna(subset=["human_pass"])
    j = (df["judge_score"] >= 0.75).astype(int)
    h = df["human_pass"].astype(int)
    agree = float((j == h).mean())
    pj, ph = float(j.mean()), float(h.mean())
    pe = pj * ph + (1 - pj) * (1 - ph)
    kappa = (agree - pe) / (1 - pe) if pe < 1 else 1.0
    print(f"labeled cases : {len(df)}")
    print(f"agreement     : {agree:.1%}")
    print(f"cohen's kappa : {kappa:.2f}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=["export", "score"])
    p.add_argument("--run", help="run id (export mode)")
    p.add_argument("--n", type=int, default=20)
    a = p.parse_args()
    if a.mode == "export":
        export(a.run, a.n)
    else:
        score()