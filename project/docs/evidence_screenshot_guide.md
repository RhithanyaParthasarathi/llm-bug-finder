# Complete Evidence & Screenshot Guide for Panel Review 2

This guide gives the **exact terminal commands** to run in PowerShell / Bash to capture clean screenshots for every single evidence item (**E1 through E14**) requested in your project report, along with the expected output.

---

## 🚀 Quick Execution Cheatsheet

You can generate any evidence individually by key, or all of them in one run:

```bash
# Run any single evidence:
python project/scripts/generate_evidence.py E1
python project/scripts/generate_evidence.py E2
# ...
python project/scripts/generate_evidence.py E14

# Or run ALL evidences sequentially:
python project/scripts/generate_evidence.py ALL
```

---

## 📸 Evidence E1: Environment & Tooling Verification
> **What to screenshot:** Terminal output showing `python --version` and `pip list` showing the exact installed versions of `crosshair-tool`, `z3-solver`, `datasets`, `huggingface-hub`, `mypy`, `pylint`, and `pytest`.

### Command:
```powershell
python project/scripts/generate_evidence.py E1
```
*(Or native command: `python --version; pip list | Select-String "crosshair|z3-solver|datasets|huggingface|mypy|pylint|pytest"`)*

### Verified Output:
```text
Python 3.14.3
=================================================================
  Evidence E1: Python Environment & Core Verification Tooling
=================================================================

Package Versions (filtered):
  Package                   Version        
  ----------------------------------------
  crosshair-tool            0.0.110        
  datasets                  5.0.1          
  huggingface_hub           1.27.0         
  mypy                      2.3.1          
  pylint                    4.1.1          
  pytest                    9.1.1          
  z3-solver                 5.1.0.0        
```

---

## 📸 Evidence E2: Authenticated AgentPack Streaming Record
> **What to screenshot:** Terminal output showing live authenticated streaming from `nuprl/AgentPack` printing the 6 core schema fields: `event_id`, `agent`, `repo`, `sha`, `description`, `patch`.

### Command:
```powershell
python project/scripts/generate_evidence.py E2
```

### Verified Output:
```text
=================================================================
  Evidence E2: Authenticated AgentPack Streaming Record (6 Fields)
=================================================================
[*] Connecting to Hugging Face nuprl/AgentPack (streaming mode)...

Successfully streamed authenticated record:

--- EVENT_ID ---
48389157678

--- AGENT ---
Claude Code

--- REPO ---
arunmenon/Symphony-Agent-Fwk

--- SHA ---
5ab6deaa6b7ff9f5646d78adfd830795039d7ee6

--- DESCRIPTION ---
Add strategy pattern for memory importance assessment

Implement a flexible importance calculation system:
- Add ImportanceStrategy abstract base class
- Implement RuleBasedStrategy, LLMBasedStrategy, and HybridStrategy
- Integrate with MemoryManager and ConversationMemoryManager
- Add memory prompt... [truncated]

--- PATCH ---
diff --git a/examples/strategic_memory_example.py b/examples/strategic_memory_example.py
new file mode 100644
index 0000000..dded20e
--- /dev/null
+++ b/examples/strategic_memory_example.py
@@ -0,0 +1,212 @@
+"""Example demonstrating the strategy-based memory architecture."""
... [diff truncated for display]
```

---

## 📸 Evidence E3: Directory Listing of `src/` and `scripts/`
> **What to screenshot:** Directory listing showing `context_synthesizer.py`, `crosshair_runner.py`, `smart_reachability.py`, `call_graph_tracker.py`, `pr_scanner.py`, `github_action.py`, `cli.py`.

### Command:
```powershell
python project/scripts/generate_evidence.py E3
```
*(Or native PowerShell: `Get-ChildItem project/src, project/scripts | Select-Object Name, Length | Format-Table -AutoSize`)*

### Verified Output:
```text
=================================================================
  Evidence E3: Directory Listing of src/ and scripts/
=================================================================

project/src/
    agentpack_loader.py                              8346 bytes
    call_graph_tracker.py                            2696 bytes
    cli.py                                           8898 bytes
    context_synthesizer.py                           8693 bytes
    crosshair_runner.py                              2927 bytes
    reachability_filter.py                           4775 bytes
    smart_reachability.py                            5290 bytes

project/scripts/
    build_test_diff.py                               2269 bytes
    debug_patches.py                                 2721 bytes
    estimate_agentpack_yield.py                      2302 bytes
    evaluate_baseline.py                             6821 bytes
    explore_functions_in_patches.py                  3956 bytes
    find_candidates_and_divergences.py               6196 bytes
    find_clean_algorithmic_pairs.py                  4648 bytes
    find_more_divergences.py                         5267 bytes
    generate_evidence.py                            15105 bytes
    github_action.py                                 8493 bytes
    harvest_benchmark.py                             8318 bytes
    inspect_agentpack_schema.py                      2096 bytes
    minimize_counterexamples.py                      1575 bytes
    pr_scanner.py                                   14958 bytes
    run_on_agentpack.py                              3681 bytes
    run_on_single_commit.py                          1981 bytes
    run_reachability_benchmark.py                    8740 bytes
    scan_more_candidates.py                          5417 bytes
    scan_typed_functions.py                          5282 bytes
    seed_benchmark.py                                4743 bytes
    taxonomy_stats.py                                1516 bytes
    verify_bugs.py                                   4420 bytes
```

---

## 📸 Evidence E4: Automated Test Suite Passing (`pytest`)
> **What to screenshot:** Terminal output of `pytest tests/ -v` passing with green status.

### Command:
```powershell
python project/scripts/generate_evidence.py E4
```
*(Or native: `pytest project/tests/ -v`)*

### Verified Output:
```text
============================= test session starts =============================
platform win32 -- Python 3.14.3, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\rhith\Downloads\llm-diff-bugfinder
configfile: pytest.ini
collected 6 items

tests\test_checkpointing.py::test_checkpointing_resumes_cleanly PASSED   [ 16%]
tests\test_context_synthesizer.py::test_type_inference_from_defaults PASSED [ 33%]
tests\test_context_synthesizer.py::test_method_synthesis_with_mock_self PASSED [ 50%]
tests\test_context_synthesizer.py::test_multi_function_extraction_and_crosshair PASSED [ 66%]
tests\test_smart_reachability.py::test_constant_propagation_finds_bug_hit PASSED [ 83%]
tests\test_smart_reachability.py::test_dynamic_variable_flagged_for_review PASSED [100%]

============================== 6 passed in 1.37s ==============================
```

---

## 📸 Evidence E5: Benchmark Audit of `benchmark_bugs.json`
> **What to screenshot:** Audit showing 101 records, agent distribution (Claude Code 98, ChatGPT 3), category distribution, 57 distinct repos, and 96 standalone repro scripts.

### Command:
```powershell
python project/scripts/generate_evidence.py E5
```

### Verified Output:
```text
=================================================================
  Evidence E5: Benchmark Audit — benchmark_bugs.json
=================================================================

  Total verified records       : 101
  Distinct repositories        : 57
  Standalone repro scripts     : 96
  Concrete counterexamples     : 85/101 (84.2%)
  Path-divergence only         : 16/101 (15.8%)

  Distribution by Agent:
    Claude Code                       98 (97.0%)
    ChatGPT / Codex                    3 (3.0%)

  Distribution by Regression Category:
    Requirement misunderstanding / Missing branch logic  43 (42.6%)
    Type-semantics bug                              34 (33.7%)
    Wrong/suboptimal algorithm                      20 (19.8%)
    Incorrect edge-case handling / Robustness crash   1 (1.0%)
    Missing branch logic / Contract change           1 (1.0%)
    Incorrect edge-case handling                     1 (1.0%)
    Requirement misunderstanding                     1 (1.0%)
```

---

## 📸 Evidence E6: Pipeline Funnel / Harvest Summary
> **What to screenshot:** Counts at each conversion stage: ~268,380 commits streamed, ~1,350 single-file diffs, ~490 SMT pairs, 101 verified regressions (20.6% yield).

### Command:
```powershell
python project/scripts/generate_evidence.py E6
```

### Verified Output:
```text
=================================================================
  Evidence E6: Pipeline Funnel / Harvest Stage Summary
=================================================================
  Scan Checkpoint Records Logged   : 6

  Pipeline Stage                                   Count     Conversion
  --------------------------------------------------------------
  1. Commits streamed from nuprl/AgentPack      ~268,380         100.0%
  2. Single-.py-file agent commits extracted    ~  1,350           0.5%
  3. Compatible function pairs passed to SMT    ~    490          36.3%
  4. Formally verified behavioral regressions        101          20.6%

  Final Candidate-to-Bug Yield: 20.6% (1 bug per 5 analyzed diff pairs)
```

---

## 📸 Evidence E7: Baseline Evaluation (mypy + pylint vs Our Tool)
> **What to screenshot:** Table showing 101 benchmark items evaluated: mypy caught 8 (7.9%), pylint caught 9 (8.9%), union caught 12 (11.9%), our tool caught 101 (100.0%). Regressions missed by BOTH: 89/101 (88.1%).

### Command:
```powershell
python project/scripts/generate_evidence.py E7
```

### Verified Output:
```text
=================================================================
  Evidence E7: Baseline Evaluation (mypy + pylint vs LLM-Diff-BugFinder)
=================================================================

  Tool                             Caught   Total   Detection Rate
  -----------------------------------------------------------------
  mypy                                  8     101             7.9%
  pylint                                9     101             8.9%
  Union (mypy OR pylint)               12     101            11.9%
  LLM-Diff-BugFinder (ours)           101     101           100.0%

  Silent Regressions Missed by BOTH Tools: 89/101 (88.1%)

  First 10 sample entries from the 101 benchmark items:
  #    Task (truncated)                                   mypy   pylint   ours
  --------------------------------------------------------------------------
  1    kym6464__clipboard-to-url_89c83dc3_read_csv       False    False   True
  2    alexwday__iris-project_2a072768__process_refe     False    False   True
  3    HumanEval_10_make_palindrome                      False    False   True
  4    HumanEval_18_how_many_times                       False    False   True
  5    HumanEval_26_remove_duplicates                    False    False   True
  6    MementoRC__ci-framework_3478c8b8_test_securit     False    False   True
  7    MementoRC__claude-code-knowledge-framework_ef     False    False   True
  8    MementoRC__claude-code-knowledge-framework_ef     False    False   True
  9    MementoRC__claude-code-knowledge-framework_ef     False    False   True
  10   MementoRC__claude-code-knowledge-framework_ef     False    False   True
  ... [91 more entries verified]
```

---

## 📸 Evidence E8: Reachability Benchmark Verdict Counts
> **What to screenshot:** Reachability verdict breakdown: 62 CONFIRMED_BUG_HIT, 44 VARIABLE_PARAM, 26 CONCRETE_SAFE out of 132 total call sites. Zero false-safe violations = 0.

### Command:
```powershell
python project/scripts/generate_evidence.py E8
```

### Verified Output:
```text
=================================================================
  Evidence E8: Reachability Benchmark Verdict Counts
=================================================================

  Total verified regressions evaluated : 44
  Total downstream call sites scanned   : 132

  CONFIRMED_BUG_HIT                     :   62 ( 47.0%)
  VARIABLE_PARAM                        :   44 ( 33.3%)
  CONCRETE_SAFE                         :   26 ( 19.7%)
  Total Call Sites                      :  132 (100.0%)

  Zero False-Safe Guarantee Violations  : 0 (MUST BE 0)
```

---

## 📸 Evidence E9: Independent Audit of CONCRETE_SAFE Verdicts
> **What to screenshot:** Independent re-evaluation of all 26 CONCRETE_SAFE call sites confirming 0 disagreements and a 0.0% false-safe error rate.

### Command:
```powershell
python project/scripts/generate_evidence.py E9
```

### Verified Output:
```text
=================================================================
  Evidence E9: Independent Re-Check of CONCRETE_SAFE Call Sites
=================================================================

  CONCRETE_SAFE verdicts issued         : 26
  Call sites independently re-evaluated : 26
  Disagreements / missed bugs           : 0
  False-safe error rate                 : 0.0%

  [VERDICT]: Zero false-safe violations verified.
  Every filtered call site was mathematically unreachable by the bug input.
```

---

## 📸 Evidence E10: Reachability Ablation (Constant Propagation On vs Off)
> **What to screenshot:** Comparative table of reachability verdicts with vs without constant propagation, showing +31 sites lifted from VARIABLE_PARAM to CONFIRMED_BUG_HIT.

### Command:
```powershell
python project/scripts/generate_evidence.py E10
```

### Verified Output:
```text
=================================================================
  Evidence E10: Reachability Ablation (Constant Propagation On vs Off)
=================================================================

  Reachability Verdict         WITHOUT Const-Prop    WITH Const-Prop
  ------------------------------------------------------------------
  CONFIRMED_BUG_HIT                            31                 62
  CONCRETE_SAFE                                26                 26
  VARIABLE_PARAM                               75                 44
  ------------------------------------------------------------------
  TOTAL SITES                                 132                132

  Net Lift: Constant propagation promoted +31 call sites from VARIABLE_PARAM
  to CONFIRMED_BUG_HIT, reducing developer triage burden.
```

---

## 📸 Evidence E11: End-to-End Bug Counterexample & Differential Execution
> **What to screenshot:** Raw CrossHair counterexample output, minimized failing input, and reproduction execution showing divergent return values on identical inputs.

### Command:
```powershell
python project/scripts/generate_evidence.py E11
```

### Verified Output:
```text
=================================================================
  Evidence E11: End-to-End Bug Counterexample & Repro Execution
=================================================================
  Bug Task   : tobypullan__CC_GH_Integration_229fa7e5_subtract_vectors
  Repository : tobypullan/CC_GH_Integration
  Function   : subtract_vectors
  Category   : Type-semantics bug

--- 1. Raw SMT Counterexample (CrossHair Output) ---
Given: (x='', y='\x00\x00'),
  tobypullan__CC_GH_Integration_229fa7e5_subtract_vectors_old.subtract_vectors : returns '\x00\x00'
  tobypullan__CC_GH_Integration_229fa7e5_subtract_vectors_new.subtract_vectors : raises TypeError("unsupported operand type(s) for -: 'str' and 'str'")

--- 2. Minimized Failing Input ---
Args: (x='', y='\x00\x00')
- Old Code: returns '\x00\x00'
- New Code: raises TypeError("unsupported operand type(s) for -: 'str' and 'str'")

--- 3. Live Differential Execution of Old vs New Version ---

  [Test Case]: Concrete Counterexample (SMT Witness)
    Input Arguments: x = '', y = '\x00\x00'
    Pre-Diff  Function Result : '\x00\x00'
    Post-Diff Function Result : raises TypeError: unsupported operand type(s) for -: 'str' and 'str'
    💥 REGRESSION CONFIRMED: Behavioral divergence detected!

  [Test Case]: Numeric Vector Difference
    Input Arguments: x = 10, y = 3
    Pre-Diff  Function Result : 13
    Post-Diff Function Result : 7
    💥 REGRESSION CONFIRMED: Behavioral divergence detected!

  [Test Case]: Boundary Zero Input
    Input Arguments: x = 0, y = 0
    Pre-Diff  Function Result : 0
    Post-Diff Function Result : 0
    Equivalence holds.
```

---

## 📸 Evidence E12: CLI Diff Check & Benchmark Report
> **What to screenshot:** Terminal run of the CLI checking two versions of a file (`cli.py check`) and displaying the benchmark summary (`cli.py benchmark-report`).

### Command:
```powershell
python project/src/cli.py check --old-file project/results/agentpack_workdir/kym6464__clipboard-to-url_89c83dc3_read_csv_old.py --new-file project/results/agentpack_workdir/kym6464__clipboard-to-url_89c83dc3_read_csv_new.py --pr-comment
```

### Verified Output:
```text
======================================================================
LLM-Diff-BugFinder: Checking Diff for Behavioral Regressions
  Old version: project/results/agentpack_workdir/kym6464__clipboard-to-url_89c83dc3_read_csv_old.py
  New version: project/results/agentpack_workdir/kym6464__clipboard-to-url_89c83dc3_read_csv_new.py
======================================================================

[*] Detected 1 changed function(s). Running symbolic analysis...

[!] REGRESSION DETECTED in `read_csv`!
    Counterexample found by SMT solver:
      Given: (value='\x00\x05'),
        read_csv_old.read_csv : raises AssertionError('Expected comma, semicolon, or tab delimiter in header')
        read_csv_new.read_csv : raises AssertionError('Expected at least 2 lines for CSV structure')

======================================== AUTOMATED PR BOT COMMENT ========================================
### ⚠️ LLM-Diff-BugFinder: Silent Behavioral Regression Detected

The proposed diff modifies `read_csv`, but alters its runtime behavior on specific inputs.

**SMT Counterexample Proof:**
```text
Given: (value='\x00\x05'),
  read_csv_old.read_csv : raises AssertionError('Expected comma, semicolon, or tab delimiter in header')
  read_csv_new.read_csv : raises AssertionError('Expected at least 2 lines for CSV structure')
```

**Downstream Impact:** No direct callers found in the analyzed scope.

**Action:** 🛑 Merge Blocked. Please review and revert the behavioral divergence.
==========================================================================================================
```

### Follow-up command for benchmark report:
```powershell
python project/src/cli.py benchmark-report
```

---

## 📸 Evidence E13: Simulated Pull-Request Bot Run
> **What to screenshot:** Simulated pull-request run of `scripts/github_action.py` showing detection of regression, SMT solver run, and generated PR comment.

### Command:
```powershell
python project/scripts/github_action.py
```

### Verified Output:
```text
======================================================
  GITHUB ACTION HOOK  —  LLM-Diff-BugFinder
======================================================
  PR received for  : MementoRC/claude-code-knowledge-framework
  AI agent         : Claude Code
  Modified function: test_get_pattern_categories
======================================================

[1/3] Repro script found: repro_MementoRC__claude-code-knowledge-framework_ef3c137f_test_get_pattern_categories.py
      Splitting into old_version.py  (before AI edit)
                  and new_version.py  (after  AI edit)...

[2/3] Running CrossHair Z3 solver LIVE on both versions...
      Solving............... done (14.4s)

  ❌  REGRESSION CONFIRMED BY Z3 SOLVER
  --------------------------------------------------
  Given: (manager='', mock_pattern_classification='\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01'),
    old_version.test_get_pattern_categories : raises AttributeError("'LazyIntSymbolicStr' object has no attribute 'get_categories_for_pattern'")
    new_version.test_get_pattern_categories : raises AttributeError("'LazyIntSymbolicStr' object has no attribute 'get_pattern_categories'")
  --------------------------------------------------

[3/3] Scanning repository for callers of `test_get_pattern_categories`...

======================================================
  📝  AUTOMATED PR COMMENT (what GitHub would see)
======================================================

⚠️ **LLM-Diff-BugFinder caught a silent regression!**

The AI agent **Claude Code** modified `test_get_pattern_categories` in `MementoRC/claude-code-knowledge-framework`.
The Z3 SMT solver proved the new version behaves differently
from the original on the following concrete inputs:

```
Given: (manager='', mock_pattern_classification='\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01'),
  old_version.test_get_pattern_categories : raises AttributeError("'LazyIntSymbolicStr' object has no attribute 'get_categories_for_pattern'")
  new_version.test_get_pattern_categories : raises AttributeError("'LazyIntSymbolicStr' object has no attribute 'get_pattern_categories'")
```

**✅ Codebase Impact:** No callers found in scanned source tree.
   (Scanned: `project\src`)

*Detected by LLM-Diff-BugFinder — mypy: missed ✗ | pylint: missed ✗ | Z3 solver: caught ✓*
======================================================
```

---

## 📸 Evidence E14: Real GitHub Actions PR Workflow & Bot Integration
> **What to screenshot:** 
> 1. Terminal output of `python project/scripts/generate_evidence.py E14`
> 2. The workflow file definition at `.github/workflows/llm-bugfinder.yml`
> 3. In GitHub UI (if live repository is connected): the Actions run tab showing the failed check step blocking merge.

### Command:
```powershell
python project/scripts/generate_evidence.py E14
```

### Verified Output:
```text
=================================================================
  Evidence E14: GitHub Actions PR Workflow & Bot Integration
=================================================================
  Workflow definition: .github/workflows/llm-bugfinder.yml (Exists: True)
  Action entrypoint   : project/scripts/pr_scanner.py / project/scripts/github_action.py

  CI Pipeline Steps in GitHub Actions:
    1. on: pull_request [paths: **.py]
    2. actions/checkout@v4 (fetch-depth: 0)
    3. pip install crosshair-tool z3-solver
    4. git diff origin/main...HEAD -- '*.py' | python project/scripts/pr_scanner.py --stdin
    5. Post automated PR review comment via GitHub REST API ($GITHUB_TOKEN)
    6. Exit Code 1 -> CI Check fails, GitHub blocks 'Squash and merge' button.
```
