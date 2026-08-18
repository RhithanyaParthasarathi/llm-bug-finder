# Why Part 2 (reachability filter) is deterministic static analysis, not an LLM call

This was a deliberate choice, considered and rejected in favor of the
simpler design. Documenting the reasoning so it isn't accidentally
"improved" back into an LLM-based classifier later.

An LLM could plausibly look at a diff, a CrossHair counterexample, and a
codebase, and guess which callers are at risk. This was rejected as the
primary mechanism for three reasons:

1. **Exhaustiveness.** A static AST walk mechanically visits every call
   site in the given source. An LLM reading a codebase — especially one
   that doesn't fit in a single context window — will miss call sites in
   files it wasn't shown or didn't attend to. A missed caller is exactly
   the failure mode this tool exists to prevent, so silent misses are the
   worst possible outcome here.
2. **Zero hallucination on the literal-argument case.** When the filter
   reports "confirmed bug hit," it's because both function versions were
   actually executed on the exact literal value and produced different
   output — not because a model inferred it looked risky.
3. **Determinism and cost.** Same input always produces the same output, no
   API calls, no per-run variance — important if this eventually runs
   automatically on every PR rather than being invoked ad hoc.

This does not mean LLMs have no role in the project. A reasonable, clearly
separated extension: use the deterministic filter for literal-argument
cases (ground truth, cheap), and use an LLM only to help a human triage the
"flagged for review" variable-argument cases — e.g. summarizing what a
variable's plausible values are from surrounding context — since that is
the one place the deterministic filter genuinely cannot resolve anything
on its own. If this is implemented, it must be clearly presented as an
assistive suggestion, never as a "safe" verdict.
