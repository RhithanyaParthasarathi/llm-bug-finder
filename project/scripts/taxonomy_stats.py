#!/usr/bin/env python3
"""
Taxonomy Stats Generator
Parses the benchmark dataset and generates statistical breakdowns.
"""
import json
import os
from collections import Counter

def generate_stats():
    benchmark_path = os.path.join(os.path.dirname(__file__), '..', 'results', 'benchmark', 'benchmark_bugs.json')
    
    if not os.path.exists(benchmark_path):
        print(f"Benchmark file not found at {benchmark_path}")
        return

    with open(benchmark_path, 'r', encoding='utf-8') as f:
        bugs = json.load(f)

    total_bugs = len(bugs)
    categories = Counter(b.get("category", "Unknown") for b in bugs)
    agents = Counter(b.get("agent", "Unknown") for b in bugs)
    repos = Counter(b.get("repo", "Unknown") for b in bugs)

    print("="*60)
    print(f"LLM-Diff-BugFinder: Phase 4 Taxonomy Report")
    print("="*60)
    print(f"Total Verified Regressions: {total_bugs}\n")
    
    print("--- Breakdown by Bug Category ---")
    for cat, count in categories.most_common():
        pct = (count / total_bugs) * 100
        print(f"- {cat:<40} : {count:3d} ({pct:4.1f}%)")
        
    print("\n--- Breakdown by Authoring Agent ---")
    for agent, count in agents.most_common():
        pct = (count / total_bugs) * 100
        print(f"- {agent:<40} : {count:3d} ({pct:4.1f}%)")

    print("\n--- Top Impacted Repositories ---")
    for repo, count in repos.most_common(5):
        print(f"- {repo:<40} : {count:3d} bugs")

    print("="*60)

if __name__ == "__main__":
    generate_stats()
