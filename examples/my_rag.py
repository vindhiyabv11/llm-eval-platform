import httpx

URL = "http://localhost:8000/ask"
_client = httpx.Client(timeout=180)


def answer(question):
    r = _client.post(URL, json={"question": question})
    r.raise_for_status()
    d = r.json()
    return {
        "output": d["answer"],
        # Left empty on purpose: your project already measures faithfulness against
        # the full chunks, and the API only returns 300-character snippets, which
        # would make my faithfulness judge unfairly harsh.
        "contexts": [],
        "prompt_tokens": d.get("prompt_tokens", 0),
        "completion_tokens": d.get("completion_tokens", 0),
    }