#!/usr/bin/env python3
"""Run the current saved-input analyses from the repository root."""
from __future__ import annotations
import argparse
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
STEPS = {
    "scores": ("analyze_scores.py", "precision_simulation.py"),
    "literal": ("analyze_literal_counts.py", "staunton_selected_sensitivity.py"),
    "selection": ("analyze_selection_decomposition.py",),
    "retention": ("reproduce_retention.py",),
    "external": ("reproduce_external_linkage.py",),
}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", choices=tuple(STEPS), help="Run one analysis group.")
    parser.add_argument("--list", action="store_true", help="List commands without running them.")
    args = parser.parse_args()
    selected = {args.only: STEPS[args.only]} if args.only else STEPS
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    for group, scripts in selected.items():
        for script in scripts:
            print(f"[{group}] {sys.executable} {script}", flush=True)
            if not args.list:
                subprocess.run([sys.executable, str(ROOT / script)], cwd=ROOT,
                               env=env, check=True)
    if not args.list:
        subprocess.run([sys.executable, str(ROOT / "verify_results.py"),
                        *(["--only", args.only] if args.only else [])],
                       cwd=ROOT, env=env, check=True)

if __name__ == "__main__":
    main()
