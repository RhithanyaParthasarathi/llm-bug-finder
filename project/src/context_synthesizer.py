"""
Context and Stub Synthesizer for Real-World Python Diffs.
Handles:
1. Class methods by synthesizing mock `self` and converting methods to testable callables.
2. Automatic type inference from default values, docstrings, and standard type patterns.
3. Stubbing and mocking external library dependencies.
4. Multi-function diff extraction (evaluating each changed function independently).
"""
import ast
import re
import textwrap
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any


@dataclass
class SynthesizedFunction:
    name: str
    original_source: str
    synthesized_source: str
    is_method: bool
    inferred_types: Dict[str, str]
    return_type: str


# Common mock prelude for isolated symbolic execution
MOCK_PRELUDE = """
import sys
from typing import *
import types
import re
import math
import json
import logging
import os
import hashlib
import datetime

# Universal Auto-Stub for external libraries
class _DynamicMock:
    def __init__(self, *args, **kwargs):
        pass
    def __getattr__(self, name):
        if name.startswith('__') and name.endswith('__'):
            raise AttributeError(name)
        return _DynamicMock()
    def __call__(self, *args, **kwargs):
        return _DynamicMock()
    def __getitem__(self, key):
        return _DynamicMock()
    def __bool__(self):
        return True
    def __str__(self):
        return ""
    def __repr__(self):
        return "<MockObject>"

class MockSelf(_DynamicMock):
    pass
"""


def infer_type_from_default(val_node: ast.AST) -> Optional[str]:
    """Infer Python type annotation from an AST literal default value."""
    if isinstance(val_node, ast.Constant):
        val = val_node.value
        if isinstance(val, bool):
            return "bool"
        elif isinstance(val, int):
            return "int"
        elif isinstance(val, float):
            return "float"
        elif isinstance(val, str):
            return "str"
        elif isinstance(val, bytes):
            return "bytes"
        elif val is None:
            return "Optional[Any]"
    elif isinstance(val_node, ast.List):
        return "List[Any]"
    elif isinstance(val_node, ast.Dict):
        return "Dict[str, Any]"
    elif isinstance(val_node, ast.Set):
        return "Set[Any]"
    elif isinstance(val_node, ast.Tuple):
        return "Tuple[Any, ...]"
    return None


def infer_types_from_docstring(docstring: str) -> Dict[str, str]:
    """Extract type hints from Sphinx/Google style docstrings."""
    types_found = {}
    if not docstring:
        return types_found

    # Sphinx style: :type param_name: int
    for m in re.finditer(r":type\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*([^\n\r]+)", docstring):
        param, type_str = m.group(1).strip(), m.group(2).strip()
        types_found[param] = type_str

    # Google style: param_name (int): description
    for m in re.finditer(r"([a-zA-Z_][a-zA-Z0-9_]*)\s*\(([a-zA-Z0-9_\[\],\s]+)\)\s*:", docstring):
        param, type_str = m.group(1).strip(), m.group(2).strip()
        types_found[param] = type_str

    return types_found


class FunctionTransformer(ast.NodeTransformer):
    """Augments function nodes with inferred type annotations if missing."""
    def __init__(self, docstring_types: Dict[str, str]):
        self.docstring_types = docstring_types
        self.inferred = {}
        self.return_type = "Any"

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        # Determine return type
        if node.returns is None:
            ret_inferred = self.docstring_types.get("return") or "Any"
            node.returns = ast.parse(ret_inferred, mode="eval").body
            self.return_type = ret_inferred
        else:
            self.return_type = ast.unparse(node.returns)

        # Match default arguments from right to left
        defaults = [None] * (len(node.args.args) - len(node.args.defaults)) + list(node.args.defaults)

        for arg, default in zip(node.args.args, defaults):
            if arg.arg in ("self", "cls"):
                continue
            if arg.annotation is None:
                # 1. Try docstring
                inferred = self.docstring_types.get(arg.arg)
                # 2. Try default value
                if not inferred and default is not None:
                    inferred = infer_type_from_default(default)
                # 3. Fallback to basic type based on name heuristic or str/int
                if not inferred:
                    if "count" in arg.arg or "index" in arg.arg or "num" in arg.arg or "len" in arg.arg or "size" in arg.arg or "limit" in arg.arg or "timeout" in arg.arg:
                        inferred = "int"
                    elif "path" in arg.arg or "name" in arg.arg or "text" in arg.arg or "str" in arg.arg or "msg" in arg.arg or "key" in arg.arg or "url" in arg.arg:
                        inferred = "str"
                    elif "is_" in arg.arg or "has_" in arg.arg or "enable" in arg.arg:
                        inferred = "bool"
                    elif "items" in arg.arg or "list" in arg.arg or "elements" in arg.arg:
                        inferred = "List[Any]"
                    elif "data" in arg.arg or "mapping" in arg.arg or "dict" in arg.arg:
                        inferred = "Dict[str, Any]"
                    else:
                        inferred = "str"  # Safe default probe

                self.inferred[arg.arg] = inferred
                node.annotation = ast.parse(inferred, mode="eval").body
                arg.annotation = node.annotation

        return node


def synthesize_function(func_node: ast.AST, enclosing_class: Optional[str] = None) -> SynthesizedFunction:
    """Synthesize a fully-typed, executable standalone test wrapper for a function or method."""
    if not isinstance(func_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        raise ValueError("Expected FunctionDef node")

    func_name = func_node.name
    docstring = ast.get_docstring(func_node) or ""
    docstring_types = infer_types_from_docstring(docstring)

    is_method = bool(func_node.args.args and func_node.args.args[0].arg in ("self", "cls"))
    raw_source = ast.unparse(func_node)

    # Clone AST to avoid mutating original
    cloned_node = ast.parse(raw_source).body[0]
    transformer = FunctionTransformer(docstring_types)
    transformed_node = transformer.visit(cloned_node)

    # Convert async to sync for CrossHair if needed or keep standard
    transformed_code = ast.unparse(transformed_node)

    if is_method:
        # If it's a method, synthesize a wrapper that injects MockSelf
        wrapper_code = f"""
{MOCK_PRELUDE}

{transformed_code}

# Standalone execution wrapper for method {func_name}
def {func_name}_wrapper({', '.join(ast.unparse(a) for a in transformed_node.args.args if a.arg not in ('self', 'cls'))}) -> {transformer.return_type}:
    _self_obj = MockSelf()
    return {func_name}(_self_obj, {', '.join(a.arg for a in transformed_node.args.args if a.arg not in ('self', 'cls'))})
"""
    else:
        wrapper_code = f"""
{MOCK_PRELUDE}

{transformed_code}
"""

    return SynthesizedFunction(
        name=func_name,
        original_source=raw_source,
        synthesized_source=wrapper_code.strip(),
        is_method=is_method,
        inferred_types=transformer.inferred,
        return_type=transformer.return_type,
    )


def extract_all_changed_functions(old_source: str, new_source: str) -> List[Tuple[SynthesizedFunction, SynthesizedFunction]]:
    """Extract ALL changed functions/methods between old and new source, synthesizing stubs for each."""
    def parse_nodes(src: str):
        for candidate in [src, textwrap.dedent(src)]:
            try:
                tree = ast.parse(candidate)
                funcs = {}
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        funcs[node.name] = node
                if funcs:
                    return funcs
            except (SyntaxError, IndentationError):
                pass
        return {}

    old_funcs = parse_nodes(old_source)
    new_funcs = parse_nodes(new_source)

    pairs = []
    for name in old_funcs:
        if name in new_funcs:
            old_unparsed = ast.unparse(old_funcs[name])
            new_unparsed = ast.unparse(new_funcs[name])
            if old_unparsed != new_unparsed:
                try:
                    synth_old = synthesize_function(old_funcs[name])
                    synth_new = synthesize_function(new_funcs[name])
                    pairs.append((synth_old, synth_new))
                except Exception:
                    pass
    return pairs
