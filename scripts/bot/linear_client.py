#!/usr/bin/env python3
"""Linear client for the DevRel code-samples bot.

Reads tickets from a `Code Samples Week N` project on the DEV team,
parses the sample name + spec from the ticket, and (when called by the
runner) updates ticket state and links the PR back to Linear.

Scope is intentionally small:
  - find_active_code_samples_week_projects() — list active Weeks
  - list_tickets_for_project(project_id) — issues in a Week project
  - parse_sample_ticket(issue) — extract {sample_name, language, spec}
  - move_to_in_review(issue_id, pr_url) — state + comment
  - move_to_done(issue_id, pr_url) — state + comment

Env vars:
    LINEAR_API_KEY   Linear personal API key (already in your env)

CLI:
    python scripts/bot/linear_client.py weeks
    python scripts/bot/linear_client.py tickets <project-id>
    python scripts/bot/linear_client.py ticket <issue-id>
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.request
import urllib.error
from dataclasses import dataclass
from typing import Optional

LINEAR_API = "https://api.linear.app/graphql"


def _gql(query: str, variables: Optional[dict] = None) -> dict:
    """POST a GraphQL query to Linear using LINEAR_API_KEY."""
    key = os.environ.get("LINEAR_API_KEY")
    if not key:
        raise SystemExit("LINEAR_API_KEY env var not set")
    body = {"query": query}
    if variables:
        body["variables"] = variables
    req = urllib.request.Request(
        LINEAR_API,
        data=json.dumps(body).encode(),
        method="POST",
        headers={
            "Authorization": key,
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        raise RuntimeError(f"Linear API error {e.code}: {err}") from e


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------

DEV_TEAM_ID = "8d84b6e1-cfb7-4f7a-862b-3635c93e56de"  # DEV / Engineering


def find_code_samples_week_projects() -> list[dict]:
    """Return all 'Code Samples Week N' projects (any state), sorted by N."""
    q = """
    {
      projects(filter: { name: { containsIgnoreCase: "Code Samples Week" } }) {
        nodes { id name state }
      }
    }
    """
    data = _gql(q)
    nodes = data["data"]["projects"]["nodes"]

    def week_num(p: dict) -> int:
        m = re.search(r"Week (\d+)", p["name"])
        return int(m.group(1)) if m else 999

    return sorted(nodes, key=week_num)


def list_tickets_for_project(project_id: str) -> list[dict]:
    """Return all issues in a Week project with the fields the bot needs."""
    q = """
    query ($id: String!) {
      project(id: $id) {
        id name
        issues { nodes {
          id identifier title url
          state { name }
          assignee { name }
          labels { nodes { name } }
          description
        } }
      }
    }
    """
    data = _gql(q, {"id": project_id})
    return data["data"]["project"]["issues"]["nodes"]


def fetch_issue(issue_id_or_uuid: str) -> dict:
    """Fetch a single Linear issue by short identifier (e.g. DEV-808) or UUID."""
    # Linear accepts the short identifier as the `id` argument for Issue queries.
    if "-" in issue_id_or_uuid and not issue_id_or_uuid.startswith("$"):
        q = """
        query ($id: String!) {
          issue(id: $id) {
            id identifier title url
            state { name }
            assignee { name }
            labels { nodes { name } }
            description
          }
        }
        """
    else:
        q = """
        query ($id: ID!) {
          issue(id: $id) {
            id identifier title url
            state { name }
            assignee { name }
            labels { nodes { name } }
            description
          }
        }
        """
    data = _gql(q, {"id": issue_id_or_uuid})
    if "errors" in data:
        raise RuntimeError(f"Linear fetch failed for {issue_id_or_uuid}: {data['errors']}")
    return data["data"]["issue"]


@dataclass
class SampleTicket:
    """Parsed code-sample ticket ready for transform.py / open_pr.py."""
    issue_id: str          # e.g. "DEV-908"
    issue_uuid: str        # Linear UUID
    title: str
    sample_name: str       # e.g. "kv-backed-rate-limiter"
    language: Optional[str]  # python | nodejs | go | ruby | ... (inferred)
    branch: str            # e.g. linear/DEV-908-kv-backed-rate-limiter
    state: str
    url: str
    description: str
    is_sample_ticket: bool  # True if title matches "Add sample to repo"


# Titles we treat as "build this code sample" tickets:
# - "[DEV-XXX] Add sample to repo — <name>"
# - "[Sprint N] <Name> — ..."
# - "[DEV-XXX] Build the `<name>` code sample ..."
SAMPLE_TITLE_PATTERNS = [
    re.compile(r"Add sample to repo\s*[—\-:]\s*([a-z0-9][a-z0-9\-]+)", re.I),
    re.compile(r"Build the\s+`?([a-z0-9][a-z0-9\-]+)`?\s+code sample", re.I),
    re.compile(r"^Add\s+([a-z0-9][a-z0-9\-]+)\s+to\s+repo", re.I),
]

LANG_HINTS = {
    "python": ["python", "flask", "fastapi", "django"],
    "nodejs": ["node", "nodejs", "express", "typescript", "javascript", "deno"],
    "go": ["go ", "golang"],
    "ruby": ["ruby", "sinatra"],
    "java": ["java", "spring"],
    "php": ["php", "laravel"],
    "csharp": ["c#", "csharp", ".net"],
}


def _infer_language(text: str) -> Optional[str]:
    t = text.lower()
    for lang, hints in LANG_HINTS.items():
        if any(h in t for h in hints):
            return lang
    return None  # default to python in transform.py


def _slugify(name: str) -> str:
    """Normalize a sample name to a folder-safe slug."""
    s = name.strip().lower()
    s = re.sub(r"[^a-z0-9\-]", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s


def parse_sample_ticket(issue: dict) -> SampleTicket:
    """Inspect a Linear issue and pull out the code-sample spec."""
    title = issue["title"]
    sample_name = ""
    matched = False
    for pat in SAMPLE_TITLE_PATTERNS:
        m = pat.search(title)
        if m:
            sample_name = _slugify(m.group(1))
            matched = True
            break

    desc = issue.get("description") or ""
    language = _infer_language(title + " " + desc) or "python"
    branch = f"linear/{issue['identifier']}-{sample_name}" if sample_name else f"linear/{issue['identifier']}"

    return SampleTicket(
        issue_id=issue["identifier"],
        issue_uuid=issue["id"],
        title=title,
        sample_name=sample_name,
        language=language,
        branch=branch,
        state=issue["state"]["name"],
        url=issue.get("url", ""),
        description=desc,
        is_sample_ticket=matched,
    )


# ---------------------------------------------------------------------------
# Mutations — state transitions + PR link comment
# ---------------------------------------------------------------------------

def _issue_state_id(issue_uuid: str, target_state_name: str) -> Optional[str]:
    """Look up the workflow state ID for a target state name on the issue's team."""
    q = """
    query ($id: ID!) {
      issue(id: $id) { team { states { nodes { id name type } } } }
    }
    """
    data = _gql(q, {"id": issue_uuid})
    states = data["data"]["issue"]["team"]["states"]["nodes"]
    for s in states:
        if s["name"].lower() == target_state_name.lower():
            return s["id"]
    # Fuzzy match fallback
    for s in states:
        if target_state_name.lower() in s["name"].lower():
            return s["id"]
    return None


def move_to_state(issue_uuid: str, state_name: str) -> dict:
    """Move an issue to the named workflow state (e.g. 'In Progress', 'In Review')."""
    state_id = _issue_state_id(issue_uuid, state_name)
    if not state_id:
        raise RuntimeError(f"Linear state '{state_name}' not found for issue {issue_uuid}")
    q = """
    mutation ($input: IssueUpdateInput!) {
      issueUpdate(input: $input) { issue { id identifier state { name } } }
    }
    """
    return _gql(q, {"input": {"id": issue_uuid, "stateId": state_id}})


def add_comment(issue_uuid: str, body: str) -> dict:
    q = """
    mutation ($input: CommentCreateInput!) {
      commentCreate(input: $input) {
        comment { id body }
        success
      }
    }
    """
    return _gql(q, {"input": {"issueId": issue_uuid, "body": body}})


def link_pr(issue_uuid: str, pr_url: str, branch: str, sample_name: str) -> dict:
    """Move to In Review + post the PR URL as a comment."""
    move_to_state(issue_uuid, "In Review")
    body = (
        f"🤖 `telnyx-devrel-bot[bot]` opened a PR for this sample.\n\n"
        f"- **PR**: {pr_url}\n"
        f"- **Branch**: `{branch}`\n"
        f"- **Sample folder**: `{sample_name}/`\n\n"
        f"Reviewer: see the PR for the generated example folder. The bot ran "
        f"`verify.py`, `rewrite_repo_links --check`, `gen_llms_txt --check` "
        f"locally before opening the PR."
    )
    return add_comment(issue_uuid, body)


def mark_done(issue_uuid: str, pr_url: str) -> dict:
    """Move to Done + post a merge-confirmation comment."""
    move_to_state(issue_uuid, "Done")
    body = (
        f"✅ PR merged: {pr_url}\n\n"
        f"The code sample is now live on `main`. The post-merge DevRel "
        f"sync workflow will pick it up next."
    )
    return add_comment(issue_uuid, body)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _cli() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    cmd = sys.argv[1]
    if cmd == "weeks":
        ps = find_code_samples_week_projects()
        print(f"Total 'Code Samples Week *' projects: {len(ps)}")
        for p in ps:
            print(f"  {p['state']:12} {p['name']:30}  id={p['id']}")
    elif cmd == "tickets":
        if len(sys.argv) < 3:
            print("usage: linear_client.py tickets <project-id>")
            return 1
        iss = list_tickets_for_project(sys.argv[2])
        print(f"Total issues in project: {len(iss)}")
        parsed = [parse_sample_ticket(i) for i in iss]
        for p in parsed:
            mark = "SAMPLE" if p.is_sample_ticket else "      "
            print(f"  {mark}  {p.issue_id:10} [{p.state:12}]  {p.title[:60]}")
            if p.is_sample_ticket:
                print(f"           sample={p.sample_name}  lang={p.language}  branch={p.branch}")
    elif cmd == "ticket":
        if len(sys.argv) < 3:
            print("usage: linear_client.py ticket <issue-id-or-uuid>")
            return 1
        ident = sys.argv[2]
        # If short identifier like DEV-908, fetch by that
        if "-" in ident and not ident.startswith("$"):
            q = "query ($id: String!) { issue(id: $id) { id identifier title url state { name } assignee { name } labels { nodes { name } } description } }"
            data = _gql(q, {"id": ident})
            issue = data["data"]["issue"]
        else:
            q = "query ($id: ID!) { issue(id: $id) { id identifier title url state { name } assignee { name } labels { nodes { name } } description } }"
            data = _gql(q, {"id": ident})
            issue = data["data"]["issue"]
        p = parse_sample_ticket(issue)
        print(f"Issue:   {p.issue_id}  ({p.url})")
        print(f"State:   {p.state}")
        print(f"Title:   {p.title}")
        print(f"Sample:  {p.sample_name or '(not detected)'}")
        print(f"Lang:    {p.language}")
        print(f"Branch:  {p.branch}")
        print(f"Is build-sample ticket? {p.is_sample_ticket}")
        print(f"Description (first 400 chars):")
        print("  " + (p.description or "(none)")[:400].replace("\n", "\n  "))
    else:
        print(f"Unknown command: {cmd}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
