"""
Tests for Context Synthesizer (Class Methods, Type Inference, Stub Generation).
"""
import ast
import tempfile
import os
import subprocess
import sys
from src.context_synthesizer import (
    synthesize_function,
    extract_all_changed_functions,
    infer_type_from_default,
    infer_types_from_docstring,
)
from src.crosshair_runner import run_diffbehavior


def test_type_inference_from_defaults():
    src = "def process(count=10, name='test', flag=False): pass"
    node = ast.parse(src).body[0]
    synth = synthesize_function(node)
    assert synth.inferred_types["count"] == "int"
    assert synth.inferred_types["name"] == "str"
    assert synth.inferred_types["flag"] == "bool"


def test_method_synthesis_with_mock_self():
    method_src = """
class MyService:
    def format_message(self, user_id: int, message: str) -> str:
        prefix = self.config.get_prefix()
        return f"{prefix} [{user_id}]: {message}"
"""
    node = ast.parse(method_src).body[0].body[0]
    synth = synthesize_function(node)
    assert synth.is_method is True
    assert "def format_message_wrapper(user_id: int, message: str) -> str:" in synth.synthesized_source
    assert "_self_obj = MockSelf()" in synth.synthesized_source


def test_multi_function_extraction_and_crosshair():
    old_file = """
def add_one(x: int) -> int:
    return x + 1

def multiply(a: int, b: int) -> int:
    return a * b
"""
    new_file = """
def add_one(x: int) -> int:
    return x + 2  # Bug: changed behavior

def multiply(a: int, b: int) -> int:
    return a * b  # Unchanged
"""
    pairs = extract_all_changed_functions(old_file, new_file)
    assert len(pairs) == 1
    old_synth, new_synth = pairs[0]
    assert old_synth.name == "add_one"

    # Test running CrossHair on synthesized code
    with tempfile.TemporaryDirectory() as tmpdir:
        old_path = os.path.join(tmpdir, "old_mod.py")
        new_path = os.path.join(tmpdir, "new_mod.py")
        with open(old_path, "w") as f:
            f.write(old_synth.synthesized_source)
        with open(new_path, "w") as f:
            f.write(new_synth.synthesized_source)

        res = run_diffbehavior("old_mod", "new_mod", "add_one", cwd=tmpdir, per_condition_timeout=5)
        assert res.counterexample_found is True
