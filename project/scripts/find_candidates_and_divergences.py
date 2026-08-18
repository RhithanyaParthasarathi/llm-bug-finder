#!/usr/bin/env python3
"""
Stream AgentPack to find single-file, single-function Python candidate pairs,
filter for type annotations per CLAUDE.md constraints, and run CrossHair diffbehavior.
"""
import ast
import os
import re
import sys
import textwrap
from datasets import load_dataset

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from agentpack_loader import is_node_modules_path, parse_patch_files, extract_file_sources_from_patch
from crosshair_runner import run_diffbehavior, run_batch_with_checkpointing

sys.stdout.reconfigure(encoding='utf-8')


def is_fully_typed(func_node: ast.AST) -> bool:
    """Check if function has complete type annotations on all arguments and return type."""
    if not isinstance(func_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return False
    if func_node.returns is None:
        return False
    for arg in func_node.args.args:
        if arg.arg in ("self", "cls"):
            continue
        if arg.annotation is None:
            return False
    for arg in func_node.args.kwonlyargs:
        if arg.annotation is None:
            return False
    for arg in func_node.args.posonlyargs:
        if arg.annotation is None:
            return False
    return True


def extract_candidate_from_patch(patch: str):
    """Extract candidate function pair if exactly one function changed."""
    extracted = extract_file_sources_from_patch(patch)
    if not extracted:
        return None
    file_path, old_source, new_source = extracted

    def get_funcs(src):
        for s in [src, textwrap.dedent(src)]:
            try:
                tree = ast.parse(s)
                funcs = {}
                for n in ast.walk(tree):
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
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

    return {
        "file_path": file_path,
        "function_name": name,
        "old_node": old_node,
        "new_node": new_node,
        "old_source": old_code,
        "new_source": new_code,
        "is_typed": is_fully_typed(old_node) and is_fully_typed(new_node),
    }


def scan(limit=3000, workdir="results/agentpack_workdir", checkpoint="results/agentpack_scan.json"):
    os.makedirs(workdir, exist_ok=True)
    os.makedirs(os.path.dirname(checkpoint), exist_ok=True)

    print(f"Streaming up to {limit} records from nuprl/AgentPack...")
    ds = load_dataset("nuprl/AgentPack", split="train", streaming=True)

    total_scanned = 0
    single_file_py = 0
    single_func_candidates = 0
    typed_candidates = []

    for r in ds:
        total_scanned += 1
        if total_scanned > limit:
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

        cand = extract_candidate_from_patch(patch)
        if not cand:
            continue

        single_func_candidates += 1
        repo_clean = r.get("repo", "unknown").replace("/", "__")
        sha_short = r.get("sha", "")[:8]
        task_name = f"{repo_clean}_{sha_short}_{cand['function_name']}"

        print(f"Found candidate #{single_func_candidates}: {task_name} (typed={cand['is_typed']})")
        
        # Write files
        old_path = os.path.join(workdir, f"{task_name}_old.py")
        new_path = os.path.join(workdir, f"{task_name}_new.py")
        with open(old_path, "w", encoding="utf-8") as f:
            f.write(cand["old_source"])
        with open(new_path, "w", encoding="utf-8") as f:
            f.write(cand["new_source"])

        typed_candidates.append({
            "task_name": task_name,
            "entry_point": cand["function_name"],
            "canon_module": os.path.splitext(os.path.basename(old_path))[0],
            "llm_module": os.path.splitext(os.path.basename(new_path))[0],
            "is_typed": cand["is_typed"],
            "repo": r.get("repo"),
            "sha": r.get("sha"),
            "description": r.get("description"),
            "old_source": cand["old_source"],
            "new_source": cand["new_source"],
        })

    print("\n" + "=" * 70)
    print(f"Scanned: {total_scanned}")
    print(f"Single-file .py commits: {single_file_py} ({(single_file_py/total_scanned)*100:.2f}%)")
    print(f"Single-function candidates: {single_func_candidates} ({(single_func_candidates/single_file_py*100 if single_file_py else 0):.2f}% of single-file)")
    print(f"Fully typed candidates: {sum(1 for c in typed_candidates if c['is_typed'])}")
    print("=" * 70)

    # Run CrossHair on candidates
    tasks_to_run = [
        (c["task_name"], c["entry_point"], c["canon_module"], c["llm_module"])
        for c in typed_candidates
    ]
    if tasks_to_run:
        print(f"\nRunning CrossHair on {len(tasks_to_run)} candidates...")
        results = run_batch_with_checkpointing(tasks_to_run, cwd=workdir, checkpoint_path=checkpoint)
        divs = [r for r in results if r.counterexample_found]
        print(f"\nCompleted: {len(divs)}/{len(results)} showed CrossHair divergences.")


if __name__ == "__main__":
    scan()
