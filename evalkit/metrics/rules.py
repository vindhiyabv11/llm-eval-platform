def non_empty(case, out):
    ok = bool(out.output.strip())
    return ("non_empty", 1.0 if ok else 0.0, "ok" if ok else "empty output")


def length_ok(case, out, max_words=120):
    n = len(out.output.split())
    return ("length_ok", 1.0 if n <= max_words else 0.0, f"{n} words")


def must_contain(case, out):
    if not case.must_contain:
        return None
    text = out.output.lower()
    missing = [s for s in case.must_contain if s.lower() not in text]
    if missing:
        return ("must_contain", 0.0, "missing: " + ", ".join(missing))
    return ("must_contain", 1.0, "all present")


def run_all(case, out):
    results = [non_empty(case, out), length_ok(case, out), must_contain(case, out)]
    return [r for r in results if r is not None]