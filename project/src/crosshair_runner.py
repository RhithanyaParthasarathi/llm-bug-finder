"""
Part 1 of the strategy: wraps `crosshair diffbehavior`. Detection logic
itself lives entirely inside CrossHair — this module just runs it, parses
its output, and adds checkpointing for batch scans (needed because
CrossHair scans can be slow and batch jobs may be interrupted; see
scripts/run_on_agentpack.py which relies on this).
"""
import json
import os
import subprocess
from dataclasses import dataclass, asdict
from typing import List, Optional


import sys

@dataclass
class DivergenceResult:
    task_name: str
    entry_point: str
    raw_output: str
    counterexample_found: bool


def run_diffbehavior(
    canon_module: str,
    llm_module: str,
    entry_point: str,
    cwd: str,
    per_condition_timeout: int = 10,
    overall_timeout: int = 25,
) -> DivergenceResult:
    """Run `crosshair diffbehavior` on two module.function references.

    canon_module / llm_module should be importable module names (i.e. the
    .py file's basename without extension) resolvable from `cwd`.
    """
    cmd = [
        sys.executable, "-m", "crosshair", "diffbehavior",
        f"{canon_module}.{entry_point}",
        f"{llm_module}.{entry_point}",
        f"--per_condition_timeout={per_condition_timeout}",
    ]
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=overall_timeout)
    out = result.stdout.strip()
    return DivergenceResult(
        task_name=f"{canon_module}_vs_{llm_module}",
        entry_point=entry_point,
        raw_output=out,
        counterexample_found="Given:" in out,
    )


def run_batch_with_checkpointing(
    tasks: List[tuple],  # (task_name, entry_point, canon_module, llm_module)
    cwd: str,
    checkpoint_path: str,
    per_condition_timeout: int = 10,
) -> List[DivergenceResult]:
    """Run diffbehavior over many tasks, saving progress after each one so
    an interrupted run can resume. This is the pattern used for the
    30-pair taxonomy scan and should be reused for AgentPack-scale runs."""
    results: List[DivergenceResult] = []
    processed = set()

    if os.path.exists(checkpoint_path):
        with open(checkpoint_path) as f:
            saved = json.load(f)
        results = [DivergenceResult(**r) for r in saved]
        processed = {r.task_name for r in results}

    for task_name, entry_point, canon_module, llm_module in tasks:
        if task_name in processed:
            continue
        try:
            r = run_diffbehavior(canon_module, llm_module, entry_point, cwd, per_condition_timeout)
        except subprocess.TimeoutExpired:
            r = DivergenceResult(task_name, entry_point, "<timeout>", False)
        results.append(r)
        processed.add(task_name)
        with open(checkpoint_path, "w") as f:
            json.dump([asdict(x) for x in results], f, indent=2)
        print(f"{'DIVERGENCE' if r.counterexample_found else 'no divergence'}: {task_name}", flush=True)

    return results
