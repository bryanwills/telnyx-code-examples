#!/usr/bin/env python3
"""Generate AEO syndication content for a code sample and push to devrel-internal.

When a code sample PR merges to telnyx-code-examples/main, this module:
1. Reads the merged sample's README + code from telnyx-code-examples
2. Generates 5 syndication files via LLM (README, blog-post, medium, HN, YouTube)
3. Opens a PR in devrel-internal/aeo/<assignee>-aeo/<sample-name>/

Env vars:
    GH_APP_ID, GH_APP_PRIVATE_KEY_PATH (or APP_PRIVATE_KEY) — GitHub App auth
    LINEAR_API_KEY — to determine assignee → which -aeo folder
    LITELLM_API_KEY or TELNYX_API_KEY — for LLM generation
    AI_MODEL — model name (default: GLM-5.2-NVFP4 on LiteLLM, deepseek-ai/DeepSeek-V4-Flash-0731 on Telnyx)

CLI:
    python scripts/bot/syndicate.py --sample ai-call-campaign-orchestrator --assignee sonam --no-dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

# Make sibling bot modules importable
SCRIPT_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SCRIPT_REPO / "scripts" / "bot"))
from github_app_auth import GitHubAppAuth  # noqa: E402
from generate_sample import _resolve_inference_config, call_inference  # noqa: E402
from pr_body import render_syndication_body  # noqa: E402


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

CODE_EXAMPLES_REPO = ("team-telnyx", "telnyx-code-examples")
DEVREL_REPO = ("team-telnyx", "devrel-internal")

# Assignee → AEO folder mapping
AEO_FOLDERS = {
    "sonam": "sonam-aeo",
    "anusha": "anusha-aeo",
    "harpreet": "harpreet-aeo",
    "steve": "steve-aeo",
    "stephen": "steve-aeo",
}


# ---------------------------------------------------------------------------
# GitHub API helpers (use the App token, not gh CLI)
# ---------------------------------------------------------------------------

def _gh_token() -> str:
    auth = GitHubAppAuth.from_env()
    return auth.installation_token()


def _gh_get(token: str, url: str) -> dict:
    req = urllib.request.Request(url, headers={
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    })
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def _gh_get_file(token: str, owner: str, repo: str, path: str, ref: str = "main") -> str:
    """Download a file from a GitHub repo."""
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={ref}"
    data = _gh_get(token, url)
    import base64
    return base64.b64decode(data["content"]).decode()


def _gh_create_branch(token: str, owner: str, repo: str, branch: str, base: str = "main") -> str:
    """Create a branch from base. Returns the new branch SHA."""
    base_data = _gh_get(token, f"https://api.github.com/repos/{owner}/{repo}/branches/{base}")
    base_sha = base_data["commit"]["sha"]
    url = f"https://api.github.com/repos/{owner}/{repo}/git/refs"
    payload = json.dumps({"ref": f"refs/heads/{branch}", "sha": base_sha}).encode()
    req = urllib.request.Request(url, data=payload, method="POST", headers={
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())["object"]["sha"]
    except urllib.error.HTTPError as e:
        if e.code == 422:
            # Branch already exists — return its current SHA
            existing = _gh_get(token, f"https://api.github.com/repos/{owner}/{repo}/branches/{branch}")
            return existing["commit"]["sha"]
        raise


def _gh_create_or_update_file(token: str, owner: str, repo: str,
                               path: str, content: str, branch: str,
                               message: str) -> dict:
    """Create or update a file via the contents API."""
    import base64
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    # Check if file exists (to get its SHA for update)
    sha = None
    try:
        existing = _gh_get(token, f"{url}?ref={branch}")
        sha = existing.get("sha")
    except urllib.error.HTTPError:
        pass  # file doesn't exist yet

    payload = json.dumps({
        "message": message,
        "content": base64.b64encode(content.encode()).decode(),
        "branch": branch,
        **({"sha": sha} if sha else {}),
    }).encode()
    req = urllib.request.Request(url, data=payload, method="PUT", headers={
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def _gh_create_pr(token: str, owner: str, repo: str,
                  base: str, head: str, title: str, body: str) -> str:
    """Create a PR via the REST API. Returns the PR URL."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    payload = json.dumps({
        "title": title, "head": head, "base": base, "body": body,
    }).encode()
    req = urllib.request.Request(url, data=payload, method="POST", headers={
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
    return data["html_url"]


# ---------------------------------------------------------------------------
# Syndication content generation
# ---------------------------------------------------------------------------

SYNDICATION_PROMPT = """You are generating AEO syndication content for a Telnyx code sample.

The code sample is: `{sample_name}`
From repo: https://github.com/team-telnyx/telnyx-code-examples/tree/main/{sample_name}

Here is the sample's README.md (the source of truth for what the sample does):

---
{readme_content}
---

Generate FIVE files for the syndication package. Use the sentinel format:
=== FILE: README.md ===
<content>

=== FILE: blog-post.md ===
<content>

=== FILE: medium-article.md ===
<content>

=== FILE: hackernews-post.md ===
<content>

=== FILE: youtube-script.md ===
<content>

=== END ===

**README.md** — Syndication package overview. Format:
- H1 title: "<Sample Name> - Syndication Package"
- One paragraph: what the sample does + link to the code repo
- "## Pillar Alignment" — which of the three Telnyx GTM pillars (Physics/Infrastructure/Trust) this supports
- "## Contents" — table listing the 5 files with their platform + purpose + length
- "## Content Strategy" — one paragraph on how the content will be distributed

**blog-post.md** — Technical walkthrough for Telnyx Blog / Dev.to (~1,200-1,600 words).
- H1 title, intro hook, "## What the App Does", "## How It Works", "## Setup", code snippets, conclusion
- Written for developers who want to build something similar

**medium-article.md** — Narrative developer story for Medium (~800-1,100 words).
- More conversational tone, personal angle, "I built X with Telnyx" style
- Focus on the problem → solution → why Telnyx

**hackernews-post.md** — Concise Show HN post (~300-500 words).
- Title + body for a Show HN submission
- Technical, concise, links to the code + live demo if applicable

**youtube-script.md** — Demo-driven script for a YouTube video (8-10 min).
- Section headers with timestamps
- Voiceover text + B-roll/cutaway instructions
- Ends with CTA to the code repo

All content should reference "AI Communications Infrastructure" where natural.
Do not mention competitors. The audience is developers and developer advocates.
"""


def generate_syndication(sample_name: str, readme_content: str) -> dict[str, str]:
    """Generate the 5 syndication files via LLM."""
    from generate_sample import extract_files_from_response

    prompt = SYNDICATION_PROMPT.format(
        sample_name=sample_name,
        readme_content=readme_content[:8000],  # cap to avoid token overflow
    )
    print(f"  Generating syndication content via LLM...")
    response = call_inference(
        [
            {"role": "system", "content": "You generate AEO syndication content for Telnyx developer relations."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=12000,
        temperature=0.4,
    )
    files = extract_files_from_response(response, "README", ".md")
    if not files:
        # Save raw for debugging
        Path("/tmp/syndication_raw.md").write_text(response)
        raise RuntimeError("Syndication generation produced no parseable files. Raw saved to /tmp/syndication_raw.md")
    return files


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def syndicate(sample_name: str, assignee: str, dry_run: bool = False) -> str:
    """Generate syndication content and open a PR in devrel-internal."""
    token = _gh_token()
    aeo_folder = AEO_FOLDERS.get(assignee.lower())
    if not aeo_folder:
        raise SystemExit(f"Unknown assignee: {assignee}. Known: {list(AEO_FOLDERS.keys())}")

    print(f"=== Syndicating {sample_name} → devrel-internal/aeo/{aeo_folder}/{sample_name}/ ===")

    # 1. Fetch the sample's README from telnyx-code-examples
    print("  Fetching README from telnyx-code-examples...")
    readme = _gh_get_file(token, *CODE_EXAMPLES_REPO, f"{sample_name}/README.md")

    # 2. Generate syndication content
    files = generate_syndication(sample_name, readme)
    print(f"  Generated {len(files)} files:")
    for name, content in files.items():
        print(f"    {name}: {len(content)} bytes")

    if dry_run:
        # Write to /tmp for review
        out_dir = Path(f"/tmp/syndication-{sample_name}")
        out_dir.mkdir(parents=True, exist_ok=True)
        for name, content in files.items():
            (out_dir / name).write_text(content)
        print(f"\n  DRY RUN — files written to {out_dir}/")
        return ""

    # 3. Create branch in devrel-internal
    branch = f"syndicate/{sample_name}"
    print(f"  Creating branch {branch} in devrel-internal...")
    _gh_create_branch(token, *DEVREL_REPO, branch)

    # 4. Write files to devrel-internal
    base_path = f"aeo/{aeo_folder}/{sample_name}"
    for name, content in files.items():
        file_path = f"{base_path}/{name}"
        print(f"  Writing {file_path}...")
        _gh_create_or_update_file(
            token, *DEVREL_REPO, file_path, content, branch,
            f"Add syndication content for {sample_name}: {name}"
        )

    # 5. Open PR
    pr_title = f"Add AEO syndication for {sample_name}"
    source_url = f"https://github.com/team-telnyx/telnyx-code-examples/tree/main/{sample_name}"
    pr_body = render_syndication_body(
        sample_name=sample_name,
        assignee=assignee,
        source_url=source_url,
        generated_files=list(files),
    )
    pr_url = _gh_create_pr(token, *DEVREL_REPO, "main", branch, pr_title, pr_body)
    print(f"  Opened PR: {pr_url}")
    return pr_url


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--sample", required=True, help="Sample folder name (e.g. ai-call-campaign-orchestrator)")
    p.add_argument("--assignee", required=True, help="Assignee (sonam, anusha, harpreet, steve)")
    p.add_argument("--no-dry-run", dest="dry_run", action="store_false")
    p.set_defaults(dry_run=True)
    args = p.parse_args()

    pr_url = syndicate(args.sample, args.assignee, dry_run=args.dry_run)
    if pr_url:
        print(f"\nPR: {pr_url}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
