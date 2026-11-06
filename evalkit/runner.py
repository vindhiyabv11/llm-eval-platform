import uuid

from . import config, storage
from .metrics import judge, rules
from .schemas import TargetOutput, load_dataset
from .targets import invoke, load_target


def cost_of(prompt_tokens, completion_tokens):
    p = config.PRICES.get(config.APP_MODEL, {"in": 0.0, "out": 0.0})
    return prompt_tokens * p["in"] / 1e6 + completion_tokens * p["out"] / 1e6


def run_eval(target_spec, dataset_path, name, tag="", use_judge=True):
    conn = storage.connect()
    cases = load_dataset(dataset_path)
    target = load_target(target_spec)
    run_id = uuid.uuid4().hex[:8]
    storage.create_run(conn, run_id, name, target_spec, dataset_path, tag)

    for i, case in enumerate(cases, 1):
        print(f"[{i}/{len(cases)}] {case.id}")
        error = None
        try:
            out = invoke(target, case.input)
        except Exception as e:
            out = TargetOutput(output="")
            error = str(e)
            print("  ERROR:", error)

        cost = cost_of(out.prompt_tokens, out.completion_tokens)
        storage.save_case(conn, run_id, case, out, cost, error)

        results = [("no_error", 0.0 if error else 1.0, error or "ok")]
        results += rules.run_all(case, out)
        if use_judge and error is None:
            results += judge.run_all(case, out, conn)
        for metric, score, reason in results:
            storage.save_score(conn, run_id, case.id, metric, score, reason)

    return conn, run_id