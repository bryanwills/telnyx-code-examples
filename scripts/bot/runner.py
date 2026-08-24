#!/usr/bin/env python3
"""End-to-end runner: Linear ticket → LLM-generated code sample → PR by the bot.

Pipeline:
  1. Fetch the Linear ticket (via linear_client)
  2. Parse sample name + language from the ticket
  3. Generate the sample folder via generate_sample (two-phase LLM call)
  4. Stage the new folder + register in examples_mapping.yaml + regen llms.txt
  5. Run pre-PR gates with auto-fix
  6. Branch → commit → push → open PR as telnyx-devrel-bot[bot]
  7. Update Linear: move to "In Review" + comment with PR URL

Env vars (in addition to GH_APP_*, LINEAR_API_KEY, TELNYX_API_KEY):
    DRY_RUN            if set, do everything except push/open PR + Linear update
    BOT_REPO_ROOT      working repo path (defaults to cwd; for CI use a clean clone)

CLI:
    # Dry-run on a real ticket (no PR, no Linear state change):
    python scripts/bot/runner.py --ticket DEV-808

    # Real run (opens PR + moves Linear to In Review):
    python scripts/bot/runner.py --ticket DEV-808 --no-dry-run
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

# Make sibling bot modules + scripts importable
SCRIPT_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SCRIPT_REPO / "scripts" / "bot"))
sys.path.insert(0, str(SCRIPT_REPO / "scripts"))

import linear_client       # noqa: E402
import generate_sample     # noqa: E402
from open_pr import open_pr  # noqa: E402


# ---------------------------------------------------------------------------
# examples_mapping.yaml registration
# ---------------------------------------------------------------------------

def register_in_mapping(folder_name: str, language: str, framework: str,
                        product_category: str = "Voice AI",
                        mapping_path: Path | None = None,
                        repo_root: Path | None = None) -> bool:
    """Append an entry for the new folder to scripts/examples_mapping.yaml.

    Returns True if a new entry was added, False if it already existed.

    `mapping_path` defaults to `<repo_root>/scripts/examples_mapping.yaml`
    so the bot edits the *working* repo's mapping file (e.g. a CI clone),
    NOT the source repo where the bot code lives.

    Existing entries are indented 2 spaces under the top-level `examples:` key.
    """
    if mapping_path is None:
        root = repo_root or Path(os.environ.get("BOT_REPO_ROOT", os.getcwd()))
        mapping_path = root / "scripts" / "examples_mapping.yaml"
    text = mapping_path.read_text()

    # Naive check: folder name already in file?
    if re.search(rf"^\s*folder:\s*{re.escape(folder_name)}\s*$", text, re.MULTILINE):
        return False

    # Match existing format: 2-space indent under `examples:`. The product
    # key must be one of {voice, sms, verify, ai, sip, iot} — those are the
    # categories gen_llms_txt.py recognizes. Default to "ai" (AI Assistants)
    # since most LLM-generated samples compose multiple primitives.
    valid_products = {"voice", "sms", "verify", "ai", "sip", "iot"}
    product_key = product_category.lower().replace(" ", "-")
    if product_key not in valid_products:
        product_key = "ai"
    entry = f"""
  - product: {product_key}
    use_case: "auto-generated-from-linear"
    language: {language}
    framework: {framework}
    folder: {folder_name}
"""
    mapping_path.write_text(text.rstrip() + "\n" + entry)
    return True


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def run_pipeline(ticket_id: str, dry_run: bool = True,
                 repo_root: Path | None = None) -> dict:
    """Run the full pipeline for one Linear ticket. Returns a result dict."""
    repo_root = repo_root or Path(os.environ.get("BOT_REPO_ROOT", os.getcwd()))

    # 1. Fetch Linear ticket
    print(f"=== 1. Fetching Linear ticket {ticket_id} ===")
    issue = linear_client.fetch_issue(ticket_id)
    parsed = linear_client.parse_sample_ticket(issue)
    if not parsed.sample_name:
        # Fallback: parse from description's "## Sample: `name`" line
        m = re.search(r"##\s*Sample:\s*`?([a-z0-9][a-z0-9\-]+)`?", parsed.description or "", re.I)
        if m:
            parsed = linear_client.SampleTicket(
                **{**parsed.__dict__,
                   "sample_name": m.group(1),
                   "branch": f"linear/{parsed.issue_id}-{m.group(1)}",
                   "is_sample_ticket": True}
            )
        else:
            raise SystemExit(
                f"Could not determine sample name from ticket {ticket_id}. "
                f"Title: {parsed.title!r}\nDescription:\n{parsed.description[:500]}"
            )

    print(f"  sample:  {parsed.sample_name}")
    print(f"  branch:  {parsed.branch}")
    print(f"  lang:    {parsed.language}")
    print(f"  url:     {parsed.url}")

    sample_dir = repo_root / parsed.sample_name
    if sample_dir.exists():
        print(f"\n⚠️  Folder already exists: {sample_dir}")
        print("   (Re-running would overwrite. Aborting for safety.)")
        return {"status": "aborted_exists", "sample_dir": str(sample_dir)}

    # 2. Generate sample via LLM
    print(f"\n=== 2. Generating sample folder via Telnyx Inference ===")
    generate_sample.generate_sample(
        ticket_id=parsed.issue_id,
        ticket_title=parsed.title,
        ticket_description=parsed.description,
        folder_name=parsed.sample_name,
        language=parsed.language or "python",
        framework="flask",
        out_dir=sample_dir,
    )

    # 3. Register in examples_mapping.yaml + regen llms.txt
    print(f"\n=== 3. Registering in examples_mapping.yaml ===")
    added = register_in_mapping(parsed.sample_name, parsed.language or "python", "flask",
                                 repo_root=repo_root)
    print(f"  mapping entry {'added' if added else 'already present'}")

    # 4. Run pre-PR gates (verify, rewrite_repo_links, sync_readme, gen_llms_txt) with auto-fix
    print(f"\n=== 4. Running pre-PR gates (auto-fixing) ===")
    gate_env = os.environ.copy()
    for cmd_desc, cmd in [
        ("rewrite_repo_links (auto-convert)",
         [sys.executable, "scripts/rewrite_repo_links.py"]),
        ("sync_readme (regenerate root README)",
         [sys.executable, "scripts/sync_readme.py"]),
        ("gen_llms_txt (regenerate index)",
         [sys.executable, "scripts/gen_llms_txt.py"]),
    ]:
        r = subprocess.run(cmd, cwd=repo_root, env=gate_env,
                           capture_output=True, text=True)
        status = "ok" if r.returncode == 0 else f"fail (exit {r.returncode})"
        print(f"  {cmd_desc}: {status}")
        if r.returncode != 0 and r.stderr:
            print(f"    stderr: {r.stderr[:300]}")

    # 5. Open PR (or stop at dry-run)
    paths_to_stage = [
        f"{parsed.sample_name}/",
        "scripts/examples_mapping.yaml",
        "llms.txt",
        "README.md",
    ]
    title = f"Add {parsed.sample_name} ({parsed.issue_id})"
    body = (
        f"Generated by `telnyx-devrel-bot[bot]` from Linear ticket "
        f"{parsed.issue_id}.\n\n"
        f"**Linear**: {parsed.url}\n\n"
        f"**Ticket title**: {parsed.title}\n\n"
        f"---\n\n"
        f"This PR was generated by an LLM (Telnyx Inference) using the ticket "
        f"spec above. Please review the generated code carefully before merge."
    )

    if dry_run:
        print(f"\n=== 5. DRY RUN — would open PR ===")
        print(f"  branch: {parsed.branch}")
        print(f"  title:  {title}")
        print(f"  paths:  {paths_to_stage}")
        print(f"\nGenerated files at: {sample_dir}")
        print(f"\nTo open a real PR, re-run with --no-dry-run.")
        return {
            "status": "dry_run",
            "ticket_id": parsed.issue_id,
            "sample_name": parsed.sample_name,
            "sample_dir": str(sample_dir),
            "branch": parsed.branch,
            "title": title,
        }

    print(f"\n=== 5. Opening PR as bot ===")
    pr_url = open_pr(
        branch=parsed.branch,
        title=title,
        body=body,
        paths=paths_to_stage,
        # The runner just generated files into the working tree — that's
        # the whole point. The dirty-tree guard in open_pr is for direct
        # CLI use; the runner bypasses it.
        skip_dirty_check=True,
    )

    # 6. Update Linear
    if pr_url:
        print(f"\n=== 6. Updating Linear (In Review + PR link) ===")
        linear_client.link_pr(parsed.issue_uuid, pr_url, parsed.branch,
                               parsed.sample_name)
        print(f"  Linear ticket {parsed.issue_id} moved to In Review.")

    return {
        "status": "ok",
        "ticket_id": parsed.issue_id,
        "sample_name": parsed.sample_name,
        "sample_dir": str(sample_dir),
        "branch": parsed.branch,
        "pr_url": pr_url,
    }


def main() -> int:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--ticket", required=True, help="Linear ticket ID (e.g. DEV-808)")
    p.add_argument("--no-dry-run", dest="dry_run", action="store_false",
                   help="Open a real PR (default is dry-run)")
    p.set_defaults(dry_run=True)
    args = p.parse_args()

    result = run_pipeline(args.ticket, dry_run=args.dry_run)
    print(f"\n=== Result ===")
    for k, v in result.items():
        print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
