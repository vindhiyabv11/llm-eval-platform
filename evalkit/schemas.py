import json
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Case:
    id: str
    input: str
    expected: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    must_contain: list[str] = field(default_factory=list)


@dataclass
class TargetOutput:
    output: str
    latency_s: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    contexts: list[str] = field(default_factory=list)


def load_dataset(path):
    cases = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            cases.append(
                Case(
                    id=d["id"],
                    input=d["input"],
                    expected=d.get("expected"),
                    tags=d.get("tags", []),
                    must_contain=d.get("must_contain", []),
                )
            )
    return cases

