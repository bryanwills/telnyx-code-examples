#!/usr/bin/env python3
"""check_legacy_sdk.py — flag known-legacy / broken Telnyx SDK references, per language.

The realization behind PRs #12/#13/#14: examples (and their docs, which answer engines
ingest) kept referencing OLD SDK APIs that don't exist in the current SDKs. This is a
LANGUAGE-SCOPED denylist of those exact patterns — each is wrong only in the languages
listed, so it won't false-positive across languages (e.g. `messages.create` + `from_`
are CORRECT in the Python SDK but wrong in Node/Ruby).

    python scripts/review/check_legacy_sdk.py
    python scripts/review/check_legacy_sdk.py --changed-against origin/main   # CI / diff-aware

Exits non-zero on any hit.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# language -> [(pattern, correct-API message)]. A folder's docs (README/API/GUIDE) inherit
# the folder's language. Patterns are only applied to files in matching-language folders.
DENY_BY_LANG = {
    "nodejs": [
        (r"\bTelnyx\.APIStatusError\b", "Telnyx.APIStatusError does not exist — use Telnyx.APIError (.status)"),
        (r"telnyx\.errors\.Telnyx\w+", "v2 error namespace — use Telnyx.<ErrorClass>"),
        (r"\.ai_assistants\b", "use client.ai.assistants.*"),
        (r"\.sipConnections\b", "use client.credentialConnections.*"),
        (r"\.simCards\.activate\b", "use client.simCards.actions.enable"),
        (r"\.messages\.create\(", "Node SDK uses client.messages.send()"),
        (r"\bfrom_:", "Node messaging param is 'from', not 'from_'"),
        (r"require\((['\"])telnyx\1\)\(", "v2 factory init — use new Telnyx({ apiKey })"),
    ],
    "go": [
        (r"github\.com/telnyx/telnyx-go", "wrong module — use github.com/team-telnyx/telnyx-go/v4"),
    ],
    "ruby": [
        (r"\.messages\.create\b", "Ruby SDK uses client.messages.send_"),
        (r"\bTelnyx\.api_key\b", "v2 module API — use Telnyx::Client.new(api_key:)"),
        (r"Telnyx::(Message|Call)\.", "v2 module API — use the Telnyx::Client instance"),
    ],
    "csharp": [
        (r"PackageReference\s+Include=\"Telnyx\"", "wrong NuGet id — use 'Telnyx.net'"),
    ],
    "python": [
        (r"\btelnyx\.(Message|Call|Conference|Number)\.\w", "old module API — use telnyx.Telnyx(...).<resource>"),
        (r"\btelnyx\.api_key\s*=", "old module API — use telnyx.Telnyx(api_key=...)"),
    ],
    "php": [
        (r"->messages->create\(", "PHP SDK uses ->messages->send()"),
    ],
    "java": [],
}
DENY_BY_LANG = {k: [(re.compile(p), m) for p, m in v] for k, v in DENY_BY_LANG.items()}

LANG_SUFFIXES = ("python", "nodejs", "go", "ruby", "php", "java", "csharp")
SCAN_NAMES = {"README.md", "API.md", "GUIDE.md", "app.py", "server.js", "main.go",
              "app.rb", "index.php", "go.mod", "Gemfile", "composer.json"}
SCAN_SUFFIX = (".java", ".cs", ".csproj")
SKIP_DIRS = {".git", "node_modules", "vendor", ".venv", "venv", "dist", "build", "bin", "obj"}


def lang_of(folder_name: str):
    for s in LANG_SUFFIXES:
        if folder_name.endswith(f"-{s}"):
            return s
    return None


def scan_folder(folder: Path, root: Path, patterns) -> list[str]:
    out = []
    for path in sorted(folder.rglob("*")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if not path.is_file() or (path.name not in SCAN_NAMES and path.suffix not in SCAN_SUFFIX):
            continue
        try:
            text = path.read_text(errors="ignore")
        except OSError:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            for rx, msg in patterns:
                if rx.search(line):
                    rel = path.relative_to(root) if path.is_relative_to(root) else path
                    out.append(f"{rel}:{i} — {msg}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Flag known-legacy Telnyx SDK references (language-scoped).")
    ap.add_argument("--path", default=".", help="root to scan (default: cwd)")
    ap.add_argument("--changed-against", metavar="REF",
                    help="diff-aware: only scan example folders changed vs this git ref (CI mode)")
    args = ap.parse_args()

    root = Path(args.path).resolve()
    if args.changed_against:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from _changed import changed_example_dirs
        names = changed_example_dirs(root, args.changed_against)
        if not names:
            print(f"Legacy-SDK check (diff-aware): no example folders changed vs {args.changed_against}.\n\nPASS")
            return 0
        print(f"Legacy-SDK check (diff-aware): {len(names)} changed folder(s) vs {args.changed_against}")
        folders = [root / n for n in names]
    else:
        folders = [p for p in sorted(root.iterdir()) if p.is_dir() and lang_of(p.name)]

    hits = []
    for folder in folders:
        lang = lang_of(folder.name)
        if not lang:
            continue
        hits += scan_folder(folder, root, DENY_BY_LANG.get(lang, []))

    for h in hits:
        print(f"  ✗ {h}")
    print(f"\nLegacy-SDK check: {len(hits)} reference(s) to dead/old SDK APIs")
    if hits:
        print("\nFAIL — replace legacy SDK references (these don't exist in the current SDK for this language).")
        return 1
    print("\nPASS — no legacy SDK references.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
