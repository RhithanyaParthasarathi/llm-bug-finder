#!/usr/bin/env python3
"""
Stream AgentPack from record 15000 onwards to find more typed candidate pairs
and discover CrossHair divergences.
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
    if not isinstance(func_node, ast.FunctionDef):
        return False
    if func_node.returns is None:
        return False
    if len(func_node.args.args) > 0 and func_node.args.args[0].arg in ("self", "cls"):
        return False
    for arg in func_node.args.args:
        if arg.annotation is None:
            return False
    for arg in func_node.args.kwonlyargs:
        if arg.annotation is None:
            return False
    return True


def extract_candidate_with_imports(patch: str):
    extracted = extract_file_sources_from_patch(patch)
    if not extracted:
        return None
    file_path, old_source, new_source = extracted

    def parse_file(src):
        for s in [src, textwrap.dedent(src)]:
            try:
                tree = ast.parse(s)
                imports = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
                funcs = {}
                for n in ast.walk(tree):
                    if isinstance(n, ast.FunctionDef) and not (n.args.args and n.args.args[0].arg in ("self", "cls")):
                        funcs[n.name] = (n, ast.unparse(n))
                if funcs:
                    return imports, funcs
            except (SyntaxError, IndentationError):
                pass
        return [], {}

    old_imports, old_funcs = parse_file(old_source)
    new_imports, new_funcs = parse_file(new_source)

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

    # Include typing/math imports if present
    import_headers = "from typing import *\nimport re\nimport math\nimport json\n\n"

    return {
        "file_path": file_path,
        "function_name": name,
        "old_source": import_headers + old_code,
        "new_source": import_headers + new_code,
    }


def main():
    workdir = "results/agentpack_workdir"
    os.makedirs(workdir, exist_ok=True)
    
    print("Streaming AgentPack from record 15000 to 50000...")
    ds = load_dataset("nuprl/AgentPack", split="train", streaming=True)

    count = 0
    divergences = []

    for r in ds:
        count += 1
        if count <= 15000:
            continue
        if count > 45000:
            break
        if count % 5000 == 0:
            print(f"Scanned {count} records, found {len(divergences)} divergences so far...", flush=True)

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

        cand = extract_candidate_with_imports(patch)
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

        print(f"\n[Record #{count}] Candidate: {task_name}")
        try:
            res = run_diffbehavior(canon_mod, llm_mod, cand["function_name"], cwd=workdir, per_condition_timeout=10)
            if res.counterexample_found:
                print(f"  --> DIVERGENCE FOUND for {task_name}!")
                print(f"  Raw output:\n{res.raw_output}")
                divergences.append((task_name, cand, res, r))
                if len(divergences) >= 4:
                    print("Found 4+ divergences! Stopping scan.")
                    break
            else:
                print("  No divergence.")
        except Exception as e:
            print(f"  Error: {e}")

    print(f"\nCompleted scan up to record {count}. Total divergences found: {len(divergences)}")


if __name__ == "__main__":
    main()
