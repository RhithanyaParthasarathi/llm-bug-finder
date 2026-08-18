#!/usr/bin/env python3
"""
Estimate usable single-file, single-function Python candidates from AgentPack,
updated with REAL measured statistics from live scans (2026-08-17).
"""

TOTAL_ITEMS = 1_800_000
CLAUDE_CODE_ITEMS = 1_070_262
CURSOR_AGENT_ITEMS = 186_044
SUPPORTED_ITEMS = CLAUDE_CODE_ITEMS + CURSOR_AGENT_ITEMS  # excluding Codex, see agentpack_loader.py

# From Table 2 in the paper: Python's share of files, by agent
PYTHON_FILE_SHARE = {
    "claude_code": 0.10,
    "cursor_agent": 0.03,
}

# Measured on live AgentPack data (2026-08-17):
# - 200-commit sample: 10.0% single-file Python commits
# - 3,000-commit sample: 6.73% single-file Python commits
# Using 0.08 (~8%) as the empirical representative average.
MEASURED_SINGLE_FILE_FRACTION = 0.08

# Measured on live AgentPack data (2026-08-17):
# - 200-commit sample: 0.0% isolated standalone functions
# - 3,000-commit sample: 2.97% (6/202) single-function candidates
# Using 0.03 (~3%) as the empirical representative fraction.
MEASURED_SINGLE_FUNCTION_FRACTION = 0.03


def estimate():
    claude_py = CLAUDE_CODE_ITEMS * PYTHON_FILE_SHARE["claude_code"]
    cursor_py = CURSOR_AGENT_ITEMS * PYTHON_FILE_SHARE["cursor_agent"]
    python_touching_commits = claude_py + cursor_py

    single_file = python_touching_commits * MEASURED_SINGLE_FILE_FRACTION
    single_function = single_file * MEASURED_SINGLE_FUNCTION_FRACTION

    print(f"Supported items (Claude Code + Cursor Agent, excl. Codex): {SUPPORTED_ITEMS:,}")
    print(f"Estimated Python-file-touching commits:                    {python_touching_commits:,.0f}")
    print(f"Estimated single-file Python commits (MEASURED ~8%):       {single_file:,.0f}")
    print(f"Estimated single-function candidates (MEASURED ~3%):       {single_function:,.0f}")
    print()
    print("COMPARISON WITH PRIOR ASSUMPTION:")
    print("  Prior assumed projection: ~22,522 candidates (~20K)")
    print(f"  Real measured projection: ~{int(single_function):,} candidates")
    print(f"  Conclusion: The original ~20K estimate was WAY OFF (an overestimate by ~80x).")
    print("  Root cause: Real agent commits are overwhelmingly multi-file and rarely")
    print("  isolate to a single standalone top-level function without outer class context.")


if __name__ == "__main__":
    estimate()
