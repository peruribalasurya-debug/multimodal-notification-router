#!/usr/bin/env python
"""tasks.py -- cross-platform task runner for the message notification router.

Works anywhere Python runs, with no install step and no dependency on GNU Make (which
isn't available out of the box on plain Windows / Git Bash). The Makefile at the repo
root wraps these same commands for Unix users who prefer `make <target>`.

Usage:
    python tasks.py install   # pip install -r requirements.txt
    python tasks.py run       # full pipeline: dataset/messages.csv -> dataset/output.csv
    python tasks.py eval      # evaluation harness: dataset/sample_messages.csv -> reports/
    python tasks.py test      # quick smoke test across all three pipeline stages
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent


def _run(cmd: list[str]) -> int:
    print(f"$ {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=REPO_ROOT).returncode


def cmd_install(extra_args: list[str]) -> int:
    return _run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt", *extra_args])


def cmd_run(extra_args: list[str]) -> int:
    return _run([sys.executable, "run.py", *extra_args])


def cmd_eval(extra_args: list[str]) -> int:
    return _run([sys.executable, "-m", "src.eval", *extra_args])


def cmd_test(extra_args: list[str]) -> int:
    """Quick smoke test, not a deep accuracy check (use `eval` for that): runs each
    pipeline stage's own self-check in turn -- context assembly on 3 sample messages
    (src/context.py), media extraction on 2 images + 2 voice notes (src/media.py), and
    the router's 30-message sample evaluation (src/router.py) -- to confirm nothing in
    the pipeline is broken end-to-end. Stops at the first failure."""
    steps = [
        [sys.executable, "src/context.py"],
        [sys.executable, "src/media.py"],
        [sys.executable, "src/router.py"],
    ]
    for step in steps:
        code = _run(step)
        if code != 0:
            print(f"\nFAILED: {' '.join(step)} exited with code {code}")
            return code
    print("\nAll smoke tests passed.")
    return 0


COMMANDS = {
    "install": cmd_install,
    "run": cmd_run,
    "eval": cmd_eval,
    "test": cmd_test,
}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Task runner for the message notification router.",
        epilog="Extra args after the command are forwarded verbatim, e.g. "
        "`python tasks.py eval --limit 5`.",
    )
    parser.add_argument("command", choices=sorted(COMMANDS), help="task to run")
    args, extra_args = parser.parse_known_args()
    sys.exit(COMMANDS[args.command](extra_args))


if __name__ == "__main__":
    main()
