import datetime
import json
import sqlite3

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id TEXT PRIMARY KEY, name TEXT, created_at TEXT,
    target TEXT, dataset TEXT, tag TEXT
);
CREATE TABLE IF NOT EXISTS case_results (
    run_id TEXT, case_id TEXT, input TEXT, expected TEXT, output TEXT,
    latency_s REAL, prompt_tokens INTEGER, completion_tokens INTEGER,
    cost_usd REAL, tags TEXT, error TEXT, contexts TEXT
);
CREATE TABLE IF NOT EXISTS scores (
    run_id TEXT, case_id TEXT, metric TEXT, score REAL, reason TEXT
);
CREATE TABLE IF NOT EXISTS judge_cache (
    key TEXT PRIMARY KEY, score REAL, reason TEXT
);
"""


def connect(path=None):
    conn = sqlite3.connect(path or config.DB_PATH)
    conn.executescript(SCHEMA)
    return conn


def create_run(conn, run_id, name, target, dataset, tag):
    now = datetime.datetime.now().isoformat(timespec="seconds")
    conn.execute(
        "INSERT INTO runs VALUES (?,?,?,?,?,?)",
        (run_id, name, now, target, dataset, tag),
    )
    conn.commit()


def save_case(conn, run_id, case, out, cost, error):
    conn.execute(
        "INSERT INTO case_results VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            run_id, case.id, case.input, case.expected, out.output,
            out.latency_s, out.prompt_tokens, out.completion_tokens,
            cost, ",".join(case.tags), error, json.dumps(out.contexts),
        ),
    )
    conn.commit()


def save_score(conn, run_id, case_id, metric, score, reason):
    conn.execute(
        "INSERT INTO scores VALUES (?,?,?,?,?)",
        (run_id, case_id, metric, score, reason),
    )
    conn.commit()


def cache_get(conn, key):
    return conn.execute(
        "SELECT score, reason FROM judge_cache WHERE key=?", (key,)
    ).fetchone()


def cache_put(conn, key, score, reason):
    conn.execute(
        "INSERT OR REPLACE INTO judge_cache VALUES (?,?,?)", (key, score, reason)
    )
    conn.commit()