# LLM-Diff-BugFinder: Final Project Runbook & Deployment Guide

This document defines the **end goal**, the **final demonstration procedures**, and how **any external repository** can install and execute LLM-Diff-BugFinder in automated CI/CD pipelines.

---

## 🎯 1. The End Goal of the Project

**LLM-Diff-BugFinder** is an automated, formal verification gatekeeper for AI-generated code.

### The Problem It Solves:
When AI coding agents (Claude Code, GitHub Copilot, Cursor) modify existing code:
1. The code almost always passes linters (`mypy`, `pylint`) and syntax checks (**over 91% miss rate**).
2. Human developers reviewing pull requests cannot catch subtle boundary or branch logic regressions.
3. Buggy code gets merged into production `main` branches.

### The Solution:
LLM-Diff-BugFinder automatically intercepts Pull Requests, compares the code before and after the AI edit using differential symbolic execution (**Z3 SMT solver**), verifies if the bug is reachable by downstream callers via **constant propagation**, posts a proof comment on the GitHub PR, and **blocks the merge button** if a regression is proven.

---

## 🚀 2. The Final Demo: Two Ways to Present

### Option A: The Instant Simulation & Browser Preview (Recommended for Presentations)
This requires zero internet connection and demonstrates the entire lifecycle in 15 seconds:

```powershell
python project/scripts/demo_pr_simulation.py
```

**What it does:**
1. Simulates an AI-authored Pull Request modifying `read_csv`.
2. Runs the Z3 SMT solver live on the ASTs to find the divergence.
3. Performs reachability analysis on downstream callers.
4. Generates a **pixel-perfect HTML replica of the GitHub PR page** at:
   `project/scratch/github_pr_preview.html`
5. **Open `github_pr_preview.html` in your browser** to show the panel the exact GitHub Pull Request UI:
   - The `github-actions[bot]` review comment with the SMT proof witness.
   - The failed CI check status.
   - The disabled **"Squash and merge (Blocked by failed check)"** button.

---

### Option B: Real Live GitHub Pull Request
To show a real PR on GitHub.com:

1. **Commit and push** the current repo to GitHub:
   ```bash
   git add .
   git commit -m "feat: complete LLM-Diff-BugFinder CI bot and packaging"
   git push origin main
   ```
2. **Create a demo branch with a bug:**
   ```bash
   git checkout -b demo/ai-refactor
   ```
3. Edit any function (e.g. in `tests/test_context_synthesizer.py` or a sample file, change `> 0` to `>= 2`).
4. Commit and push the branch:
   ```bash
   git commit -am "AI refactor"
   git push origin demo/ai-refactor
   ```
5. Open a Pull Request from `demo/ai-refactor` to `main` on GitHub.
6. Under the PR **Checks** tab, watch GitHub Actions run and automatically post the review comment blocking the merge!

---

## 📦 3. How Other Repositories Use This Tool

Any developer or enterprise repository can integrate LLM-Diff-BugFinder in **one of three ways**:

### Method 1: Drop-In GitHub Action (Zero Installation)
In any target Python repository, create `.github/workflows/bugfinder.yml`:

```yaml
name: Behavioral Regression Check
on:
  pull_request:
    paths: ["**.py"]

permissions:
  contents: read
  pull-requests: write

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: RhithanyaParthasarathi/llm-bug-finder@main
```

### Method 2: The Self-Contained Workflow File
Copy [.github/workflows/llm-bugfinder.yml](file:///c:/Users/rhith/Downloads/llm-diff-bugfinder/.github/workflows/llm-bugfinder.yml) into the target repository. It installs `crosshair-tool` and `z3-solver` and runs `pr_scanner.py` on the PR diff.

### Method 3: Local CLI & Pre-Commit Hook
Developers can run it locally on their machines before pushing:

```powershell
# Install the package locally:
pip install .

# Check any two file versions:
python cli.py check --old-file old.py --new-file new.py --pr-comment

# Or pipe any git diff directly:
git diff main HEAD | python cli.py scan-pr --stdin
```

---

## 📊 4. Core Evidence Reference Table

| Evidence ID | Description | Terminal Command |
| :--- | :--- | :--- |
| **E1** | Environment & Package Versions | `python project/scripts/generate_evidence.py E1` |
| **E2** | Authenticated AgentPack Streaming | `python project/scripts/generate_evidence.py E2` |
| **E3** | Module Directory Listing | `python project/scripts/generate_evidence.py E3` |
| **E4** | Automated Test Suite (`pytest`) | `python project/scripts/generate_evidence.py E4` |
| **E5** | Benchmark Suite Audit (101 bugs) | `python project/scripts/generate_evidence.py E5` |
| **E6** | Pipeline Funnel Summary (20.6% yield) | `python project/scripts/generate_evidence.py E6` |
| **E7** | Baseline Evaluation (mypy/pylint >91% miss) | `python project/scripts/generate_evidence.py E7` |
| **E8** | Reachability Verdict Counts (62/26/44) | `python project/scripts/generate_evidence.py E8` |
| **E9** | Independent Audit (0 false-safes) | `python project/scripts/generate_evidence.py E9` |
| **E10** | Constant Propagation Ablation (+31 lift) | `python project/scripts/generate_evidence.py E10` |
| **E11** | End-to-End Bug Counterexample Proof | `python project/scripts/generate_evidence.py E11` |
| **E12** | CLI Diff Check & Benchmark Report | `python project/scripts/generate_evidence.py E12` |
| **E13** | Simulated PR Bot Run | `python project/scripts/generate_evidence.py E13` |
| **E14** | GitHub Actions Workflow Integration | `python project/scripts/generate_evidence.py E14` |
