#!/usr/bin/env python3
import re
import ast
import sys
import textwrap
from datasets import load_dataset

sys.stdout.reconfigure(encoding='utf-8')

def parse_patch_to_files(patch: str):
    file_diffs = re.split(r'(?m)^diff --git ', patch)
    files = {}
    for fd in file_diffs:
        if not fd.strip():
            continue
        m = re.match(r'a/(\S+) b/(\S+)', fd)
        if not m:
            continue
        files[m.group(2)] = fd
    return files

def reconstruct_hunk_slices(file_diff: str):
    """Extract each hunk separately from the file diff."""
    if '--- /dev/null' in file_diff or '+++ /dev/null' in file_diff:
        return []
    
    # Split into hunks by '@@'
    hunk_matches = list(re.finditer(r'(?m)^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)$', file_diff))
    hunks = []
    for i, m in enumerate(hunk_matches):
        start = m.end()
        end = hunk_matches[i+1].start() if i+1 < len(hunk_matches) else len(file_diff)
        hunk_header_info = m.group(5)
        hunk_body = file_diff[start:end]
        
        old_lines, new_lines = [], []
        for line in hunk_body.splitlines():
            if line.startswith('-'):
                old_lines.append(line[1:])
            elif line.startswith('+'):
                new_lines.append(line[1:])
            elif line.startswith(' '):
                old_lines.append(line[1:])
                new_lines.append(line[1:])
        
        hunks.append({
            'header': hunk_header_info,
            'old_text': '\n'.join(old_lines),
            'new_text': '\n'.join(new_lines)
        })
    return hunks

def try_parse_functions(text: str):
    """Attempt to parse functions from text, trying raw and dedented."""
    funcs = {}
    # First try raw
    for src in [text, textwrap.dedent(text)]:
        try:
            tree = ast.parse(src)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # check if node has type annotations
                    funcs[node.name] = (node, ast.unparse(node))
            if funcs:
                return funcs
        except Exception:
            pass
    return funcs

def main():
    ds = load_dataset('nuprl/AgentPack', split='train', streaming=True)
    count = 0
    single_file_py = 0
    hunks_with_funcs = 0
    
    for r in ds:
        count += 1
        if count > 500:
            break
        agent = r.get('agent', '')
        if agent not in ('Claude Code', 'Cursor Agent'):
            continue
        patch = r.get('patch', '')
        files = parse_patch_to_files(patch)
        py_files = [f for f in files if f.endswith('.py') and 'node_modules/' not in f]
        
        if len(files) == 1 and len(py_files) == 1:
            single_file_py += 1
            hunks = reconstruct_hunk_slices(files[py_files[0]])
            for h in hunks:
                old_funcs = try_parse_functions(h['old_text'])
                new_funcs = try_parse_functions(h['new_text'])
                common = [name for name in old_funcs if name in new_funcs and old_funcs[name][1] != new_funcs[name][1]]
                if common:
                    hunks_with_funcs += 1
                    print(f"Record #{count} | {r.get('repo')} @ {r.get('sha')[:8]} | file: {py_files[0]}")
                    print(f"  Changed func: {common} in hunk header: {h['header']}")
                    for c in common:
                        node_old = old_funcs[c][0]
                        has_arg_types = all(arg.annotation is not None for arg in node_old.args.args)
                        has_ret_type = node_old.returns is not None
                        print(f"    Func: {c} | fully typed: {has_arg_types and has_ret_type} (args typed: {has_arg_types}, ret typed: {has_ret_type})")

    print(f"\nTotal scanned: {count} | single-file py: {single_file_py} | hunks with parsable changed funcs: {hunks_with_funcs}")

if __name__ == '__main__':
    main()
