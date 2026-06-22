"""Shared helper for diff-aware PR-review gating.

Returns what a PR changed vs a git ref so CI can gate ONLY what the PR introduces
— grandfathering the existing backlog on `main` instead of failing every PR on
pre-existing debt.

Three granularities, picked per gate so a repo-wide change (e.g. a mass doc edit)
doesn't re-flag untouched backlog in folders it happens to touch:
  - changed_example_dirs : top-level example folders touched (structural gate)
  - changed_files        : every changed file path (pinning scopes to dep files)
  - added_lines          : only lines the PR ADDS (legacy-ref gate — a ref can
                           only be *introduced* on an added line)
"""
from __future__ import annotations

# nosemgrep: gitlab.bandit.B404 -- git is invoked list-form (no shell=True) with the
# ref passed as a discrete argv element, never string-interpolated, so there is no
# shell-injection surface. We need the local git binary to compute the PR diff.
import subprocess  # noqa: S404
from pathlib import Path

LANG_SUFFIXES = ("-python", "-nodejs", "-go", "-ruby", "-php", "-java", "-csharp")


def is_example_dir(name: str) -> bool:
    return name.endswith(LANG_SUFFIXES)


def _git_diff(root: Path, ref: str, *extra: str) -> str:
    """Run `git diff <extra> <range>`, trying three-dot (changes since merge-base,
    i.e. what the PR adds) then a plain diff (e.g. shallow checkout)."""
    for diff_args in ([f"{ref}...HEAD"], [ref]):
        try:
            res = subprocess.run(
                ["git", "-C", str(root), "diff", *extra, *diff_args],
                capture_output=True, text=True, check=True,
            )
            return res.stdout
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    return ""


def changed_files(root: Path, ref: str) -> list[str]:
    """Every changed file path (repo-relative) vs <ref>."""
    return [line for line in _git_diff(root, ref, "--name-only").splitlines() if line]


def changed_example_dirs(root: Path, ref: str) -> list[str]:
    """Top-level example folders with changes vs <ref>."""
    dirs = set()
    for line in changed_files(root, ref):
        top = line.split("/", 1)[0]
        if is_example_dir(top) and (root / top).is_dir():
            dirs.add(top)
    return sorted(dirs)


def added_lines(root: Path, ref: str) -> list[tuple[str, str]]:
    """Lines the PR ADDS vs <ref>, as (repo-relative-path, line-text).

    Uses --unified=0 so only genuinely-added lines are returned — never context
    or removed lines. This lets a gate flag a violation only when the PR
    introduces it, not when it merely touches a file that already contained it.
    """
    out = []
    current = None
    for line in _git_diff(root, ref, "--unified=0").splitlines():
        if line.startswith("+++ b/"):
            current = line[len("+++ b/"):]
        elif line.startswith("+++ "):  # /dev/null (deletion) — no target file
            current = None
        elif current and line.startswith("+") and not line.startswith("+++"):
            out.append((current, line[1:]))
    return out
