# Project Context for AI Coding Assistants

Read this fully before making changes. This project has a specific, tested
scope — don't expand it without being asked, and don't "improve" the design
decisions below without flagging why first.

## What this project actually does

Given a diff to a Python function (old version, new version), detect
whether the AI-generated diff silently changed the function's real
behavior, then determine which callers in the surrounding codebase are
actually exposed to that change.

## The two-part strategy — do not conflate these

**Part 1 — Detection.** Delegated entirely to CrossHair
(`crosshair diffbehavior old_module.func new_module.func`). This is an
existing, mature open-source symbolic execution tool. We do NOT reimplement
symbolic execution, invariant inference, or fuzzing ourselves. If a task
looks like it needs "infer what this function should do" — stop, that is
explicitly out of scope (see `docs/limitations.md`, "why we don't infer
invariants").

**Part 2 — Reachability filtering.** This is the project's own code
(`src/reachability_filter.py`). It is deliberately simple, deterministic
static analysis:
- Literal-argument call site → execute both function versions on the exact
  literal value, report ground truth (no guessing).
- Variable-argument call site → flag as "needs human review." Never
  classify a variable-argument call site as safe. This is a hard rule —
  false "safe" verdicts are worse than false positives for this tool's
  purpose.

Do not replace Part 2 with an LLM call that "guesses" which callers are at
risk. That was considered and deliberately rejected — see
`docs/design_decisions.md`. The value of Part 2 is that it's exhaustive and
hallucination-free, not that it's clever.

## Repo layout

```
src/
  diff_extractor.py       # given a git commit/diff, extract old+new function source
  crosshair_runner.py      # wraps `crosshair diffbehavior`, parses its output, has checkpointing
  reachability_filter.py   # Part 2 — call-site classifier (literal vs variable args)
  agentpack_loader.py      # loads + filters AgentPack commits (see below — NOT YET RUN)
  pipeline.py               # orchestrates: commit -> extracted function -> crosshair -> filter
scripts/
  run_on_single_commit.py  # CLI for one before/after pair, for local testing
  run_on_agentpack.py      # batch runner over AgentPack, with checkpointing (see scan_typed30.py pattern)
docs/
  agentpack_setup.md         # gated-dataset access instructions (must be done locally)
  agentpack_dataset_facts.md # real stats/methodology from the AgentPack paper (arXiv:2509.21891)
  limitations.md              # known, real failure modes found during feasibility testing
  design_decisions.md         # why Part 2 is deterministic, not LLM-based
results/
  taxonomy_scan/              # prior real-data scan results (6 verified bug categories)
```

## Known, real constraints — apply these before writing new code

1. **Only scan functions with complete type annotations on every argument
   and the return type.** Untyped functions cause CrossHair to explore
   nonsensical inputs (e.g. a string where a list was expected). This was
   confirmed empirically — see `docs/limitations.md`.
2. **A divergence CrossHair finds is not automatically a real bug.** Some
   divergences only occur on inputs outside the function's intended domain
   (e.g. negative numbers for a function documented to take positive
   integers). Always sanity-check a new divergence against the docstring's
   stated domain before treating it as a confirmed bug.
3. **AgentPack commits are mostly multi-file (confirmed by the paper, not
   assumed).** Median files touched per commit is 2 (Claude Code / Cursor
   Agent) — AgentPack does not pre-filter to single-file edits the way
   CommitPackFT/CanItEdit did. This means our single-file filter will
   reject the majority of records by design; that's expected, not a bug.
   See `docs/agentpack_dataset_facts.md` for the real statistics. Do not
   try to handle multi-file commits in the MVP.
4. **Codex items need different handling than Claude Code / Cursor Agent.**
   Codex is identified via a PR description link, not a commit trailer, and
   its diff may span commits by other contributors. First pass restricts
   to Claude Code and Cursor Agent only (see `agentpack_loader.py`).
4. **Never claim a variable-argument call site is safe.** See Part 2 rule
   above. This is the single most important correctness rule in the repo.

## Bug categories already confirmed with real evidence (don't re-derive)

Requirement misunderstanding, type-semantics bugs, missing/incomplete
branch logic, incorrect edge-case handling, wrong/suboptimal algorithm,
robustness/crash-on-malformed-input. Full examples with code are in
`results/taxonomy_scan/`. New categories can be added if real evidence
supports them — don't assume the list is exhaustive, but don't invent
categories without a confirmed example either.

## What "done" looks like for a task in this repo

Any new detection or filtering logic should be demonstrated against a real
before/after function pair (from EvalPlus, AgentPack, or a real GitHub
commit) with the actual output shown — not just unit tests against
hand-written toy examples. This project's credibility rests on results
being traceable to real data; keep that pattern.
