# Prompts for the Code Assistant

`CLAUDE.md` at the repo root is read automatically by Claude Code at the
start of a session — it already has the project context, so you don't need
to re-explain the strategy every time. These prompts are for specific next
tasks. Paste them as-is; each assumes the assistant has already read
CLAUDE.md (true by default in Claude Code; for Copilot Chat, paste
CLAUDE.md's contents first if it isn't auto-attached).

## Task 1 — Confirm the AgentPack schema and fix the loader's placeholders

```
Read docs/agentpack_setup.md and src/agentpack_loader.py. The field names
"files_changed", "old_content", "new_content", "repo", and "commit_sha" in
agentpack_loader.py are placeholders I have not yet verified against the
real dataset schema. Write a small script (scripts/inspect_agentpack_schema.py)
that streams the first 5 records from nuprl/AgentPack and prints their full
key structure and one truncated example value per key, so I can see the
real field names. Do not modify agentpack_loader.py yet — just help me see
the real schema first.
```

## Task 2 — Update the loader once you know the real schema

```
Here is the real record structure from AgentPack (paste the output from
Task 1). Update is_single_file_commit and extract_single_function_diff in
src/agentpack_loader.py to use the correct real field names instead of the
placeholders. Keep the existing filtering behavior described in CLAUDE.md:
reject multi-file commits, and reject files where more than one top-level
function changed. Add a docstring note showing today's date and that the
schema was confirmed against real data, not assumed.
```

## Task 3 — Run a small sanity-check batch before scaling up

```
Run scripts/run_on_agentpack.py with --limit 50 and show me the output.
Before running, check: does the checkpointing in
crosshair_runner.run_batch_with_checkpointing actually resume correctly if
I interrupt and re-run the same command? Write a quick test for that
specifically, since AgentPack is large and this will likely need to run in
many batches over time.
```

## Task 4 — Manually verify any new divergence before trusting it

```
scripts/run_on_agentpack.py just found a divergence for [task_name]. Before
I count this as a confirmed bug, do the following: (1) show me the actual
old and new function source, (2) construct a clean, human-readable input
(not just CrossHair's raw counterexample, which may contain unreadable
characters) that reproduces the divergence, (3) run both versions on that
input and show the actual differing output, (4) check the function's
docstring for any stated domain restriction that might make this a false
positive rather than a real bug, per docs/limitations.md. Do not mark it
confirmed until all four steps are shown.
```

## Task 5 — Extend the taxonomy with new AgentPack-sourced bugs

```
Once we have several manually-verified real divergences from AgentPack
(via Task 4), read results/taxonomy_scan/typed30_divergences.json for the
existing category format from the HumanEval+ scan, and help me classify
each new AgentPack-sourced bug into an existing category from CLAUDE.md's
"Bug categories already confirmed" list, or propose a new category only if
none of the existing ones genuinely fit. Do not force-fit a new bug into an
existing category just to avoid adding one — but don't add a new category
without a real, verified example either.
```

## Task 6 — Extend the reachability filter (only if genuinely needed)

```
Read docs/design_decisions.md before touching src/reachability_filter.py.
I want to reduce false "VARIABLE_PARAM" flags for callers where the
variable is actually provably bounded (e.g. a loop variable with a known
range, or a value that was validated by an earlier assert/if-check in the
same function). Propose a minimal, scoped extension — this should still
never claim a call site is safe without proof; it should only convert some
existing VARIABLE_PARAM cases into CONCRETE_SAFE or CONFIRMED_BUG_HIT where
the safety can genuinely be derived, not guessed. Show me the design before
implementing it.
```

## General rule for any task not listed above

```
Before implementing, check CLAUDE.md's "known, real constraints" and
docs/limitations.md. If what I'm asking conflicts with a documented
constraint or limitation, tell me explicitly which one and why, rather
than silently working around it.
```
