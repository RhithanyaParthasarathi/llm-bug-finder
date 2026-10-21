#!/usr/bin/env python3
"""
Minimize Counterexamples
Parses the benchmark JSON and simplifies the raw SMT output.
"""
import json
import os
import re

def minimize_counterexamples():
    benchmark_path = os.path.join(os.path.dirname(__file__), '..', 'results', 'benchmark', 'benchmark_bugs.json')
    
    if not os.path.exists(benchmark_path):
        print(f"Benchmark file not found at {benchmark_path}")
        return

    with open(benchmark_path, 'r', encoding='utf-8') as f:
        bugs = json.load(f)

    minimized_count = 0
    for bug in bugs:
        raw = bug.get("raw_counterexample", "")
        if not raw:
            continue
            
        # Parse Given: (args...)
        given_match = re.search(r'Given: (\(.*?\)),', raw)
        args = given_match.group(1) if given_match else "Unknown args"
        
        # Parse old result
        old_match = re.search(r'_old\.[^\s]+\s*:\s*(.*)', raw)
        old_res = old_match.group(1).strip() if old_match else "Unknown"
        
        # Parse new result
        new_match = re.search(r'_new\.[^\s]+\s*:\s*(.*)', raw)
        new_res = new_match.group(1).strip() if new_match else "Unknown"
        
        minimized = f"Args: {args}\n- Old Code: {old_res}\n- New Code: {new_res}"
        bug["minimized_counterexample"] = minimized
        minimized_count += 1

    with open(benchmark_path, 'w', encoding='utf-8') as f:
        json.dump(bugs, f, indent=2)

    print(f"Successfully minimized counterexamples for {minimized_count} bugs.")

if __name__ == "__main__":
    minimize_counterexamples()
