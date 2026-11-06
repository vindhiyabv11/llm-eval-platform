import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
APP_MODEL = os.getenv("APP_MODEL", "gpt-4o-mini")
JUDGE_MODEL = os.getenv("JUDGE_MODEL", "gpt-4o-mini")
DB_PATH = os.getenv("EVAL_DB", "eval_runs.db")

# USD per 1M tokens. Verify against OpenAI's pricing page and add your model here.
PRICES = {
    "gpt-4o-mini": {"in": 0.15, "out": 0.60},
    "gpt-4.1-mini": {"in": 0.40, "out": 1.60},
}





