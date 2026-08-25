#!/usr/bin/env python3
"""Open a pull request as the telnyx-devrel-bot GitHub App.

This module wraps the existing repo scripts (transform.py, verify.py,
fix_required_files.py, gen_llms_txt.py, rewrite_repo_links.py) and the
git/gh CLI to:

  1. branch off main as the bot
  2. stage generated/updated example folders
  3. run pre-PR gates, auto-fixing what's fixable
  4. commit + push as telnyx-devrel-bot[bot]
  5. open a PR with a Linear-ticket-linked body

Designed to be called by the Linear-triggered agent runner, but also
CLI-runnable for manual invocation.

Env vars (in addition to GH_APP_*):
    LINEAR_TICKET_ID    e.g. DEV-908  (optional but recommended for PR body)
    LINEAR_TICKET_URL   Linear issue URL (optional)
    REPO_OWNER         default: team-telnyx
    REPO_NAME          default: telnyx-code-examples
    BASE_BRANCH        default: main
    DRY_RUN            if set, do everything except push/open PR

CLI:
    python scripts/bot/open_pr.py \\
        --branch linear/DEV-908-kv-backed-rate-limiter \\
        --title "Add kv-backed-rate-limiter (DEV-908)" \\
        --body "Generated from Linear DEV-908" \\
        --paths kv-backed-rate-limiter/ scripts/examples_mapping.yaml llms.txt
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(os.environ.get("BOT_REPO_ROOT", os.getcwd()))
# Make sure the bot modules + scripts are importable regardless of CWD.
# REPO_ROOT is the *working* repo (where git commands run); the script's
# own repo (where scripts/bot/ and scripts/*.py live) is for imports.
_SCRIPT_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_SCRIPT_REPO / "scripts" / "bot"))
sys.path.insert(0, str(_SCRIPT_REPO / "scripts"))
from github_app_auth import GitHubAppAuth  # noqa: E402


# ---------------------------------------------------------------------------
# git/gh helpers authenticated as the bot
# ---------------------------------------------------------------------------

def _git_env() -> dict[str, str]:
    """Build an env dict that makes git/gh authenticate as the bot."""
    env = os.environ.copy()
    auth = GitHubAppAuth.from_env()
    token = auth.installation_token()
    env["GH_TOKEN"] = token           # gh CLI reads GH_TOKEN
    env["GH_ENTERPRISE_TOKEN"] = token
    # For git push over HTTPS, encode the token as x-access-token:<token>
    # The .gitconfig "insteadOf" trick pushes https://github.com -> x-access-token@github.com
    return env, token


def run(cmd: list[str], env: Optional[dict] = None, cwd: Optional[Path] = None,
        check: bool = True, capture: bool = False) -> subprocess.CompletedProcess:
    if capture:
        return subprocess.run(cmd, env=env, cwd=cwd, check=check,
                              capture_output=True, text=True)
    return subprocess.run(cmd, env=env, cwd=cwd, check=check)


# ---------------------------------------------------------------------------
# Pre-PR gates — auto-fix what's fixable, then re-check
# ---------------------------------------------------------------------------

GATES = [
    # (description, check_cmd, fix_cmd_or_None)
    ("verify.py (full repo)",
     [sys.executable, "scripts/verify.py"],
     None),
    ("In-repo doc links are absolute raw URLs",
     [sys.executable, "scripts/rewrite_repo_links.py", "--check"],
     [sys.executable, "scripts/rewrite_repo_links.py"]),
    ("llms.txt index in sync",
     [sys.executable, "scripts/gen_llms_txt.py", "--check"],
     [sys.executable, "scripts/gen_llms_txt.py"]),
    ("Required files & no forbidden scaffolding",
     [sys.executable, "scripts/review/check_required_files.py",
      "--changed-against", "origin/main"],
     [sys.executable, "scripts/fix_required_files.py"]),
]


def run_gates_with_autofix(env: dict[str, str]) -> tuple[bool, list[str]]:
    """Return (all_passed, list_of_unfixable_failures)."""
    failures: list[str] = []
    for desc, check, fix in GATES:
        result = run(check, env=env, cwd=REPO_ROOT, check=False, capture=True)
        if result.returncode == 0:
            print(f"  PASS  {desc}")
            continue
        print(f"  FAIL  {desc}")
        if fix is None:
            failures.append(desc)
            continue
        print(f"        auto-fixing: {' '.join(fix)}")
        fix_result = run(fix, env=env, cwd=REPO_ROOT, check=False, capture=True)
        if fix_result.returncode != 0:
            print(fix_result.stdout)
            print(fix_result.stderr, file=sys.stderr)
            failures.append(f"{desc} (autofix failed)")
            continue
        # Re-check after fix
        recheck = run(check, env=env, cwd=REPO_ROOT, check=False, capture=True)
        if recheck.returncode == 0:
            print(f"  PASS  {desc} (after autofix)")
        else:
            failures.append(f"{desc} (still failing after autofix)")
    return (len(failures) == 0, failures)


# ---------------------------------------------------------------------------
# Branch / commit / push / PR
# ---------------------------------------------------------------------------

def open_pr(branch: str, title: str, body: str, paths: list[str],
            base: str = "main", dry_run: bool = False,
            skip_dirty_check: bool = False) -> str:
    """Open a PR as the bot.

    `skip_dirty_check=True` is for callers (e.g. the runner) that have
    *just* generated files into the working tree on purpose and need to
    commit them. Direct CLI users get the dirty-tree guard by default.
    """
    env, token = _git_env()
    owner = os.environ.get("REPO_OWNER", "team-telnyx")
    repo = os.environ.get("REPO_NAME", "telnyx-code-examples")

    if not skip_dirty_check:
        # Refuse to run on a dirty working tree — this script is meant for
        # CI/agent contexts with a clean checkout. Silent stashing would risk
        # clobbering user work in interactive use.
        dirty = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=REPO_ROOT, capture_output=True, text=True,
        ).stdout.strip()
        if dirty:
            raise SystemExit(
                "Working tree is dirty. Refusing to run.\n"
                "Either commit/stash your changes first, or run the bot from a "
                "clean checkout (recommended for CI/agent use):\n\n"
                "  git stash -u  # OR\n"
                "  git clone https://github.com/team-telnyx/telnyx-code-examples "
                "/tmp/bot-run && cd /tmp/bot-run\n\n"
                "Dirty files:\n" + dirty
            )

    # Configure git to push as the bot via HTTPS. Two approaches:
    # 1. Set the remote URL with the token embedded (most reliable in containers)
    # 2. Also set the insteadOf config as a fallback
    remote_url = f"https://x-access-token:{token}@github.com/{owner}/{repo}.git"
    run(["git", "remote", "set-url", "origin", remote_url], env=env, cwd=REPO_ROOT)
    run(["git", "config", "http.https://github.com/.insteadOf",
         f"https://x-access-token:{token}@github.com/"],
        env=env, cwd=REPO_ROOT)

    # Sync main
    run(["git", "fetch", "origin", base, "--depth=1"], env=env, cwd=REPO_ROOT)

    # Branch (delete stale local branch if present)
    if subprocess.run(["git", "rev-parse", "--verify", branch],
                      cwd=REPO_ROOT, capture_output=True).returncode == 0:
        run(["git", "branch", "-D", branch], env=env, cwd=REPO_ROOT)
    run(["git", "switch", "-c", branch, f"origin/{base}"], env=env, cwd=REPO_ROOT)

    # Stage requested paths
    if paths:
        run(["git", "add", "--", *paths], env=env, cwd=REPO_ROOT)

    # If nothing staged, abort cleanly
    diff_status = run(["git", "diff", "--cached", "--name-only"],
                      env=env, cwd=REPO_ROOT, capture=True).stdout.strip()
    if not diff_status:
        print("Nothing staged to commit. Aborting.")
        run(["git", "switch", base], env=env, cwd=REPO_ROOT)
        return ""

    # Pre-PR gates (run after staging so autofixes are included in this commit)
    print("Running pre-PR gates (auto-fixing where possible)...")
    all_passed, failures = run_gates_with_autofix(env)

    # Re-stage anything autofix touched
    if paths:
        run(["git", "add", "--", *paths], env=env, cwd=REPO_ROOT)
    else:
        run(["git", "add", "-A"], env=env, cwd=REPO_ROOT)

    # Commit as the bot. Git author identity is forced via -c flags; the App
    # email format is <app-id>+<slug>[bot]@users.noreply.github.com.
    app_id = os.environ["GH_APP_ID"]
    bot_name = "telnyx-devrel-bot[bot]"
    bot_email = f"{app_id}+telnyx-devrel-bot[bot]@users.noreply.github.com"
    commit_env = env.copy()
    commit_env["GIT_AUTHOR_NAME"] = bot_name
    commit_env["GIT_AUTHOR_EMAIL"] = bot_email
    commit_env["GIT_COMMITTER_NAME"] = bot_name
    commit_env["GIT_COMMITTER_EMAIL"] = bot_email

    files = diff_status.split("\n")
    commit_msg = f"{title}\n\n{body}"
    if failures:
        commit_msg += "\n\n⚠️ Pre-PR gates that did not pass:\n- " + "\n- ".join(failures)

    run(["git", "commit", "-m", commit_msg], env=commit_env, cwd=REPO_ROOT)
    print(f"Committed {len(files)} file(s) as {bot_name}")

    if dry_run:
        print("DRY_RUN=1 — skipping push and PR creation.")
        run(["git", "switch", base], env=env, cwd=REPO_ROOT)
        return ""

    # Push the branch
    run(["git", "push", "--force-with-lease", "origin", branch],
        env=env, cwd=REPO_ROOT)
    print(f"Pushed {branch}")

    # Build PR body
    pr_body = body
    if failures:
        pr_body += (
            "\n\n---\n\n> ⚠️ **Pre-PR gate status**: This PR was opened by "
            "`telnyx-devrel-bot[bot]` with the following gates not passing "
            "locally. Reviewer should confirm CI below is green before merge:\n"
            + "\n".join(f"- ❌ {f}" for f in failures)
        )
    else:
        pr_body += "\n\n---\n\n> ✅ All pre-PR gates passed locally before this PR was opened."

    linear_url = os.environ.get("LINEAR_TICKET_URL")
    if linear_url:
        pr_body += f"\n\nLinear: {linear_url}"

    # Open the PR via GitHub REST API (no gh CLI dependency — works in
    # containers like the ACP Hermes runtime where gh is not installed).
    pr_url = _create_pr_via_api(token, owner, repo, base, branch, title, pr_body)
    print(f"Opened PR: {pr_url}")
    return pr_url


def _create_pr_via_api(token: str, owner: str, repo: str,
                       base: str, head: str, title: str, body: str) -> str:
    """Create a PR + add label via the GitHub REST API (no gh CLI needed)."""
    import json as _json
    import urllib.request as _urlreq
    import urllib.error as _urlerr

    api = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    payload = _json.dumps({
        "title": title,
        "head": head,
        "base": base,
        "body": body,
    }).encode()
    req = _urlreq.Request(api, data=payload, method="POST", headers={
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
    })
    try:
        with _urlreq.urlopen(req) as resp:
            data = _json.loads(resp.read().decode())
    except _urlerr.HTTPError as e:
        err = e.read().decode()
        raise RuntimeError(f"GitHub PR create failed: {e.code} {err}") from e

    pr_url = data["html_url"]
    pr_num = data["number"]

    # Add the code-samples label
    label_api = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_num}/labels"
    label_payload = _json.dumps({"labels": ["code-samples"]}).encode()
    label_req = _urlreq.Request(label_api, data=label_payload, method="POST", headers={
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
    })
    try:
        _urlreq.urlopen(label_req).read()
    except _urlerr.HTTPError:
        pass  # label might already exist or fail — non-fatal

    return pr_url


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--branch", required=True, help="Branch name to create")
    p.add_argument("--title", required=True, help="PR title")
    p.add_argument("--body", default="Generated by telnyx-devrel-bot.",
                   help="PR body markdown")
    p.add_argument("--paths", nargs="*", default=[],
                   help="Paths to stage (default: stage from diff)")
    p.add_argument("--base", default=os.environ.get("BASE_BRANCH", "main"))
    p.add_argument("--dry-run", action="store_true",
                   help="Do everything except push/open PR")
    args = p.parse_args()

    pr_url = open_pr(args.branch, args.title, args.body, args.paths,
                     base=args.base, dry_run=args.dry_run)
    if pr_url:
        print(pr_url)
    return 0


if __name__ == "__main__":
    sys.exit(main())
