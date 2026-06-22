"""Shared helper for diff-aware PR-review gating.

Returns the set of top-level example folders touched vs a git ref, so CI can gate
ONLY what a PR changes — grandfathering the existing backlog on `main` instead of
failing every PR on pre-existing debt.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

LANG_SUFFIXES = ("-python", "-nodejs", "-go", "-ruby", "-php", "-java", "-csharp")


def is_example_dir(name: str) -> bool:
    return name.endswith(LANG_SUFFIXES)


def changed_example_dirs(root: Path, ref: str) -> list[str]:
    """Top-level example folders with changes vs <ref>.

    Tries three-dot (changes since the merge-base, i.e. what the PR adds) and
    falls back to a plain diff if that form fails (e.g. shallow checkout).
    """
    out = ""
    for diff_args in ([f"{ref}...HEAD"], [ref]):
        try:
            res = subprocess.run(
                ["git", "-C", str(root), "diff", "--name-only", *diff_args],
                capture_output=True, text=True, check=True,
            )
            out = res.stdout
            break
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    dirs = set()
    for line in out.splitlines():
        top = line.split("/", 1)[0]
        if is_example_dir(top) and (root / top).is_dir():
            dirs.add(top)
    return sorted(dirs)
