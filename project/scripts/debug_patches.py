#!/usr/bin/env python3
import re
import ast
import sys
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

def reconstruct_versions_from_file_diff(file_diff: str):
    if '--- /dev/null' in file_diff or '+++ /dev/null' in file_diff:
        return 'NEW_OR_DEL', 'NEW_OR_DEL'
    old_lines, new_lines = [], []
    in_hunks = False
    for line in file_diff.splitlines():
        if line.startswith('@@'):
            in_hunks = True
            continue
        if not in_hunks:
            continue
        if line.startswith('-'):
            old_lines.append(line[1:])
        elif line.startswith('+'):
            new_lines.append(line[1:])
        elif line.startswith(' '):
            old_lines.append(line[1:])
            new_lines.append(line[1:])
    return '\n'.join(old_lines), '\n'.join(new_lines)

def main():
    ds = load_dataset('nuprl/AgentPack', split='train', streaming=True)
    count = 0
    for r in ds:
        count += 1
        if count > 200:
            break
        patch = r.get('patch', '')
        files = parse_patch_to_files(patch)
        py_files = [f for f in files if f.endswith('.py') and 'node_modules/' not in f]
        if len(files) == 1 and len(py_files) == 1:
            path = py_files[0]
            fd = files[path]
            old_src, new_src = reconstruct_versions_from_file_diff(fd)
            repo = r.get('repo')
            sha = r.get('sha', '')[:8]
            agent = r.get('agent')
            print(f"\n--- Record #{count} | agent: {agent} | repo: {repo} | sha: {sha} | file: {path} ---")
            if old_src == 'NEW_OR_DEL':
                print('  -> File was newly created or deleted')
            else:
                print(f'  old_src lines: {len(old_src.splitlines())}, new_src lines: {len(new_src.splitlines())}')
                try:
                    otree = ast.parse(old_src)
                    print(f'  ast.parse(old_src): SUCCESS, nodes: {[type(n).__name__ for n in otree.body]}')
                    funcs = [n.name for n in otree.body if isinstance(n, ast.FunctionDef)]
                    print(f'  functions in old_src: {funcs}')
                except Exception as e:
                    print(f'  ast.parse(old_src): FAILED with {type(e).__name__}: {e}')
                    print('  first 5 lines of old_src:\n', '\n'.join(old_src.splitlines()[:5]))

if __name__ == '__main__':
    main()
