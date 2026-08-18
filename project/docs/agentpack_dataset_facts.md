# AgentPack — Real Dataset Facts (from the paper, not guessed)

Source: Zi, Wu, Boruch-Gruszecki, Bell, Guha. "AgentPack: A Dataset of Code
Changes, Co-Authored by Agents and Humans." arXiv:2509.21891v2.
https://arxiv.org/html/2509.21891v2

Read this before writing or trusting any code in `src/agentpack_loader.py`.

## Scale
- **1.8M code edits total** (not 1.3M — that figure was from an older
  dataset card blurb, superseded by the current paper).
- 371 GB total. Claude Code: 1,070,262 items / 277GB. Codex: 669,615 items /
  32GB. Cursor Agent: 186,044 items / 62GB.
- Collected from GH Archive events, April 1 – October 7, 2025.

## Structural statistics (medians, per item)
- **Files touched: 2** (Claude Code, Cursor Agent), 3 (Codex). This means
  single-file commits are a MINORITY of the dataset, not the norm — unlike
  CommitPackFT/CanItEdit, which deliberately restricted themselves to
  single-file edits only. AgentPack does not pre-filter by file count.
- Patch size: 67–102 lines depending on agent (81 overall median).
- Hunks per file: ~1.3–1.6 (small, mostly-contiguous edits).
- Commit/PR description length: 116–490 characters median (much longer than
  typical human commit messages).

## How agent-authored commits were identified (use these exact signals)
1. **Claude Code**: commits signed with
   `Co-authored-by: Claude <noreply@anthropic.com>` in the commit message
   (the paper notes there are other variations of this trailer they also
   search for — check for near-variants, not just this exact string).
2. **Codex**: does NOT sign commits directly. Instead, it opens pull
   requests whose description contains a link starting with
   `chatgpt.com/codex/tasks`. Identification requires scanning PR-opening
   events, not commit messages.
3. **Cursor (Background) Agent**: commits authored by
   `Cursor Agent <cursoragent@cursor.com>`.

## Known exclusions applied by the original authors
- `node_modules` changes are filtered out entirely (major source of
  accidental duplicate/bulk commits in JS projects).
- A small random sample per agent was manually verified for correct
  attribution — full-dataset attribution is not guaranteed to be 100% clean.

## Data provenance (relevant to how we should extract old/new content)
The released dataset is built from real git patches on real GitHub repos.
For fine-tuning, the authors themselves parse each item's git patch to
extract: the list of updated files, the previous file content, and the
patched file content — using an "ellipsis-hunk" format for large files
(unseen/unchanged regions are elided). This confirms the underlying data
does support old-content vs new-content extraction per file, which is
exactly what `agentpack_loader.py` needs — but the *exact* field names in
the raw HF dataset release still need to be confirmed by inspecting real
records (see `docs/prompts.md`, Task 1), since the paper describes the
processing pipeline, not necessarily the raw storage schema verbatim.

## Practical implications for our filtering strategy
- Expect roughly **1/3 to 1/2** of items to be single-file (rough estimate
  from "median 2 files" — not exact, needs empirical confirmation once
  real access is available), so filtering to single-file, single-function
  commits will discard the majority of the dataset by design. On 1.8M
  total items this should still leave a large enough pool (likely tens to
  low hundreds of thousands) to build a meaningful evaluation benchmark
  from, but this needs to be measured, not assumed.
- Codex items require different extraction logic than Claude Code / Cursor
  Agent items, since Codex is identified via PR description rather than
  commit trailer, and a Codex PR's diff may span commits by other
  contributors too ("the diff for the entire pull request, which may
  include future commits by others" — per the paper). For a first pass,
  restrict to Claude Code and Cursor Agent items only, since their
  attribution is a single, clean commit rather than a possibly-mixed PR.
- Patch sizes are small (median 81 lines) — this is good news for our
  pipeline; large, unreviewable diffs are not the common case.
