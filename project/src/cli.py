#!/usr/bin/env python3
"""
LLM-Diff-BugFinder: Automated CLI and PR Review Tool.
Usage:
    python src/cli.py check --old-file <file> --new-file <file> --callers-file <callers.py>
    python src/cli.py benchmark-report
"""
import argparse
import ast
import json
import os
import sys
import tempfile

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.context_synthesizer import extract_all_changed_functions
from src.crosshair_runner import run_diffbehavior
from src.smart_reachability import analyze_reachability


def check_diff(old_file_path: str, new_file_path: str, callers_file: str = ""):
    print(f"\n{'='*70}")
    print(f"LLM-Diff-BugFinder: Checking Diff for Behavioral Regressions")
    print(f"  Old version: {old_file_path}")
    print(f"  New version: {new_file_path}")
    print(f"{'='*70}\n")

    with open(old_file_path, "r", encoding="utf-8") as f:
        old_src = f.read()
    with open(new_file_path, "r", encoding="utf-8") as f:
        new_src = f.read()

    pairs = extract_all_changed_functions(old_src, new_src)
    if not pairs:
        print("[+] No changed functions detected.")
        return

    print(f"[*] Detected {len(pairs)} changed function(s). Running symbolic analysis...\n")

    with tempfile.TemporaryDirectory() as tmpdir:
        for old_synth, new_synth in pairs:
            func_name = old_synth.name
            entry_point = f"{func_name}_wrapper" if old_synth.is_method else func_name

            old_mod_path = os.path.join(tmpdir, f"{func_name}_old.py")
            new_mod_path = os.path.join(tmpdir, f"{func_name}_new.py")

            with open(old_mod_path, "w", encoding="utf-8") as f:
                f.write(old_synth.synthesized_source)
            with open(new_mod_path, "w", encoding="utf-8") as f:
                f.write(new_synth.synthesized_source)

            res = run_diffbehavior(f"{func_name}_old", f"{func_name}_new", entry_point, cwd=tmpdir, per_condition_timeout=10)

            if res.counterexample_found:
                print(f"[!] DIVERGENCE DETECTED in `{func_name}`!")
                print(f"    Counterexample found by SMT solver:")
                for line in res.raw_output.splitlines()[:10]:
                    print(f"      {line}")

                if callers_file and os.path.exists(callers_file):
                    print(f"\n    [+] Analyzing Call-Site Reachability in {callers_file}...")
                    with open(callers_file, "r", encoding="utf-8") as cf:
                        callers_src = cf.read()
                    
                    try:
                        import importlib.util
                        spec_old = importlib.util.spec_from_file_location(f"{func_name}_old", old_mod_path)
                        mod_old = importlib.util.module_from_spec(spec_old)
                        spec_old.loader.exec_module(mod_old)
                        fn_old = getattr(mod_old, entry_point)

                        spec_new = importlib.util.spec_from_file_location(f"{func_name}_new", new_mod_path)
                        mod_new = importlib.util.module_from_spec(spec_new)
                        spec_new.loader.exec_module(mod_new)
                        fn_new = getattr(mod_new, entry_point)

                        findings = analyze_reachability(callers_src, func_name, fn_old, fn_new)
                        print(f"    {'Caller':<20} {'Line':<6} {'Verdict':<20} Detail")
                        print(f"    {'-'*65}")
                        for finding in findings:
                            print(f"    {finding.caller or '<module>':<20} {finding.line:<6} {finding.verdict:<20} {finding.detail}")
                    except Exception as e:
                        print(f"    [!] Error during call-site execution: {e}")
            else:
                print(f"[+] `{func_name}`: No behavioral divergences found (function contract preserved).")


def print_benchmark_report():
    bench_file = os.path.join(PROJECT_ROOT, "results", "benchmark", "benchmark_bugs.json")
    if not os.path.exists(bench_file):
        print(f"[!] No benchmark data found at {bench_file}. Run scripts/harvest_benchmark.py first.")
        return

    with open(bench_file, "r", encoding="utf-8") as f:
        bugs = json.load(f)

    print(f"\n{'='*80}")
    print(f"LLM-Diff-BugFinder: Verified AI Regression Benchmark Suite ({len(bugs)} Bugs)")
    print(f"{'='*80}")
    print(f"{'ID':<4} {'Function':<22} {'Category':<32} {'Source / Repo'}")
    print(f"{'-'*80}")
    for i, b in enumerate(bugs, 1):
        print(f"{i:<4} {b['function_name']:<22} {b['category'][:30]:<32} {b['repo']}")

    print(f"\n[+] Detailed reproduction scripts saved in results/benchmark/")


def main():
    parser = argparse.ArgumentParser(description="LLM-Diff-BugFinder: Behavioral Diff and Reachability CLI")
    subparsers = parser.add_subparsers(dest="command")

    check_parser = subparsers.add_parser("check", help="Check two file versions for behavioral regression")
    check_parser.add_argument("--old-file", required=True)
    check_parser.add_argument("--new-file", required=True)
    check_parser.add_argument("--callers-file", default="")

    subparsers.add_parser("benchmark-report", help="Display verified benchmark bugs report")

    args = parser.parse_args()
    if args.command == "check":
        check_diff(args.old_file, args.new_file, args.callers_file)
    elif args.command == "benchmark-report":
        print_benchmark_report()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
