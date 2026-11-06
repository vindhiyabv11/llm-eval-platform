import importlib
import time

import httpx

from .schemas import TargetOutput


def _normalize(res, latency):
    if isinstance(res, str):
        res = {"output": res}
    return TargetOutput(
        output=str(res.get("output", "")),
        latency_s=latency,
        prompt_tokens=int(res.get("prompt_tokens", 0)),
        completion_tokens=int(res.get("completion_tokens", 0)),
        contexts=list(res.get("contexts", [])),
    )


def load_target(spec):
    """spec is either 'package.module:function' or an http(s) URL."""
    if spec.startswith("http://") or spec.startswith("https://"):
        client = httpx.Client(timeout=120)

        def call(question):
            r = client.post(spec, json={"input": question})
            r.raise_for_status()
            return r.json()

        return call
    module_name, func_name = spec.split(":")
    module = importlib.import_module(module_name)
    return getattr(module, func_name)


def invoke(target, question):
    start = time.perf_counter()
    res = target(question)
    return _normalize(res, time.perf_counter() - start)