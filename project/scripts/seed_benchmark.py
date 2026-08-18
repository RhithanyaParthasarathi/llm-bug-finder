#!/usr/bin/env python3
"""
Seed the benchmark repository with verified real bugs found across AgentPack and HumanEval+.
"""
import json
import os

BENCHMARK_DIR = "results/benchmark"
os.makedirs(BENCHMARK_DIR, exist_ok=True)
BENCHMARK_FILE = os.path.join(BENCHMARK_DIR, "benchmark_bugs.json")

SEED_BUGS = [
    {
        "task_name": "kym6464__clipboard-to-url_89c83dc3_read_csv",
        "repo": "kym6464/clipboard-to-url",
        "sha": "89c83dc3772fe2710385bf56fa1d927a7c1bda86",
        "agent": "Claude Code",
        "function_name": "read_csv",
        "is_method": False,
        "category": "Incorrect edge-case handling / Robustness crash",
        "commit_description": "Enhance CSV validation by enforcing multi-line structure checks.",
        "raw_counterexample": "Given: (value='col1,col2'), raises AssertionError('Expected at least 2 lines for CSV structure')",
        "repro_script": "results/benchmark/repro_kym6464_read_csv.py",
        "verified_input": "user_id,username,email",
        "canonical_behavior": "Returns (b'user_id,username,email', '<hash>.csv')",
        "ai_behavior": "Raises AssertionError('Expected at least 2 lines for CSV structure')"
    },
    {
        "task_name": "alexwday__iris-project_2a072768__process_reference_buffer",
        "repo": "alexwday/iris-project",
        "sha": "2a072768a3560738676bf953716d9e03d368e7b9",
        "agent": "Claude Code",
        "function_name": "_process_reference_buffer",
        "is_method": False,
        "category": "Missing branch logic / Contract change",
        "commit_description": "For streaming: just accumulate chunks without processing references.",
        "raw_counterexample": "Given: (buffer='See [REF:1]\\n\\n', reference_index={'1': {'file_link': 'doc.pdf'}}), returns ('See [REF:1]\\n\\n', '') instead of replacing link.",
        "repro_script": "results/benchmark/repro_alexwday_process_reference_buffer.py",
        "verified_input": "('See [REF:1]\\n\\n', {'1': {'file_link': 'doc.pdf'}})",
        "canonical_behavior": "Replaces [REF:1] with HTML link tag in processed output",
        "ai_behavior": "Returns raw unmodified buffer without replacing link"
    },
    {
        "task_name": "HumanEval_10_make_palindrome",
        "repo": "HumanEval+ / OpenAI completion",
        "sha": "bench_he10",
        "agent": "ChatGPT / Codex",
        "function_name": "make_palindrome",
        "is_method": False,
        "category": "Wrong/suboptimal algorithm",
        "commit_description": "Find shortest palindrome by appending reverse prefix.",
        "raw_counterexample": "Given: (string='ababb'), canon returns 'ababbaba' (len 8), new returns 'ababbbaba' (len 9)",
        "repro_script": "results/benchmark/repro_HumanEval_10.py",
        "verified_input": "ababb",
        "canonical_behavior": "Returns 'ababbaba' (minimal palindrome)",
        "ai_behavior": "Returns 'ababbbaba' (suboptimal non-minimal palindrome)"
    },
    {
        "task_name": "HumanEval_18_how_many_times",
        "repo": "HumanEval+ / OpenAI completion",
        "sha": "bench_he18",
        "agent": "ChatGPT / Codex",
        "function_name": "how_many_times",
        "is_method": False,
        "category": "Incorrect edge-case handling",
        "commit_description": "Count overlapping occurrences of substring.",
        "raw_counterexample": "Given: (string='banana', substring=''), canon returns 6, new returns 0",
        "repro_script": "results/benchmark/repro_HumanEval_18.py",
        "verified_input": "('banana', '')",
        "canonical_behavior": "Returns 6 (matches at each index)",
        "ai_behavior": "Returns 0 (special-case early return for empty string)"
    },
    {
        "task_name": "HumanEval_26_remove_duplicates",
        "repo": "HumanEval+ / OpenAI completion",
        "sha": "bench_he26",
        "agent": "ChatGPT / Codex",
        "function_name": "remove_duplicates",
        "is_method": False,
        "category": "Requirement misunderstanding",
        "commit_description": "Remove duplicate numbers from list while maintaining order.",
        "raw_counterexample": "Given: (numbers=[1, 2, 2, 3]), canon returns [1, 3], new returns [1, 2, 3]",
        "repro_script": "results/benchmark/repro_HumanEval_26.py",
        "verified_input": "[1, 2, 2, 3]",
        "canonical_behavior": "Returns [1, 3] (removes all occurrences of duplicate elements)",
        "ai_behavior": "Returns [1, 2, 3] (preserves first occurrence of duplicate elements)"
    }
]


def seed():
    with open(BENCHMARK_FILE, "w", encoding="utf-8") as f:
        json.dump(SEED_BUGS, f, indent=2)
    print(f"Successfully seeded {len(SEED_BUGS)} verified bugs to {BENCHMARK_FILE}!")


if __name__ == "__main__":
    seed()
