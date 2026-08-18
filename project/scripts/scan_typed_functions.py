#!/usr/bin/env python3
"""
Stream AgentPack to find fully-typed, isolable, standalone functions,
and run CrossHair diffbehavior on them.
"""
import ast
import os
import re
import sys
import textwrap
from datasets import load_dataset

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from agentpack_loader import is_node_modules_path, parse_patch_files, extract_file_sources_from_patch
from crosshair_runner import run_diffbehavior

sys.stdout.reconfigure(encoding='utf-8')


def is_fully_typed_standalone(func_node: ast.AST) -> bool:
    """Check if function is a standalone top-level function with full type annotations."""
    if not isinstance(func_node, ast.FunctionDef):
        return False
    if func_node.returns is None:
        return False
    if len(func_node.args.args) == 0:
        # no args function
        return True
    # If first arg is self/cls, not a standalone function
    if func_node.args.args[0].arg in ("self", "cls"):
        return False
    for arg in func_node.args.args:
        if arg.annotation is None:
            return False
    for arg in func_node.args.kwonlyargs:
        if arg.annotation is None:
            return False
    return True


def try_extract_standalone_candidate(patch: str):
    extracted = extract_file_sources_from_patch(patch)
    if not extracted:
        return None
    file_path, old_source, new_source = extracted

    def get_funcs(src):
        for s in [src, textwrap.dedent(src)]:
            try:
                tree = ast.parse(s)
                funcs = {}
                for n in tree.body:  # top-level nodes in hunk
                    if isinstance(n, ast.FunctionDef):
                        funcs[n.name] = (n, ast.unparse(n))
                if funcs:
                    return funcs
            except (SyntaxError, IndentationError):
                pass
        return {}

    old_funcs = get_funcs(old_source)
    new_funcs = get_funcs(new_source)
    if not old_funcs or not new_funcs:
        return None

    changed = [
        name for name in old_funcs
        if name in new_funcs and old_funcs[name][1] != new_funcs[name][1]
    ]
    if len(changed) != 1:
        return None

    name = changed[0]
    old_node, old_code = old_funcs[name]
    new_node, new_code = new_funcs[name]

    if not is_fully_typed_standalone(old_node) or not is_fully_typed_standalone(new_node):
        return None

    return {
        "file_path": file_path,
        "function_name": name,
        "old_source": old_code,
        "new_source": new_code,
    }


def main():
    workdir = "results/agentpack_workdir"
    os.makedirs(workdir, exist_ok=True)
    
    print("Streaming AgentPack to find typed candidates...")
    ds = load_dataset("nuprl/AgentPack", split="train", streaming=True)

    count = 0
    single_file_py = 0
    candidates = []

    for r in ds:
        count += 1
        if count % 1000 == 0:
            print(f"Scanned {count} records, found {len(candidates)} typed candidates so far...", flush=True)
        if count > 15000:
            break

        agent = r.get("agent", "")
        if agent not in ("Claude Code", "Cursor Agent"):
            continue

        patch = r.get("patch", "")
        file_entries = parse_patch_files(patch)
        if not file_entries:
            continue

        valid = [
            f for f in file_entries
            if not is_node_modules_path(f[0]) and not is_node_modules_path(f[1])
        ]
        if len(valid) != 1:
            continue
        old_p, new_p, is_new, is_del = valid[0]
        target = new_p if not is_del else old_p
        if not target.endswith(".py") or is_new or is_del:
            continue

        single_file_py += 1

        cand = try_extract_standalone_candidate(patch)
        if not cand:
            continue

        repo_clean = r.get("repo", "unknown").replace("/", "__")
        sha_short = r.get("sha", "")[:8]
        task_name = f"{repo_clean}_{sha_short}_{cand['function_name']}"

        old_path = os.path.join(workdir, f"{task_name}_old.py")
        new_path = os.path.join(workdir, f"{task_name}_new.py")
        with open(old_path, "w", encoding="utf-8") as f:
            f.write(cand["old_source"])
        with open(new_path, "w", encoding="utf-8") as f:
            f.write(cand["new_source"])

        canon_mod = os.path.splitext(os.path.basename(old_path))[0]
        llm_mod = os.path.splitext(os.path.basename(new_path))[0]

        # Test with CrossHair immediately
        print(f"\n[Record #{count}] Testing candidate: {task_name}...")
        try:
            res = run_diffbehavior(canon_mod, llm_mod, cand["function_name"], cwd=workdir, per_condition_timeout=10)
            print(f"  Result: counterexample={res.counterexample_found}")
            if res.raw_output:
                print(f"  Output:\n{res.raw_output[:400]}")
            candidates.append((task_name, cand, res))
        except Exception as e:
            print(f"  CrossHair failed with error: {e}")

    print(f"\nDone. Scanned {count} records | Single-file .py: {single_file_py} | Typed candidates: {len(candidates)}")
    divs = [c for c in candidates if c[2].counterexample_found]
    print(f"Divergences found: {len(divs)}")


if __name__ == "__main__":
    main()
