import argparse
import sys

import pandas as pd

from . import storage
from .compare import compare_runs, print_summary, summarize
from .runner import run_eval


def cmd_run(a):
    conn, run_id = run_eval(
        a.target, a.dataset, a.name, a.tag, use_judge=not a.no_judge
    )
    s = summarize(conn, run_id)
    print_summary(run_id, s)

    failed = False
    gated = False
    if a.fail_under is not None:
        gated = True
        if s["quality"] < a.fail_under:
            print(f"GATE FAIL: quality {s['quality']:.3f} < {a.fail_under}")
            failed = True
    if a.baseline:
        gated = True
        b = summarize(conn, a.baseline)
        diff = s["quality"] - b["quality"]
        if diff < -a.max_drop:
            print(f"GATE FAIL: quality dropped {diff:+.3f} vs baseline {a.baseline}")
            failed = True
    if gated and not failed:
        print("GATE PASS")
    sys.exit(1 if failed else 0)


def cmd_compare(a):
    conn = storage.connect()
    sa, sb, deltas, worse = compare_runs(conn, a.run_a, a.run_b)
    print(
        f"quality: {sa['quality']:.3f} -> {sb['quality']:.3f} "
        f"({sb['quality'] - sa['quality']:+.3f})"
    )
    for m in sorted(deltas):
        print(f"  {m:<14} {deltas[m]:+.3f}")
    print(
        f"latency p95: {sa['p95']:.2f}s -> {sb['p95']:.2f}s | "
        f"cost: ${sa['cost']:.5f} -> ${sb['cost']:.5f}"
    )
    if len(worse):
        print("\nRegressed cases:")
        for case_id, row in worse.iterrows():
            print(f"  {case_id}: {row['a']:.2f} -> {row['b']:.2f}")
    else:
        print("\nNo regressed cases.")


def cmd_list(a):
    conn = storage.connect()
    runs = pd.read_sql_query(
        "SELECT id, name, tag, created_at FROM runs ORDER BY created_at", conn
    )
    for _, r in runs.iterrows():
        s = summarize(conn, r["id"])
        print(f"{r['id']}  {r['name']:<20} tag={r['tag']:<8} quality={s['quality']:.3f}")


def main():
    p = argparse.ArgumentParser(prog="evalkit")
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run")
    r.add_argument("--target", required=True, help="module:function or http URL")
    r.add_argument("--dataset", default="datasets/golden.jsonl")
    r.add_argument("--name", default="run")
    r.add_argument("--tag", default="")
    r.add_argument("--no-judge", action="store_true")
    r.add_argument("--fail-under", type=float, default=None)
    r.add_argument("--baseline", default=None, help="run id to compare against")
    r.add_argument("--max-drop", type=float, default=0.05)
    r.set_defaults(func=cmd_run)

    c = sub.add_parser("compare")
    c.add_argument("run_a", help="baseline run id")
    c.add_argument("run_b", help="new run id")
    c.set_defaults(func=cmd_compare)

    l = sub.add_parser("list")
    l.set_defaults(func=cmd_list)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()