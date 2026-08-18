# AgentPack Access Setup (must be done locally, not in this scaffold)

AgentPack (huggingface.co/datasets/nuprl/AgentPack) is gated: you must be
logged into a Hugging Face account and have accepted the dataset's terms
before you can download or stream it.

## Steps

1. Create a free account at https://huggingface.co/join if you don't have one.
2. Visit https://huggingface.co/datasets/nuprl/AgentPack and accept the
   dataset's terms (there will be a button/checkbox on the page).
3. Generate an access token: https://huggingface.co/settings/tokens
   (a "read" token is sufficient).
4. Install and authenticate the CLI:
   ```bash
   pip install huggingface-hub
   huggingface-cli login
   # paste your token when prompted
   ```
5. Verify access:
   ```python
   from datasets import load_dataset
   ds = load_dataset("nuprl/AgentPack", split="train", streaming=True)
   print(next(iter(ds)))
   ```
   If this prints a record instead of a permissions error, you're set up.

## Before running the full pipeline against it

- Inspect the actual schema of a few real records first (field names for
  file lists, diffs, commit metadata) and update `is_single_file_commit`
  and `extract_single_function_diff` in `src/agentpack_loader.py`
  accordingly — the current implementation has placeholder field-name
  assumptions that need to be confirmed against real records.
- Start with `--limit 50` or so in `scripts/run_on_agentpack.py` to sanity
  check the pipeline before running it against the full 1.3M-commit
  dataset.
