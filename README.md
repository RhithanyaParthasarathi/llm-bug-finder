# LLM-Diff-BugFinder 🔍

> **Automated Detection and Reachability Analysis of Silent Behavioral Regressions in AI-Generated Code Diffs using Differential Symbolic Execution.**

---

## 📌 Overview

AI coding assistants (such as **Claude Code**, **Cursor Agent**, and **GitHub Copilot**) generate billions of lines of code modifications daily. However, their code changes frequently introduce **silent, non-crashing behavioral regressions** that evade static linters, type checkers, and traditional code review.

**LLM-Diff-BugFinder** provides a mathematically sound, hallucination-free pipeline that:
1. **Detects Behavioral Divergences:** Uses the Z3 SMT solver via **CrossHair** to explore execution paths symbolically and solve for exact concrete inputs where the AI's version breaks the original function contract.
2. **Synthesizes Context & Stubs:** Supports class methods (`MockSelf`), docstring/default-based type inference, and external library dependency mocking.
3. **Smart Reachability Analysis:** Performs intra-procedural constant propagation across the codebase AST to prove which downstream callers are broken (**`CONFIRMED_BUG_HIT`**) vs. unaffected (**`CONCRETE_SAFE`**) with zero AI hallucination.
4. **Mined Benchmark Suite:** Includes a curated benchmark of **101 verified, reproducible real-world AI bugs** harvested from **100,000 commits** in the **AgentPack** dataset across 57 repositories.
5. **GitHub Actions CI/CD Bot:** Packaged as a drop-in reusable composite Action (`action.yml`) that scans incoming pull requests, posts automated witness proof comments, and blocks merging on confirmed regressions.

---

## 🏗️ Architecture

```
                      ┌────────────────────────────────────────┐
                      │             INPUT CODE DIFF            │
                      │  (Git Commit / GitHub PR / AgentPack)  │
                      └──────────────────┬─────────────────────┘
                                         │
                                         ▼
                      ┌────────────────────────────────────────┐
                      │   Context & Stub Synthesizer           │
                      │  - Class Method Isolation (MockSelf)   │
                      │  - Automatic Type Inference            │
                      │  - External Module Auto-Mocking        │
                      └──────────────────┬─────────────────────┘
                                         │
                                         ▼
                      ┌────────────────────────────────────────┐
                      │       PART 1: CrossHair Runner         │
                      │      (Symbolic Execution & Z3)         │
                      │   Finds x such that Old(x) != New(x)   │
                      │     * Checkpoint Resumption Store *    │
                      └──────────────────┬─────────────────────┘
                                         │
                          ┌──────────────┴──────────────┐
                          │                             │
                   [No Divergence]              [Divergence Found]
                          │                             │
                          ▼                             ▼
                  Marked Preserved            ┌────────────────────────────────────┐
                                              │   PART 2: Smart Reachability       │
                                              │   (Constant Propagation + AST)     │
                                              └─────────────────┬──────────────────┘
                                                                │
                                        ┌───────────────────────┼──────────────────────┐
                                        ▼                       ▼                      ▼
                               [CONFIRMED_BUG_HIT]       [CONCRETE_SAFE]        [VARIABLE_PARAM]
                              (Literal/Const Breaks)  (Literal/Const Agrees) (Dynamic Call Site)
                                        │                       │                      │
                                        ▼                       ▼                      ▼
                                 Direct Blocker         Proven Harmless        Flagged for Audit
```

---

## ⚙️ Setup and Prerequisites

### 1. Environment Setup

```bash
# 1. Clone repository
git clone https://github.com/your-org/llm-diff-bugfinder.git
cd llm-diff-bugfinder

# 2. Create and activate virtual environment
python -m venv .venv

# On Windows PowerShell:
.venv\Scripts\activate

# On Linux / macOS:
source .venv/bin/activate

# 3. Install dependencies
pip install -r project/requirements.txt
```

---

### 2. Hugging Face Gated Dataset Setup (For Batch Harvesting)

`nuprl/AgentPack` is a gated dataset on Hugging Face (1.8M commits, 371 GB). To stream commits directly from the dataset without downloading the 371 GB:

1. **Accept Terms:** Visit [huggingface.co/datasets/nuprl/AgentPack](https://huggingface.co/datasets/nuprl/AgentPack) in your browser while logged into your Hugging Face account and click **"Accept Terms" / "Access Repository"**.
2. **Generate Token:** Go to [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) and create a **Read-Only** Access Token.
3. **Authenticate Locally:**
   ```bash
   huggingface-cli login
   ```
   *(Or on Windows PowerShell, save token to your local cache)*:
   ```powershell
   New-Item -ItemType Directory -Force -Path "$HOME\.cache\huggingface" | Out-Null
   Set-Content -Path "$HOME\.cache\huggingface\token" -Value "YOUR_HF_TOKEN_HERE" -NoNewline
   ```

> [!NOTE]
> **Security Notice:** Your Hugging Face token is stored securely in your user home cache (`~/.cache/huggingface/token`) outside this Git repository and will **never** be committed to GitHub.

---

## 🚀 Complete Command Reference

Here are all the commands to run every part of the system:

### 1. View the 101-Bug Benchmark Report
Display the formatted summary table of all 101 verified real-world AI regressions:
```bash
python cli.py benchmark-report
```

---

### 2. Scan a Pull Request or Git Diff
Scan an entire git commit or PR diff with AST call-graph reachability:
```bash
# Scan git diff directly from working branch against main:
git diff main...HEAD | python cli.py scan-pr --stdin --repo .

# Or scan a saved unified diff file:
python cli.py scan-pr --diff pr.diff --repo . --output pr_comment.md
```

---

### 3. Check a Function Diff for Regressions
Run differential symbolic execution and call-site reachability on two file versions:
```bash
# Basic check:
python cli.py check \
  --old-file project/results/agentpack_workdir/kym6464__clipboard-to-url_89c83dc3_read_csv_old.py \
  --new-file project/results/agentpack_workdir/kym6464__clipboard-to-url_89c83dc3_read_csv_new.py

# Check with caller reachability analysis:
python cli.py check \
  --old-file project/results/agentpack_workdir/kym6464__clipboard-to-url_89c83dc3_read_csv_old.py \
  --new-file project/results/agentpack_workdir/kym6464__clipboard-to-url_89c83dc3_read_csv_new.py \
  --callers-file path/to/callers_app.py
```

---

### 4. Run Interactive PR Simulation & Browser Demo
Simulate a full GitHub Pull Request scan and open the interactive review preview in your browser:
```bash
python project/scripts/demo_pr_simulation.py
```

---

### 5. Generate Evidence Items E1 to E14
Run any individual evidence generator or all at once:
```bash
python project/scripts/generate_evidence.py ALL
# Or individual items: python project/scripts/generate_evidence.py E1
```

---

### 6. Run the Automated Unit Test Suite
Execute the entire test suite (verifying checkpointing, context synthesis, and constant propagation):
```bash
python -m pytest
```

---

## 🤖 Reusable GitHub Action Integration

Any external repository can add LLM-Diff-BugFinder as a mandatory merge blocker by adding `.github/workflows/bugfinder.yml`:

```yaml
name: Z3 Differential Regression Gatekeeper
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

---

## 📊 Benchmark Suite Results

Across **100,001 scanned commits** from the `nuprl/AgentPack` dataset, the pipeline discovered and verified **101 reproducible real-world AI bugs** across **57 repositories**:
- **85 Concrete Counterexamples:** Exact input witnesses generated where `Old(x) != New(x)`
- **16 Path Divergences:** Execution branches terminated or modified unexpectedly

Furthermore, the **132-Call-Site Reachability Benchmark** proved:
- **62 CONFIRMED_BUG_HIT:** Call sites broken at runtime with constant inputs (Direct Blockers)
- **26 CONCRETE_SAFE:** Call sites mathematically unaffected despite the function change
- **44 VARIABLE_PARAM:** Dynamic calls flagged for prioritized human review
- **0 False-Safe Violations:** 100% mathematical soundness guarantee

All benchmark bugs are saved in [`project/results/benchmark/benchmark_bugs.json`](project/results/benchmark/benchmark_bugs.json), and standalone reproduction tests are available in `project/results/benchmark/repro_*.py`.

---

## 📁 Repository & Commit Artifacts

| Component | Committed to Repo? | Purpose / Description |
|---|---|---|
| **Source Code (`src/`, `cli.py`)** | ✅ **Committed** | Ingestion, context synthesis, symbolic runner, and smart reachability engine. |
| **Test Suite (`tests/`, `pytest.ini`)** | ✅ **Committed** | 6 automated pytest regression tests. |
| **Benchmark (`results/benchmark/`)**| ✅ **Committed** | `benchmark_bugs.json` (50 verified bugs) and 50 standalone `repro_*.py` scripts. |
| **Review Documentation (`docs/`)** | ✅ **Committed** | Formal 10-section Review 1 document (`project_first_review.md`). |
| **Personal HF Tokens** | ❌ **Ignored** | Kept in `~/.cache/huggingface/token` (never committed). |
| **Transient Run Workdirs** | ❌ **Ignored** | `results/*_workdir/` (temporary symbolic execution workspaces ignored by `.gitignore`). |

---

## 📚 Academic References

1. **Y. Zi, Z. Wu, J. Boruch-Gruszecki, J. Bell, and A. Guha**, "AgentPack: A Dataset of Code Changes, Co-Authored by Agents and Humans," *arXiv preprint arXiv:2509.21891v2*, 2025.
2. **P. Schanely**, "CrossHair: A Symbolic Execution Engine for Python," *GitHub Repository*, 2020–2024.
3. **S. Person, M. B. Dwyer, S. Elbaum, and C. S. Pasareanu**, "Differential symbolic execution," *Proc. ACM SIGSOFT FSE*, 2008.
4. **J. Liu, C. S. Xia, Y. Wang, and L. Zhang**, "Is Your Code Generated by ChatGPT Really Correct? Rigorous Evaluation with EvalPlus," *NeurIPS*, 2023.
