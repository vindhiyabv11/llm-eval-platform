import hashlib
import json

from openai import OpenAI

from .. import config, storage

_client = None

SYSTEM = (
    "You are a strict, impartial evaluator of AI assistant answers. "
    'Respond with JSON only: {"score": <integer 1-5>, "reason": "<one sentence>"}.'
)

RUBRICS = {
    "correctness": (
        "Score how well the ANSWER matches the REFERENCE in meaning. "
        "5 = fully correct and complete; 4 = correct with minor omissions; "
        "3 = partially correct; 2 = mostly wrong; 1 = wrong or contradicts the reference. "
        "If the REFERENCE says the information is unavailable, the ANSWER must say it "
        "does not know; inventing details scores 1."
    ),
    "faithfulness": (
        "Score whether every claim in the ANSWER is supported by the CONTEXT. "
        "5 = all claims supported; 3 = some unsupported detail; 1 = mostly unsupported "
        "or fabricated. An answer that says it does not know is faithful (5)."
    ),
        "relevance": (
        "Score whether the ANSWER directly addresses the QUESTION. "
        "5 = fully on point; 3 = partially; 1 = off topic. "
        "An honest 'I do not know' to a question the context cannot answer counts as relevant (5)."
    ),
}


def _client_get():
    global _client
    if _client is None:
        _client = OpenAI(api_key=config.OPENAI_API_KEY)
    return _client


def _build_prompt(metric, case, out):
    parts = [f"RUBRIC: {RUBRICS[metric]}", f"QUESTION: {case.input}"]
    if metric == "correctness":
        parts.append(f"REFERENCE: {case.expected}")
    if metric == "faithfulness":
        parts.append("CONTEXT:\n" + "\n".join(out.contexts))
    parts.append(f"ANSWER: {out.output}")
    return "\n\n".join(parts)


def judge(metric, case, out, conn):
    prompt = _build_prompt(metric, case, out)
    key = hashlib.sha256((config.JUDGE_MODEL + metric + prompt).encode()).hexdigest()
    cached = storage.cache_get(conn, key)
    if cached:
        return cached[0], cached[1]
    resp = _client_get().chat.completions.create(
        model=config.JUDGE_MODEL,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt},
        ],
    )
    data = json.loads(resp.choices[0].message.content)
    raw = max(1, min(5, int(data["score"])))
    score = (raw - 1) / 4
    reason = str(data.get("reason", ""))
    storage.cache_put(conn, key, score, reason)
    return score, reason


def run_all(case, out, conn):
    results = []
    for metric in RUBRICS:
        if metric == "correctness" and not case.expected:
            continue
        if metric == "faithfulness" and not out.contexts:
            continue
        try:
            score, reason = judge(metric, case, out, conn)
            results.append((metric, score, reason))
        except Exception as e:
            print(f"  judge error ({metric}, {case.id}): {e}")
    return results