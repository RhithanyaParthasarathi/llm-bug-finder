"""
AgentPack ingestion. Grounded in the real paper (arXiv:2509.21891v2) and confirmed
against live dataset schema on 2026-08-17.

Schema confirmed on 2026-08-17:
Top-level keys: ['event_id', 'agent', 'repo', 'sha', 'description', 'patch']
- 'event_id': str (GitHub archive event ID)
- 'agent': str ('Claude Code', 'Cursor Agent', 'Codex')
- 'repo': str (repository owner/name)
- 'sha': str (commit SHA)
- 'description': str (commit message or PR description with trailers)
- 'patch': str (standard unified git diff)

Key facts driving this design:
- Median files touched per commit is 2 (Claude Code / Cursor Agent), 3
  (Codex) — AgentPack does NOT pre-filter to single-file commits, so most
  items will be REJECTED by is_single_file_commit. That is expected and
  correct, not a bug.
- Codex is identified via PR description (a link to chatgpt.com/codex/tasks),
  not a commit trailer, and its diff may span commits by other contributors.
  For a first pass we restrict to Claude Code and Cursor Agent items only,
  since their attribution is a single, clean commit.
- node_modules changes are excluded, matching the original pipeline.
"""
import ast
import re
import textwrap
from dataclasses import dataclass
from typing import Optional, List, Tuple

# Exact / near-variant signals used by the original AgentPack pipeline.
# See docs/agentpack_dataset_facts.md.
CLAUDE_CODE_TRAILER_PATTERNS = [
    re.compile(r"Co-authored-by:\s*Claude\s*<noreply@anthropic\.com>", re.IGNORECASE),
    re.compile(r"Generated with \[?Claude Code\]?", re.IGNORECASE),
    re.compile(r"Claude Code", re.IGNORECASE),
]
CURSOR_AGENT_AUTHOR_PATTERN = re.compile(r"Cursor Agent(\s*<cursoragent@cursor\.com>)?", re.IGNORECASE)

SUPPORTED_AGENTS = ("claude_code", "cursor_agent")  # Codex excluded in first pass, see module docstring


@dataclass
class AgentCommitCandidate:
    commit_sha: str
    repo: str
    file_path: str
    function_name: str
    old_source: str
    new_source: str
    agent: str


def identify_agent(commit_message: str, author_field: str = "", agent_field: str = "") -> Optional[str]:
    """Return 'claude_code', 'cursor_agent', or None. Codex is intentionally
    not detected here — see module docstring."""
    if agent_field:
        norm = agent_field.strip().lower().replace(" ", "_")
        if norm in SUPPORTED_AGENTS:
            return norm
        elif norm == "codex":
            return None  # Codex out of scope for now
    if any(p.search(commit_message or "") for p in CLAUDE_CODE_TRAILER_PATTERNS):
        return "claude_code"
    if CURSOR_AGENT_AUTHOR_PATTERN.search(author_field or "") or CURSOR_AGENT_AUTHOR_PATTERN.search(commit_message or ""):
        return "cursor_agent"
    return None


def load_agentpack_stream():
    """Load AgentPack via the `datasets` library. Requires:
        huggingface-cli login (or valid HF token in ~/.cache/huggingface/token)
    and having accepted the dataset's terms on huggingface.co first.
    See docs/agentpack_setup.md.
    """
    from datasets import load_dataset
    # 1.8M items / 371GB total -- stream rather than downloading in full.
    return load_dataset("nuprl/AgentPack", split="train", streaming=True)


def is_node_modules_path(path: str) -> bool:
    return "node_modules/" in path or path.startswith("node_modules")


def parse_patch_files(patch: str) -> List[Tuple[str, str, bool, bool]]:
    """Parse git patch and return list of (old_path, new_path, is_new_file, is_deleted_file)."""
    if not patch or not patch.strip():
        return []
    file_diffs = re.split(r"(?m)^diff --git ", patch)
    results = []
    for fd in file_diffs:
        if not fd.strip():
            continue
        m = re.search(r"^a/(\S+) b/(\S+)", fd)
        if m:
            old_p, new_p = m.group(1), m.group(2)
        else:
            # fallback for patches without diff --git header
            m_old = re.search(r"^--- (?:a/)?(\S+)", fd, re.MULTILINE)
            m_new = re.search(r"^\+\+\+ (?:b/)?(\S+)", fd, re.MULTILINE)
            if not m_old or not m_new:
                continue
            old_p, new_p = m_old.group(1), m_new.group(1)
        is_new = "--- /dev/null" in fd or old_p == "/dev/null"
        is_del = "+++ /dev/null" in fd or new_p == "/dev/null"
        results.append((old_p, new_p, is_new, is_del))
    return results


def is_single_file_commit(commit_record: dict) -> bool:
    """Reject anything except a clean single-.py-file change. Given AgentPack's
    median of 2 files/commit, MOST records will fail this check by design --
    that is expected, not a bug.
    Confirmed against real schema (2026-08-17): inspects 'patch' field.
    """
    agent = identify_agent(
        commit_message=commit_record.get("description", ""),
        author_field="",
        agent_field=commit_record.get("agent", ""),
    )
    if not agent:
        return False

    patch = commit_record.get("patch", "")
    file_entries = parse_patch_files(patch)
    if not file_entries:
        return False

    # Exclude node_modules
    valid_files = [
        (old_p, new_p, is_new, is_del)
        for (old_p, new_p, is_new, is_del) in file_entries
        if not is_node_modules_path(old_p) and not is_node_modules_path(new_p)
    ]

    # Must be exactly 1 file
    if len(valid_files) != 1:
        return False

    old_p, new_p, is_new, is_del = valid_files[0]
    target_path = new_p if not is_del else old_p
    
    # Must be a Python file and not a fresh creation / total deletion
    if not target_path.endswith(".py"):
        return False
    if is_new or is_del:
        return False

    return True


def extract_file_sources_from_patch(patch: str) -> Optional[Tuple[str, str, str]]:
    """Extract (file_path, old_source, new_source) from a single-file patch."""
    file_diffs = re.split(r"(?m)^diff --git ", patch)
    for fd in file_diffs:
        if not fd.strip():
            continue
        m = re.search(r"^a/(\S+) b/(\S+)", fd)
        file_path = m.group(2) if m else "file.py"
        if "--- /dev/null" in fd or "+++ /dev/null" in fd:
            return None
        old_lines = []
        new_lines = []
        in_hunk = False
        for line in fd.splitlines():
            if line.startswith("@@"):
                in_hunk = True
                continue
            if not in_hunk:
                continue
            if line.startswith("-"):
                old_lines.append(line[1:])
            elif line.startswith("+"):
                new_lines.append(line[1:])
            elif line.startswith(" "):
                old_lines.append(line[1:])
                new_lines.append(line[1:])
        return file_path, "\n".join(old_lines), "\n".join(new_lines)
    return None


def extract_single_function_diff(old_file_source: str, new_file_source: str) -> Optional[List[AgentCommitCandidate]]:
    """Given the old and new content slices of ONE Python file, return an
    isolable before/after function pair if and only if exactly one function's
    body changed.
    Confirmed on 2026-08-17.
    """
    if not old_file_source or not new_file_source:
        return None

    def _parse_and_find_funcs(src: str):
        for candidate in [src, textwrap.dedent(src)]:
            try:
                tree = ast.parse(candidate)
                funcs = {}
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        funcs[node.name] = (node, ast.unparse(node))
                if funcs:
                    return funcs
            except (SyntaxError, IndentationError):
                pass
        return {}

    old_funcs = _parse_and_find_funcs(old_file_source)
    new_funcs = _parse_and_find_funcs(new_file_source)

    if not old_funcs or not new_funcs:
        return None

    changed = [
        name for name in old_funcs
        if name in new_funcs and old_funcs[name][1] != new_funcs[name][1]
    ]

    if len(changed) != 1:
        return None  # ambiguous (0 or multiple changed functions) -- skip deliberately

    name = changed[0]
    return [AgentCommitCandidate(
        commit_sha="", repo="", file_path="",
        function_name=name,
        old_source=old_funcs[name][1],
        new_source=new_funcs[name][1],
        agent="",  # filled in by caller from identify_agent()
    )]
