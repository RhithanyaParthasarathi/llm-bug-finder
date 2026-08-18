"""
Unit tests for Smart Reachability Analyzer.
"""
from src.smart_reachability import analyze_reachability


def canon_add(x: int) -> int:
    return x + 10


def buggy_add(x: int) -> int:
    return x + 20  # Buggy implementation


def test_constant_propagation_finds_bug_hit():
    caller_code = """
def my_service():
    input_val = 5  # local constant
    result = target_func(input_val)
    return result
"""
    findings = analyze_reachability(caller_code, "target_func", canon_add, buggy_add)
    assert len(findings) == 1
    f = findings[0]
    assert f.verdict == "CONFIRMED_BUG_HIT"
    assert f.caller == "my_service"
    assert f.resolved_args == [5]


def test_dynamic_variable_flagged_for_review():
    caller_code = """
def dynamic_caller(untrusted_user_input):
    result = target_func(untrusted_user_input)
    return result
"""
    findings = analyze_reachability(caller_code, "target_func", canon_add, buggy_add)
    assert len(findings) == 1
    f = findings[0]
    assert f.verdict == "VARIABLE_PARAM"
    assert "requires manual audit" in f.detail
