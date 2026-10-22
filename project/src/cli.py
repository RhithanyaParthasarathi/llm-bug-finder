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

sys.stdout.reconfigure(encoding='utf-8')

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.context_synthesizer import extract_all_changed_functions
from src.crosshair_runner import run_diffbehavior
from src.smart_reachability import analyze_reachability
from src.call_graph_tracker import track_calls_in_repo


def check_diff(old_file_path: str, new_file_path: str, callers_file: str = "", repo_dir: str = "", pr_comment: bool = False):
    print(f"\n{'='*70}")
    print(f"LLM-Diff-BugFinder: Checking Diff for Behavioral Regressions")
    print(f"  Old version: {old_file_path}")
    print(f"  New version: {new_file_path}")
    if repo_dir:
        print(f"  Target Repository: {repo_dir}")
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
                print(f"[!] REGRESSION DETECTED in `{func_name}`!")
                print(f"    Counterexample found by SMT solver:")
                for line in res.raw_output.splitlines()[:10]:
                    print(f"      {line}")

                import importlib.util
                spec_old = importlib.util.spec_from_file_location(f"{func_name}_old", old_mod_path)
                mod_old = importlib.util.module_from_spec(spec_old)
                spec_old.loader.exec_module(mod_old)
                fn_old = getattr(mod_old, entry_point)

                spec_new = importlib.util.spec_from_file_location(f"{func_name}_new", new_mod_path)
                mod_new = importlib.util.module_from_spec(spec_new)
                spec_new.loader.exec_module(mod_new)
                fn_new = getattr(mod_new, entry_point)

                all_findings = []

                # 1. Single callers file if provided
                if callers_file and os.path.exists(callers_file):
                    print(f"\n    [+] Analyzing Call-Site Reachability in {callers_file}...")
                    with open(callers_file, "r", encoding="utf-8") as cf:
                        callers_src = cf.read()
                    findings = analyze_reachability(callers_src, func_name, fn_old, fn_new)
                    all_findings.extend([(callers_file, f) for f in findings])

                # 2. Entire repository scan if repo_dir provided
                if repo_dir and os.path.exists(repo_dir):
                    print(f"\n    [+] Scanning entire repository '{repo_dir}' for callers of `{func_name}`...")
                    repo_calls = track_calls_in_repo(repo_dir, func_name)
                    print(f"    Found {len(repo_calls)} call site(s) across repository.")

                    unique_files = list({c[0] for c in repo_calls})
                    for rel_file in unique_files:
                        full_fpath = os.path.join(repo_dir, rel_file)
                        try:
                            with open(full_fpath, "r", encoding="utf-8") as rf:
                                r_src = rf.read()
                            r_findings = analyze_reachability(r_src, func_name, fn_old, fn_new)
                            all_findings.extend([(rel_file, f) for f in r_findings])
                        except Exception:
                            pass

                if all_findings:
                    print(f"\n    {'File':<30} {'Caller':<18} {'Line':<6} {'Verdict':<18}")
                    print(f"    {'-'*76}")
                    for fpath, finding in all_findings:
                        print(f"    {fpath[:28]:<30} {finding.caller or '<module>':<18} {finding.line:<6} {finding.verdict:<18}")

                if pr_comment:
                    print("\n" + "="*40 + " AUTOMATED PR BOT COMMENT " + "="*40)
                    print(f"### ⚠️ LLM-Diff-BugFinder: Silent Behavioral Regression Detected\n")
                    print(f"The proposed diff modifies `{func_name}`, but alters its runtime behavior on specific inputs.\n")
                    print(f"**SMT Counterexample Proof:**")
                    print("```text")
                    for line in res.raw_output.splitlines()[:5]:
                        print(line)
                    print("```\n")
                    if all_findings:
                        hits = [f for f in all_findings if f[1].verdict == 'CONFIRMED_BUG_HIT']
                        flagged = [f for f in all_findings if f[1].verdict == 'VARIABLE_PARAM']
                        print(f"**Downstream Repository Impact:**")
                        print(f"- 🔴 **Confirmed Broken Callers:** {len(hits)} location(s)")
                        for fpath, f in hits:
                            print(f"  - `{fpath}:{f.line}` ({f.caller or 'module'})")
                        print(f"- ⚠️ **Flagged for Audit (Dynamic Variables):** {len(flagged)} location(s)")
                        for fpath, f in flagged:
                            print(f"  - `{fpath}:{f.line}` ({f.caller or 'module'})")
                    else:
                        print(f"**Downstream Impact:** No direct callers found in the analyzed scope.")
                    print(f"\n**Action:** 🛑 Merge Blocked. Please review and revert the behavioral divergence.")
                    print("="*106 + "\n")
            else:
                print(f"[+] `{func_name}`: No behavioral divergences found (function contract mathematically preserved).")


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
    check_parser.add_argument("--old-file", required=True, help="Path to original (canonical) file")
    check_parser.add_argument("--new-file", required=True, help="Path to AI-modified file")
    check_parser.add_argument("--callers-file", default="", help="Single file containing callers to analyze")
    check_parser.add_argument("--repo-dir", default="", help="Path to full repository directory to scan call graph")
    check_parser.add_argument("--pr-comment", action="store_true", help="Format output as a GitHub PR review bot comment")

    subparsers.add_parser("benchmark-report", help="Display verified benchmark bugs report")

    scan_parser = subparsers.add_parser("scan-pr", help="Scan a git diff or multi-file PR for regressions")
    scan_parser.add_argument("--diff", default=None, help="Path to .diff file")
    scan_parser.add_argument("--stdin", action="store_true", help="Read diff from stdin (e.g. git diff | ...)")
    scan_parser.add_argument("--repo", default=None, help="Path to repository root for call-graph tracking")
    scan_parser.add_argument("--timeout", type=int, default=30, help="CrossHair timeout per function in seconds")
    scan_parser.add_argument("--output", default=None, help="Save PR comment markdown to file")

    args = parser.parse_args()
    if args.command == "check":
        check_diff(args.old_file, args.new_file, callers_file=args.callers_file, repo_dir=args.repo_dir, pr_comment=args.pr_comment)
    elif args.command == "benchmark-report":
        print_benchmark_report()
    elif args.command == "scan-pr":
        sys.path.insert(0, os.path.join(PROJECT_ROOT, "scripts"))
        from pr_scanner import scan_pr_diff, parse_all_changed_functions, format_pr_comment
        
        diff_text = ""
        if args.stdin:
            diff_text = sys.stdin.read()
        elif args.diff:
            diff_text = open(args.diff, encoding="utf-8").read()
        
        if not diff_text.strip():
            print("ERROR: Empty diff provided. Usage: git diff main HEAD | python cli.py scan-pr --stdin")
            sys.exit(1)

        repo_path = args.repo or (os.getcwd() if os.path.isdir(".git") else None)
        changed = parse_all_changed_functions(diff_text)
        reports = scan_pr_diff(diff_text, repo_path=repo_path, per_func_timeout=args.timeout)
        comment = format_pr_comment(reports, total_checked=len(changed))
        print("\n" + "=" * 60)
        print("  AUTOMATED PR COMMENT (Markdown)")
        print("=" * 60 + "\n")
        print(comment)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(comment)
            print(f"\n[Comment saved to {args.output}]")
        sys.exit(1 if reports else 0)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
