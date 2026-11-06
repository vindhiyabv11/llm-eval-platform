from evalkit.metrics import rules
from evalkit.schemas import Case, TargetOutput


def test_must_contain_pass():
    case = Case(id="1", input="q", must_contain=["49"])
    out = TargetOutput(output="The Pro plan costs $49 per month.")
    assert rules.must_contain(case, out)[1] == 1.0


def test_must_contain_fail():
    case = Case(id="1", input="q", must_contain=["49", "annual"])
    out = TargetOutput(output="The Pro plan costs $49 per month.")
    score, reason = rules.must_contain(case, out)[1:]
    assert score == 0.0 and "annual" in reason


def test_must_contain_skipped_when_empty():
    assert rules.must_contain(Case(id="1", input="q"), TargetOutput(output="x")) is None


def test_non_empty_and_length():
    case = Case(id="1", input="q")
    assert rules.non_empty(case, TargetOutput(output="  "))[1] == 0.0
    assert rules.length_ok(case, TargetOutput(output="word " * 500))[1] == 0.0