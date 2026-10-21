"""
Build a synthetic unified git diff from two real repro scripts
to demonstrate the multi-file, multi-function PR scanner.
"""
import sys, os, json, glob

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

repro_dir = os.path.join(os.path.dirname(__file__), "..", "results", "benchmark")

MARKER = "# --- Post-diff Version (AI Modified) ---"

def load_repro(path):
    text = open(path, encoding="utf-8").read()
    if MARKER not in text:
        return None, None
    old, new = text.split(MARKER, 1)
    return old.strip(), new.strip()

def make_unified_diff(old_src, new_src, filepath):
    """Create a minimal unified diff block from two source strings."""
    old_lines = old_src.splitlines()  # no keepends — we add them uniformly
    new_lines = new_src.splitlines()

    lines = [
        f"diff --git a/{filepath} b/{filepath}\n",
        f"--- a/{filepath}\n",
        f"+++ b/{filepath}\n",
        f"@@ -1,{len(old_lines)} +1,{len(new_lines)} @@\n",
    ]
    for l in old_lines:
        lines.append("-" + l + "\n")
    for l in new_lines:
        lines.append("+" + l + "\n")
    return "".join(lines)

# Pick 2 repros from different repos
repros = [
    ("project/results/benchmark/repro_MementoRC__claude-code-knowledge-framework_ef3c137f_test_get_pattern_categories.py",
     "knowledge_framework/test_knowledge_manager.py"),
    ("project/results/benchmark/repro_HubSpot__homebrew-pypi-poet_f5baa0a5__find_latest_version.py",
     "poet/utils.py"),
]

diff_blocks = []
for repro_path, fake_filepath in repros:
    full_path = os.path.join(os.path.dirname(__file__), "..", repro_path.replace("project/", ""))
    if not os.path.exists(full_path):
        full_path = repro_path
    if not os.path.exists(full_path):
        print(f"[skip] {repro_path}")
        continue
    old, new = load_repro(full_path)
    if old and new:
        diff_blocks.append(make_unified_diff(old, new, fake_filepath))

combined = "\n".join(diff_blocks)
out_path = os.path.join(os.path.dirname(__file__), "..", "scratch", "test_pr.diff")
os.makedirs(os.path.dirname(out_path), exist_ok=True)
open(out_path, "w", encoding="utf-8").write(combined)
print(f"Wrote synthetic 2-file diff to: {out_path}")
print(f"Lines: {len(combined.splitlines())}")
