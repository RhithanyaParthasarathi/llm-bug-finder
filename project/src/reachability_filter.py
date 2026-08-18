"""
Part 2 of the strategy: reachability filtering.

Given the old and new versions of a function (as callables) and a path to
a Python file containing callers, classify each call site of the target
function as:
  - CONFIRMED_BUG_HIT : all args are literals, and executing both versions
                         on those exact values produces different output
  - CONCRETE_SAFE      : all args are literals, and both versions agree
  - VARIABLE_PARAM      : at least one arg is a variable/expression;
                         safety cannot be proven statically, so this is
                         NEVER classified as safe

This is deliberately simple, deterministic static analysis. See CLAUDE.md
"Part 2 — Reachability filtering" before modifying this file.

Verified against 3 real confirmed bugs from EvalPlus/HumanEval+ ChatGPT
completions (match_parens, how_many_times, make_palindrome) — see
results/taxonomy_scan/ for the source data and expected output.
"""
import ast
import importlib.util
from dataclasses import dataclass
from typing import Callable, List, Optional


@dataclass
class CallSiteFinding:
    caller: Optional[str]
    line: int
    verdict: str  # CONFIRMED_BUG_HIT | CONCRETE_SAFE | VARIABLE_PARAM
    detail: str


def load_function(module_path: str, module_name: str, func_name: str) -> Callable:
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, func_name)


def _is_pure_literal(node: ast.AST) -> bool:
    try:
        ast.literal_eval(node)
        return True
    except (ValueError, TypeError):
        return False


def _literal_value(node: ast.AST):
    return ast.literal_eval(node)


class _CallSiteAnalyzer(ast.NodeVisitor):
    def __init__(self, target_func_name: str, canon_fn: Callable, llm_fn: Callable):
        self.target_func_name = target_func_name
        self.canon_fn = canon_fn
        self.llm_fn = llm_fn
        self.findings: List[CallSiteFinding] = []
        self.current_func: Optional[str] = None

    def visit_FunctionDef(self, node: ast.FunctionDef):
        prev, self.current_func = self.current_func, node.name
        self.generic_visit(node)
        self.current_func = prev

    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id == self.target_func_name:
            self._classify_call(node)
        self.generic_visit(node)

    def _classify_call(self, node: ast.Call):
        all_arg_nodes = list(node.args) + [kw.value for kw in node.keywords]
        all_literal = all(_is_pure_literal(a) for a in all_arg_nodes)

        if all_literal:
            args = [_literal_value(a) for a in node.args]
            kwargs = {kw.arg: _literal_value(kw.value) for kw in node.keywords}
            canon_result = self._safe_call(self.canon_fn, args, kwargs)
            llm_result = self._safe_call(self.llm_fn, args, kwargs)
            if canon_result != llm_result:
                verdict = "CONFIRMED_BUG_HIT"
                detail = f"args={args or kwargs} -> canonical={canon_result!r}, new={llm_result!r} (DIFFER)"
            else:
                verdict = "CONCRETE_SAFE"
                detail = f"args={args or kwargs} -> both return {canon_result!r} (agree)"
        else:
            verdict = "VARIABLE_PARAM"
            detail = "one or more arguments are variables/expressions; cannot prove safety statically"

        self.findings.append(CallSiteFinding(self.current_func, node.lineno, verdict, detail))

    @staticmethod
    def _safe_call(fn, args, kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            return f"<raises {type(e).__name__}>"


def analyze(app_path: str, target_func_name: str, canon_fn: Callable, llm_fn: Callable) -> List[CallSiteFinding]:
    with open(app_path) as f:
        tree = ast.parse(f.read(), filename=app_path)
    analyzer = _CallSiteAnalyzer(target_func_name, canon_fn, llm_fn)
    analyzer.visit(tree)
    return analyzer.findings


def print_report(task_name: str, findings: List[CallSiteFinding]) -> None:
    print(f"\n{'='*100}\n{task_name}\n{'='*100}")
    print(f"{'Caller':<20} {'Line':<6} {'Verdict':<20} Detail")
    print("-" * 100)
    for f in findings:
        print(f"{f.caller or '<module>':<20} {f.line:<6} {f.verdict:<20} {f.detail}")
    hits = sum(1 for f in findings if f.verdict == "CONFIRMED_BUG_HIT")
    flagged = sum(1 for f in findings if f.verdict == "VARIABLE_PARAM")
    safe = sum(1 for f in findings if f.verdict == "CONCRETE_SAFE")
    print(f"\n{hits} confirmed bug hits, {flagged} flagged for review (unprovable), "
          f"{safe}/{len(findings)} proven safe and suppressed.")
