# Known Limitations (found empirically, not hypothetical)

## Untyped function signatures produce unreliable results
CrossHair needs complete type annotations to explore realistic inputs. When
an argument has no type hint, symbolic execution can pass values of the
wrong type (e.g. a string where a list was expected), producing a
"divergence" that isn't a real bug. Fix applied: only scan functions where
every argument and the return value has a type annotation (see
`agentpack_loader.py` and the original 30-pair scan in
`results/taxonomy_scan/`).

## Some real divergences are false positives relative to the function's domain
Example: a `factorize(n)` function documented for positive integers will
disagree between old/new versions on negative input, even though negative
input was never a defined case. This is not a bug in either version — it's
an out-of-domain input. This project does not currently infer preconditions
from docstrings; a human (or a future extension) needs to sanity-check new
divergences against the stated domain before treating them as confirmed
bugs.

## The reachability filter cannot prove safety for variable-argument callers
If a call site passes a variable or expression rather than a literal, we
cannot know its runtime value statically. We flag these for human review —
we never claim they're safe. A real extension (constant propagation /
lightweight range inference, or running CrossHair on the caller itself)
could resolve some of these automatically, but this is future work, not
implemented.

## Real agent commits are mostly multi-file and hard to isolate
Mining real GitHub commits with AI-agent co-author trailers (as a stand-in
for AgentPack, which is gated) showed most real agent commits span many
files with long, multi-topic commit messages. Cleanly isolating a single
before/after function pair — which this pipeline needs — is much harder
than with curated benchmark data. `agentpack_loader.py` deliberately
rejects multi-file commits and commits with more than one changed function
per file, rather than attempting to handle the general case.

## AgentPack itself has not yet been tested against this pipeline
Access requires a Hugging Face account, login, and accepting the dataset's
terms — this was not available in the environment where this project was
initially prototyped. `docs/agentpack_setup.md` has the steps needed to
complete this locally.
