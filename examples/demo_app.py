import os
import re

from openai import OpenAI

from evalkit import config

KB = [
    "Acme Cloud offers three plans: Starter at $10 per month, Pro at $49 per month, and Enterprise with custom pricing.",
    "The Starter plan includes 5 projects and 10 GB storage. The Pro plan includes unlimited projects and 500 GB storage.",
    "Refunds are available within 30 days of purchase for annual plans. Monthly plans are not refundable.",
    "Support is available 24/7 via chat for Pro and Enterprise. Starter users get email support with a 48-hour response time.",
    "Acme Cloud data centers are located in Frankfurt, Virginia, and Singapore.",
    "Two-factor authentication is mandatory for all admin accounts and optional for regular users.",
    "The API rate limit is 100 requests per minute on Starter and 1000 requests per minute on Pro.",
    "To cancel a subscription, go to Settings, then Billing, and click Cancel Plan. Cancellation takes effect at the end of the billing period.",
]

STOP = {
    "the", "a", "an", "is", "are", "of", "on", "for", "to", "do", "does", "how",
    "what", "can", "i", "my", "in", "and", "or", "it", "you", "your", "with", "by",
}

VARIANT = os.getenv("APP_VARIANT", "v1")
_client = None


def _tokens(text):
    words = re.findall(r"[a-z0-9$]+", text.lower())
    return {w[:-1] if len(w) > 3 and w.endswith("s") else w for w in words} - STOP


def retrieve(question, k):
    q = _tokens(question)
    ranked = sorted(KB, key=lambda d: len(q & _tokens(d)), reverse=True)
    return ranked[:k]


def _get_client():
    global _client
    if _client is None:
        _client = OpenAI(api_key=config.OPENAI_API_KEY)
    return _client


def answer(question):
    if VARIANT == "v1":
        k = 1
        system = "You are a helpful support assistant for Acme Cloud. Answer the question."
    else:
        k = 3
        system = (
            "You are a support assistant for Acme Cloud. Answer ONLY using the "
            "provided context. Be concise (max 2 sentences). If the context does "
            "not contain the answer, say you do not know."
        )
    contexts = retrieve(question, k)
    user = "Context:\n" + "\n".join("- " + c for c in contexts) + "\n\nQuestion: " + question
    resp = _get_client().chat.completions.create(
        model=config.APP_MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return {
        "output": resp.choices[0].message.content,
        "contexts": contexts,
        "prompt_tokens": resp.usage.prompt_tokens,
        "completion_tokens": resp.usage.completion_tokens,
    }