#!/usr/bin/env python3
"""
Run the full pipeline (detect -> filter) on one manually-supplied
before/after function pair. Useful for testing before running at scale.

Example:
    python scripts/run_on_single_commit.py \\
        --old results/taxonomy_scan/HumanEval_119_canon.py \\
        --new results/taxonomy_scan/HumanEval_119_llm.py \\
        --entry match_parens \\
        --callers path/to/app.py
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from crosshair_runner import run_diffbehavior
from reachability_filter import load_function, analyze, print_report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--old", required=True, help="path to old/canonical version .py file")
    parser.add_argument("--new", required=True, help="path to new/LLM-generated version .py file")
    parser.add_argument("--entry", required=True, help="function name to compare")
    parser.add_argument("--callers", required=False, help="path to a .py file with call sites to filter")
    args = parser.parse_args()

    old_dir = os.path.dirname(os.path.abspath(args.old))
    old_mod = os.path.splitext(os.path.basename(args.old))[0]
    new_mod = os.path.splitext(os.path.basename(args.new))[0]

    print(f"Running crosshair diffbehavior on {old_mod}.{args.entry} vs {new_mod}.{args.entry} ...")
    result = run_diffbehavior(old_mod, new_mod, args.entry, cwd=old_dir)

    if not result.counterexample_found:
        print("No divergence found (within the search budget). Nothing to filter.")
        return

    print(result.raw_output)

    if args.callers:
        canon_fn = load_function(args.old, f"{old_mod}_canon", args.entry)
        llm_fn = load_function(args.new, f"{new_mod}_llm", args.entry)
        findings = analyze(args.callers, args.entry, canon_fn, llm_fn)
        print_report(f"{args.entry}: caller reachability", findings)


if __name__ == "__main__":
    main()
