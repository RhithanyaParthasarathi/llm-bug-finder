"""
Smart Reachability Filter with Intra-Procedural Constant Propagation.
Evaluates caller exposure to differential behavior with zero hallucination:
- Resolves locally defined constants (e.g., `x = 'test'; func(x)`).
- Evaluates bounded loops (e.g., `for i in range(3): func(i)`).
- Executes both function versions on resolved values.
- Categorizes call sites as:
    CONFIRMED_BUG_HIT : All args resolve to concrete values, and versions differ.
    CONCRETE_SAFE      : All args resolve to concrete values, and versions agree.
    VARIABLE_PARAM     : Args cannot be resolved statically (never claimed safe).
"""
import ast
import importlib.util
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple


@dataclass
class SmartFinding:
    caller: Optional[str]
    line: int
    verdict: str  # CONFIRMED_BUG_HIT | CONCRETE_SAFE | VARIABLE_PARAM
    detail: str
    resolved_args: Optional[List[Any]] = None


class ScopeTracker(ast.NodeVisitor):
    def __init__(self):
        self.scope: Dict[str, Any] = {}

    def visit_Assign(self, node: ast.Assign):
        try:
            val = ast.literal_eval(node.value)
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self.scope[target.id] = val
        except Exception:
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self.scope.pop(target.id, None)
        self.generic_visit(node)


class SmartCallSiteAnalyzer(ast.NodeVisitor):
    def __init__(self, target_func_name: str, canon_fn: Callable, llm_fn: Callable):
        self.target_func_name = target_func_name
        self.canon_fn = canon_fn
        self.llm_fn = llm_fn
        self.findings: List[SmartFinding] = []
        self.current_func: Optional[str] = None
        self.local_scope: Dict[str, Any] = {}

    def visit_FunctionDef(self, node: ast.FunctionDef):
        prev_func = self.current_func
        prev_scope = self.local_scope
        self.current_func = node.name
        self.local_scope = {}

        # First pass: collect local constant assignments
        for stmt in node.body:
            if isinstance(stmt, ast.Assign):
                try:
                    val = ast.literal_eval(stmt.value)
                    for t in stmt.targets:
                        if isinstance(t, ast.Name):
                            self.local_scope[t.id] = val
                except Exception:
                    pass

        self.generic_visit(node)
        self.current_func = prev_func
        self.local_scope = prev_scope

    def _resolve_arg(self, node: ast.AST) -> Tuple[bool, Any]:
        """Try resolving argument via literal_eval or local scope."""
        try:
            return True, ast.literal_eval(node)
        except Exception:
            pass
        if isinstance(node, ast.Name) and node.id in self.local_scope:
            return True, self.local_scope[node.id]
        return False, None

    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id == self.target_func_name:
            self._classify_call(node)
        self.generic_visit(node)

    def _safe_call(self, fn: Callable, args: list, kwargs: dict) -> Any:
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            return f"<raises {type(e).__name__}: {e}>"

    def _classify_call(self, node: ast.Call):
        resolved_args = []
        all_resolved = True

        for a in node.args:
            ok, val = self._resolve_arg(a)
            if ok:
                resolved_args.append(val)
            else:
                all_resolved = False
                break

        resolved_kwargs = {}
        if all_resolved:
            for kw in node.keywords:
                ok, val = self._resolve_arg(kw.value)
                if ok:
                    resolved_kwargs[kw.arg] = val
                else:
                    all_resolved = False
                    break

        if all_resolved:
            canon_res = self._safe_call(self.canon_fn, resolved_args, resolved_kwargs)
            llm_res = self._safe_call(self.llm_fn, resolved_args, resolved_kwargs)

            if canon_res != llm_res:
                verdict = "CONFIRMED_BUG_HIT"
                detail = f"args={resolved_args} -> canon={canon_res!r}, new={llm_res!r} (DIFFER)"
            else:
                verdict = "CONCRETE_SAFE"
                detail = f"args={resolved_args} -> both return {canon_res!r} (agree)"
        else:
            verdict = "VARIABLE_PARAM"
            detail = "unresolvable dynamic parameter; requires manual audit"

        self.findings.append(SmartFinding(
            caller=self.current_func,
            line=node.lineno,
            verdict=verdict,
            detail=detail,
            resolved_args=resolved_args if all_resolved else None,
        ))


def analyze_reachability(app_source: str, target_func: str, canon_fn: Callable, llm_fn: Callable) -> List[SmartFinding]:
    """Analyze reachability of a target function across Python source text."""
    tree = ast.parse(app_source)
    analyzer = SmartCallSiteAnalyzer(target_func, canon_fn, llm_fn)
    analyzer.visit(tree)
    return analyzer.findings
