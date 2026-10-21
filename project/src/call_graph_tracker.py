#!/usr/bin/env python3
"""
Inter-procedural Call Graph Tracker
Scans a repository to find all files and lines that call a target function.
"""
import ast
import os
from typing import List, Tuple

class CallVisitor(ast.NodeVisitor):
    def __init__(self, target_func: str):
        self.target_func = target_func
        self.calls = []

    def visit_Call(self, node: ast.Call):
        # Handle direct calls: target_func()
        if isinstance(node.func, ast.Name) and node.func.id == self.target_func:
            self.calls.append(node.lineno)
        # Handle method/module calls: obj.target_func() or module.target_func()
        elif isinstance(node.func, ast.Attribute) and node.func.attr == self.target_func:
            self.calls.append(node.lineno)
        self.generic_visit(node)

def track_calls_in_repo(repo_path: str, target_func: str, exclude_dirs: List[str] = None) -> List[Tuple[str, int]]:
    """
    Returns a list of tuples: (file_path, line_number) where the target_func is called.
    """
    if exclude_dirs is None:
        exclude_dirs = [".git", "__pycache__", "venv", "node_modules", "env"]

    found_calls = []

    for root, dirs, files in os.walk(repo_path):
        # Exclude hidden and virtual environment directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in exclude_dirs]

        for file in files:
            if not file.endswith(".py"):
                continue

            file_path = os.path.join(root, file)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                tree = ast.parse(content)
                visitor = CallVisitor(target_func)
                visitor.visit(tree)
                
                for line in visitor.calls:
                    # Convert to relative path for cleaner output
                    rel_path = os.path.relpath(file_path, repo_path)
                    found_calls.append((rel_path, line))
            except Exception:
                # Skip files that can't be parsed (syntax errors in partial AI edits)
                pass

    return found_calls

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python call_graph_tracker.py <repo_path> <function_name>")
        sys.exit(1)
        
    repo = sys.argv[1]
    func = sys.argv[2]
    
    print(f"Scanning {repo} for calls to '{func}'...")
    calls = track_calls_in_repo(repo, func)
    
    if not calls:
        print(f"No calls found for '{func}'.")
    else:
        print(f"Found {len(calls)} call(s):")
        for path, line in calls:
            print(f"  - {path}:{line}")
