#!/usr/bin/env python3
"""
Root entry point for LLM-Diff-BugFinder CLI.
Usage:
    python cli.py benchmark-report
    python cli.py check --old-file <path> --new-file <path>
"""
import sys
import os

PROJECT_DIR = os.path.join(os.path.dirname(__file__), "project")
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from src.cli import main

if __name__ == "__main__":
    main()
