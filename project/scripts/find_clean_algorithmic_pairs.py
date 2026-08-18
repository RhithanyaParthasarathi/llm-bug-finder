#!/usr/bin/env python3
"""
Scan AgentPack specifically for self-contained, typed utility/algorithmic functions.
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
    if len(func_node.args.args) == 0:
        return False
    if func_node.args.args[0].arg in ("self", "cls"):
        return False
    for arg in func_node.args.args:
        if arg.annotation is None:
            return False
    return True


def extract_self_contained(patch: str):
    extracted = extract_file_sources_from_patch(patch)
    if not extracted:
        return None
    file_path, old_source, new_source = extracted

    def parse_file(src):
        for s in [src, textwrap.dedent(src)]:
            try:
                tree = ast.parse(s)
                funcs = {}
                for n in ast.walk(tree):
                    if isinstance(n, ast.FunctionDef) and not (n.args.args and n.args.args[0].arg in ("self", "cls")):
                        funcs[n.name] = (n, ast.unparse(n))
                if funcs:
                    return funcs
            except (SyntaxError, IndentationError):
                pass
        return {}

    old_funcs = parse_file(old_source)
    new_funcs = parse_file(new_source)
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

    import_headers = "from typing import *\nimport re\nimport math\nimport json\nimport logging\nimport os\n\n"
    return {
        "file_path": file_path,
        "function_name": name,
        "old_source": import_headers + old_code,
        "new_source": import_headers + new_code,
    }


def main():
    workdir = "results/agentpack_workdir"
    os.makedirs(workdir, exist_ok=True)
    
    print("Streaming AgentPack from record 120000 to 200000...")
    ds = load_dataset("nuprl/AgentPack", split="train", streaming=True)

    count = 0
    divergences = []

    for r in ds:
        count += 1
        if count <= 120000:
            continue
        if count > 220000:
            break
        if count % 10000 == 0:
            print(f"Scanned {count} records, found {len(divergences)} divergences...", flush=True)

        agent = r.get("agent", "")
        if agent not in ("Claude Code", "Cursor Agent"):
            continue

        patch = r.get("patch", "")
        file_entries = parse_patch_files(patch)
        if not file_entries or len(file_entries) != 1:
            continue

        cand = extract_self_contained(patch)
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

        try:
            res = run_diffbehavior(canon_mod, llm_mod, cand["function_name"], cwd=workdir, per_condition_timeout=8)
            if res.counterexample_found:
                print(f"\n[Record #{count}] Candidate: {task_name}")
                print(f"  --> DIVERGENCE FOUND for {task_name}!")
                print(f"  Raw output:\n{res.raw_output[:400]}")
                divergences.append((task_name, cand, res, r))
                if len(divergences) >= 3:
                    break
        except Exception:
            pass

    print(f"\nFinished. Scanned up to {count}. Divergences found: {len(divergences)}")


if __name__ == "__main__":
    main()
