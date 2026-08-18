# LLM-Diff-BugFinder 🔍

> **Automated Detection and Reachability Analysis of Silent Behavioral Regressions in AI-Generated Code Diffs using Differential Symbolic Execution.**

---

## 📌 Overview

AI coding assistants (such as **Claude Code**, **Cursor Agent**, and **GitHub Copilot**) generate billions of lines of code modifications daily. However, their code changes frequently introduce **silent, non-crashing behavioral regressions** that evade static linters, type checkers, and traditional code review.

**LLM-Diff-BugFinder** provides a mathematically sound, hallucination-free pipeline that:
1. **Detects Behavioral Divergences:** Uses the Z3 SMT solver via **CrossHair** to explore execution paths symbolically and solve for exact concrete inputs where the AI's version breaks the original function contract.
2. **Synthesizes Context & Stubs:** Supports class methods (`MockSelf`), docstring/default-based type inference, and external library dependency mocking.
3. **Smart Reachability Analysis:** Performs intra-procedural constant propagation across the codebase AST to prove which downstream callers are broken (**`CONFIRMED_BUG_HIT`**) vs. unaffected (**`CONCRETE_SAFE`**) with zero AI hallucination.
4. **Mined Benchmark Suite:** Includes a curated benchmark of **50 verified, reproducible real-world AI bugs** harvested from 100,000 commits in the **AgentPack** dataset.

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

### 1. View the 50-Bug Benchmark Report
```bash
python cli.py benchmark-report
```

---

### 2. Check a Code Diff for Regressions
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

### 3. Run the Batch Harvester on AgentPack
```bash
# Quick test scan (10,000 commits, target 5 bugs):
python project/scripts/harvest_benchmark.py --limit 10000 --target 5

# Full-scale benchmark sweep (100,000 commits, target 50 bugs):
python project/scripts/harvest_benchmark.py --limit 100000 --target 50
```

---

### 4. Run the Automated Unit Test Suite
```bash
python -m pytest
```

---

### 5. Inspect AgentPack Dataset Schema
```bash
python project/scripts/inspect_agentpack_schema.py
```

---

## 📊 Benchmark Suite Results

Across **100,001 scanned commits** from the `nuprl/AgentPack` dataset, the pipeline discovered and verified **50 reproducible real-world AI bugs**:

| Category | Bugs Found | Example Repositories |
|---|---|---|
| **Requirement Misunderstanding / Missing Logic** | **23** | `awilmoth/mcp-firewall`, `MementoRC/claude-code-knowledge-framework`, `naofumi-fujii/my-schedule`, `broadinstitute/starrynight` |
| **Type-Semantics Bug** | **17** | `MementoRC/mcp-git`, `kevin82222/remote-server`, `tobypullan/CC_GH_Integration`, `kimata/rasp-water` |
| **Wrong / Suboptimal Algorithm** | **7** | `HumanEval_10`, `toiee-lab/librechat-manager`, `johnathan-greenaway/chat-console`, `fsgeek/Mallku`, `DevsyAI/devsy-action` |
| **Incorrect Edge-Case Handling / Robustness Crash** | **3** | `kym6464/clipboard-to-url`, `HumanEval_18` |

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
