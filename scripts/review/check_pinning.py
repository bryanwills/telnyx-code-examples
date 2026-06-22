#!/usr/bin/env python3
"""check_pinning.py — flag unpinned / "latest" dependencies across every ecosystem.

Part of the PR-review toolkit (scripts/review/). Codifies the manual scan behind
PR #11: the "latest" + no-lockfile anti-pattern is what generated 75 Dependabot
alerts, and invalid `latest` in go.mod won't even build.

Run on any checkout/branch/PR worktree:

    python scripts/review/check_pinning.py                 # whole repo
    python scripts/review/check_pinning.py --path some-dir  # one subtree
    python scripts/review/check_pinning.py --verbose

Exits non-zero when any hard finding is present, so it can gate CI directly.
Ecosystems: npm (package.json), pip (requirements.txt), Go (go.mod), Ruby
(Gemfile), PHP (composer.json), .NET (*.csproj), Maven (pom.xml).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# A finding: (severity, ecosystem, file, dependency, detail)
# severity: "error" fails the run; "warn" is reported but does not fail.
Finding = tuple


def _rel(p: Path, root: Path) -> str:
    try:
        return str(p.relative_to(root))
    except ValueError:
        return str(p)


# --- npm -------------------------------------------------------------------
BAD_NPM = {"latest", "*", "", "x", "X"}


def check_package_json(path: Path, root: Path) -> list:
    out = []
    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as e:
        return [("warn", "npm", _rel(path, root), "-", f"unreadable: {e}")]
    for section in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
        for name, spec in (data.get(section) or {}).items():
            if not isinstance(spec, str):
                continue
            s = spec.strip()
            if s in BAD_NPM or s.lower() == "latest":
                out.append(("error", "npm", _rel(path, root), f"{name} ({section})", f'"{spec}" — unpinned'))
    return out


# --- pip -------------------------------------------------------------------
PIN_OPS = ("==", ">=", "<=", "~=", "!=", "===", "<", ">", "@")


def check_requirements_txt(path: Path, root: Path) -> list:
    out = []
    try:
        lines = path.read_text().splitlines()
    except OSError as e:
        return [("warn", "pip", _rel(path, root), "-", f"unreadable: {e}")]
    for i, raw in enumerate(lines, 1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if line.startswith(("-r ", "-c ", "--", "-e ", "git+", "http://", "https://")):
            continue
        # strip environment markers / extras for the pin check
        core = line.split(";", 1)[0].strip()
        if any(op in core for op in PIN_OPS):
            continue
        # bare "package" or "package[extra]" with no version
        name = re.split(r"[\[<>=!~ ]", core, 1)[0]
        if name:
            out.append(("error", "pip", _rel(path, root), name, f"line {i}: no version specifier"))
    return out


# --- Go --------------------------------------------------------------------
def check_go_mod(path: Path, root: Path) -> list:
    out = []
    try:
        text = path.read_text()
    except OSError as e:
        return [("warn", "go", _rel(path, root), "-", f"unreadable: {e}")]
    in_block = False
    for raw in text.splitlines():
        line = raw.split("//", 1)[0].strip()
        if not line:
            continue
        if line.startswith("require ("):
            in_block = True
            continue
        if in_block and line == ")":
            in_block = False
            continue
        entry = None
        if in_block:
            entry = line
        elif line.startswith("require "):
            entry = line[len("require "):].strip()
        if not entry:
            continue
        parts = entry.split()
        if len(parts) >= 2:
            mod, ver = parts[0], parts[1]
            if ver == "latest" or not re.match(r"^v\d+\.\d+\.\d+", ver):
                out.append(("error", "go", _rel(path, root), mod, f'version "{ver}" — not a pinned semver'))
    return out


# --- Ruby ------------------------------------------------------------------
GEM_RE = re.compile(r"""^\s*gem\s+['"]([^'"]+)['"](.*)$""")


def check_gemfile(path: Path, root: Path) -> list:
    out = []
    try:
        lines = path.read_text().splitlines()
    except OSError as e:
        return [("warn", "ruby", _rel(path, root), "-", f"unreadable: {e}")]
    for i, raw in enumerate(lines, 1):
        line = raw.split("#", 1)[0]
        m = GEM_RE.match(line)
        if not m:
            continue
        name, rest = m.group(1), m.group(2)
        # a version constraint appears as a second quoted string after a comma
        if re.search(r""",\s*['"][^'"]*\d""", rest):
            continue
        out.append(("error", "ruby", _rel(path, root), name, f"line {i}: no version constraint"))
    return out


# --- PHP -------------------------------------------------------------------
def check_composer_json(path: Path, root: Path) -> list:
    out = []
    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as e:
        return [("warn", "php", _rel(path, root), "-", f"unreadable: {e}")]
    for section in ("require", "require-dev"):
        for name, spec in (data.get(section) or {}).items():
            if name.lower() == "php" or "/" not in name:  # platform reqs / ext-*
                continue
            s = str(spec).strip().lower()
            if s in ("*", "latest", ""):
                out.append(("error", "php", _rel(path, root), name, f'"{spec}" — unpinned'))
    return out


# --- .NET ------------------------------------------------------------------
def check_csproj(path: Path, root: Path) -> list:
    out = []
    try:
        tree = ET.parse(path)
    except (ET.ParseError, OSError) as e:
        return [("warn", "dotnet", _rel(path, root), "-", f"unreadable: {e}")]
    for ref in tree.iter():
        if ref.tag.split("}")[-1] != "PackageReference":
            continue
        name = ref.get("Include") or ref.get("Update") or "?"
        ver = ref.get("Version")
        if ver is None:
            # may be a child <Version> element
            child = next((c for c in ref if c.tag.split("}")[-1] == "Version"), None)
            ver = child.text if child is not None else None
        if not ver or not ver.strip():
            out.append(("error", "dotnet", _rel(path, root), name, "no Version"))
    return out


# --- Maven -----------------------------------------------------------------
def check_pom_xml(path: Path, root: Path) -> list:
    out = []
    try:
        tree = ET.parse(path)
    except (ET.ParseError, OSError) as e:
        return [("warn", "maven", _rel(path, root), "-", f"unreadable: {e}")]
    ns = {"m": "http://maven.apache.org/POM/4.0.0"}
    deps = tree.findall(".//m:dependencies/m:dependency", ns) or tree.findall(".//dependencies/dependency")
    for d in deps:
        gid = d.findtext("m:groupId", default=d.findtext("groupId", ""), namespaces=ns)
        aid = d.findtext("m:artifactId", default=d.findtext("artifactId", "?"), namespaces=ns)
        ver = d.findtext("m:version", default=d.findtext("version", None), namespaces=ns)
        if not ver:
            # could be managed by a parent/BOM — warn rather than fail
            out.append(("warn", "maven", _rel(path, root), f"{gid}:{aid}", "no <version> (may be managed by a BOM)"))
        elif ver.strip().upper() in ("LATEST", "RELEASE"):
            out.append(("error", "maven", _rel(path, root), f"{gid}:{aid}", f"version {ver}"))
    return out


HANDLERS = [
    ("package.json", check_package_json),
    ("requirements.txt", check_requirements_txt),
    ("go.mod", check_go_mod),
    ("Gemfile", check_gemfile),
    ("composer.json", check_composer_json),
    ("pom.xml", check_pom_xml),
]
SKIP_DIRS = {".git", "node_modules", "vendor", ".venv", "venv", "dist", "build", "bin", "obj"}


def scan(root: Path, subdirs=None) -> list:
    findings = []
    bases = [root / d for d in subdirs] if subdirs is not None else [root]
    for base in bases:
        for path in sorted(base.rglob("*")):
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            if not path.is_file():
                continue
            name = path.name
            if name.endswith(".csproj"):
                findings += check_csproj(path, root)
                continue
            for fname, handler in HANDLERS:
                if name == fname:
                    findings += handler(path, root)
                    break
    return findings


def main() -> int:
    ap = argparse.ArgumentParser(description="Flag unpinned / 'latest' dependencies across ecosystems.")
    ap.add_argument("--path", default=".", help="root to scan (default: cwd)")
    ap.add_argument("--changed-against", metavar="REF",
                    help="diff-aware: only check example folders changed vs this git ref (CI mode)")
    ap.add_argument("--verbose", action="store_true", help="list every finding (default groups by ecosystem)")
    args = ap.parse_args()

    root = Path(args.path).resolve()
    subdirs = None
    if args.changed_against:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from _changed import changed_example_dirs
        subdirs = changed_example_dirs(root, args.changed_against)
        if not subdirs:
            print(f"Pinning check (diff-aware): no example folders changed vs {args.changed_against}.\n\nPASS")
            return 0
        print(f"Pinning check (diff-aware): {len(subdirs)} changed folder(s) vs {args.changed_against}")
    findings = scan(root, subdirs)
    errors = [f for f in findings if f[0] == "error"]
    warns = [f for f in findings if f[0] == "warn"]

    by_eco: dict[str, int] = {}
    for sev, eco, *_ in findings:
        if sev == "error":
            by_eco[eco] = by_eco.get(eco, 0) + 1

    if args.verbose or errors:
        for sev, eco, fpath, dep, detail in findings:
            if sev == "error" or args.verbose:
                mark = "✗" if sev == "error" else "·"
                print(f"  {mark} [{eco}] {fpath}: {dep} — {detail}")

    print("\nPinning check:")
    print(f"  unpinned (errors): {len(errors)}" + (f"  {by_eco}" if by_eco else ""))
    print(f"  warnings:          {len(warns)} (e.g. Maven versions possibly managed by a BOM)")
    if errors:
        print("\nFAIL — pin every dependency to a concrete safe version (no 'latest'/bare names).")
        return 1
    print("\nPASS — all dependencies are pinned.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
