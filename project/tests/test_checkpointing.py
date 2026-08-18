"""
Test that run_batch_with_checkpointing in crosshair_runner resumes correctly
when interrupted and does not re-run already processed tasks.
"""
import os
import json
import tempfile
import pytest
from src.crosshair_runner import run_batch_with_checkpointing, DivergenceResult


def test_checkpointing_resumes_cleanly(monkeypatch):
    # Mock run_diffbehavior to record calls
    call_log = []

    def mock_run_diffbehavior(canon_module, llm_module, entry_point, cwd, per_condition_timeout=10):
        task_name = f"{canon_module}_vs_{llm_module}"
        call_log.append(task_name)
        return DivergenceResult(
            task_name=task_name,
            entry_point=entry_point,
            raw_output="Given: x=1",
            counterexample_found=True,
        )

    monkeypatch.setattr("src.crosshair_runner.run_diffbehavior", mock_run_diffbehavior)

    with tempfile.TemporaryDirectory() as tmpdir:
        checkpoint_file = os.path.join(tmpdir, "checkpoint.json")

        tasks = [
            ("task1_vs_task1_llm", "foo", "task1", "task1_llm"),
            ("task2_vs_task2_llm", "bar", "task2", "task2_llm"),
            ("task3_vs_task3_llm", "baz", "task3", "task3_llm"),
        ]

        # First run: only run first 2 tasks (simulating interruption before task 3)
        res1 = run_batch_with_checkpointing(tasks[:2], cwd=tmpdir, checkpoint_path=checkpoint_file)
        assert len(res1) == 2
        assert call_log == ["task1_vs_task1_llm", "task2_vs_task2_llm"]

        # Verify checkpoint file exists and has 2 records
        assert os.path.exists(checkpoint_file)
        with open(checkpoint_file) as f:
            data = json.load(f)
        assert len(data) == 2
        assert data[0]["task_name"] == "task1_vs_task1_llm"
        assert data[1]["task_name"] == "task2_vs_task2_llm"

        # Second run: resume with all 3 tasks
        res2 = run_batch_with_checkpointing(tasks, cwd=tmpdir, checkpoint_path=checkpoint_file)
        assert len(res2) == 3
        # Ensure task1 and task2 were NOT re-run
        assert call_log == ["task1_vs_task1_llm", "task2_vs_task2_llm", "task3_vs_task3_llm"]

        # Verify final checkpoint file has 3 records
        with open(checkpoint_file) as f:
            data2 = json.load(f)
        assert len(data2) == 3
        assert [r["task_name"] for r in data2] == [
            "task1_vs_task1_llm",
            "task2_vs_task2_llm",
            "task3_vs_task3_llm",
        ]
