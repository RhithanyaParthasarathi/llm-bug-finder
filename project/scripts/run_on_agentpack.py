#!/usr/bin/env python3
"""
Batch pipeline runner over AgentPack.
Streams records, filters to single-file, single-function Python commits,
and runs CrossHair diffbehavior with checkpointing.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from agentpack_loader import (
    load_agentpack_stream,
    is_single_file_commit,
    extract_file_sources_from_patch,
    extract_single_function_diff,
)
from crosshair_runner import run_batch_with_checkpointing


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=200, help="max commits to scan")
    parser.add_argument("--checkpoint", default="results/agentpack_scan.json")
    parser.add_argument("--workdir", default="results/agentpack_workdir")
    parser.add_argument("--per-condition-timeout", type=int, default=10)
    args = parser.parse_args()

    os.makedirs(args.workdir, exist_ok=True)
    if os.path.dirname(args.checkpoint):
        os.makedirs(os.path.dirname(args.checkpoint), exist_ok=True)

    print(f"Loading AgentPack stream (limit={args.limit})...")
    stream = load_agentpack_stream()

    tasks = []
    seen = 0
    single_file_count = 0
    single_function_count = 0

    for record in stream:
        if seen >= args.limit:
            break
        seen += 1

        if not is_single_file_commit(record):
            continue
        single_file_count += 1

        patch = record.get("patch", "")
        extracted = extract_file_sources_from_patch(patch)
        if not extracted:
            continue
        file_path, old_source, new_source = extracted

        candidates = extract_single_function_diff(old_source, new_source)
        if not candidates:
            continue
        single_function_count += 1

        for c in candidates:
            repo_clean = record.get("repo", "unknown").replace("/", "__")
            sha_short = record.get("sha", "")[:8]
            task_name = f"{repo_clean}_{sha_short}_{c.function_name}"
            old_path = os.path.join(args.workdir, f"{task_name}_old.py")
            new_path = os.path.join(args.workdir, f"{task_name}_new.py")
            with open(old_path, "w", encoding="utf-8") as f:
                f.write(c.old_source)
            with open(new_path, "w", encoding="utf-8") as f:
                f.write(c.new_source)
            tasks.append((
                task_name, c.function_name,
                os.path.splitext(os.path.basename(old_path))[0],
                os.path.splitext(os.path.basename(new_path))[0],
            ))

    print("\n" + "=" * 60)
    print("SANITY BATCH STATS:")
    print(f"  Total scanned:                  {seen}")
    print(f"  Single-file commits:            {single_file_count} ({(single_file_count/seen)*100:.1f}%)")
    print(f"  Single-function candidates:     {single_function_count} ({(single_function_count/seen)*100:.1f}% of total, {(single_function_count/single_file_count*100 if single_file_count else 0):.1f}% of single-file)")
    print(f"  Tasks prepared for CrossHair:   {len(tasks)}")
    print("=" * 60 + "\n")

    if tasks:
        results = run_batch_with_checkpointing(
            tasks,
            cwd=args.workdir,
            checkpoint_path=args.checkpoint,
            per_condition_timeout=args.per_condition_timeout,
        )
        divergences = [r for r in results if r.counterexample_found]
        print(f"\nDone. {len(divergences)}/{len(results)} tasks showed a CrossHair divergence.")
        print(f"Results saved to {args.checkpoint}")
    else:
        print("No tasks generated to run CrossHair on.")


if __name__ == "__main__":
    main()
