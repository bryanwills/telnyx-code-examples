#!/usr/bin/env python3
"""GitHub App auth helper for telnyx-devrel-bot.

Issues a signed JWT from the App's private key and exchanges it for a
short-lived installation access token (1h TTL). The token authenticates
git push, gh CLI, and REST calls as the bot identity
(`<app-name>[bot]`), not a human user.

Usage:
    from github_app_auth import GitHubAppAuth
    auth = GitHubAppAuth(app_id="4704723", private_key_path="/path/to.pem",
                        installation_id=12345)
    token = auth.installation_token()  # cached, auto-refreshed

    # Or via env vars (preferred in CI):
    auth = GitHubAppAuth.from_env()
    token = auth.installation_token()

Env vars:
    GH_APP_ID            App ID (numeric string)
    GH_APP_PRIVATE_KEY   Private key PEM (multiline string) OR
    GH_APP_PRIVATE_KEY_PATH  Path to .pem file
    GH_INSTALLATION_ID  (optional) Installation ID; auto-discovered if omitted

CLI (for testing):
    python scripts/bot/github_app_auth.py whoami
    python scripts/bot/github_app_auth.py token
    python scripts/bot/github_app_auth.py repos
"""

from __future__ import annotations

import json
import os
import pathlib
import sys
import time
import urllib.request
import urllib.error
from dataclasses import dataclass
from typing import Optional

try:
    import jwt  # PyJWT
except ImportError as e:
    raise SystemExit(
        "PyJWT + cryptography required: pip install pyjwt cryptography"
    ) from e


GITHUB_API = "https://api.github.com"


@dataclass
class GitHubAppAuth:
    app_id: str
    private_key_pem: str
    installation_id: Optional[int] = None

    # Internal caches
    _cached_token: Optional[str] = None
    _cached_token_expires_at: float = 0.0
    _cached_installation_id: Optional[int] = None

    @classmethod
    def from_env(cls) -> "GitHubAppAuth":
        app_id = os.environ.get("GH_APP_ID")
        if not app_id:
            raise SystemExit("GH_APP_ID env var not set")
        pem_path = os.environ.get("GH_APP_PRIVATE_KEY_PATH")
        pem_inline = os.environ.get("GH_APP_PRIVATE_KEY")
        if pem_inline:
            pem = pem_inline
        elif pem_path:
            pem = pathlib.Path(pem_path).read_text()
        else:
            raise SystemExit(
                "Set GH_APP_PRIVATE_KEY (inline PEM) or "
                "GH_APP_PRIVATE_KEY_PATH (path to .pem)"
            )
        inst = os.environ.get("GH_INSTALLATION_ID")
        return cls(
            app_id=app_id,
            private_key_pem=pem,
            installation_id=int(inst) if inst else None,
        )

    def _sign_jwt(self) -> str:
        now = int(time.time())
        payload = {
            "iat": now - 60,        # 60s clock-skew tolerance
            "exp": now + 9 * 60,    # 9 min (max is 10)
            "iss": str(self.app_id),
        }
        return jwt.encode(payload, self.private_key_pem, algorithm="RS256")

    def _api(self, method: str, path: str, auth_token: str, body: Optional[dict] = None) -> dict:
        url = f"{GITHUB_API}{path}"
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        data = json.dumps(body).encode() if body else None
        if body is not None:
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req) as resp:
                if resp.status == 204:
                    return {}
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            err_body = e.read().decode()
            raise RuntimeError(f"GitHub API {method} {path} -> {e.code}: {err_body}") from e

    def app_identity(self) -> dict:
        """GET /app — verify the App and its permissions."""
        return self._api("GET", "/app", self._sign_jwt())

    def discover_installation_id(self) -> int:
        """Find the installation ID for this App (first installation)."""
        if self.installation_id:
            return self.installation_id
        installations = self._api("GET", "/app/installations", self._sign_jwt())
        nodes = installations.get("data", installations) if isinstance(installations, dict) else installations
        if isinstance(nodes, dict):
            nodes = nodes.get("nodes", [])
        if not nodes:
            raise SystemExit(
                "App is not installed on any account. Have an org admin "
                "install it via https://github.com/apps/telnyx-devrel-bot/installations/new"
            )
        first = nodes[0] if isinstance(nodes, list) else None
        self.installation_id = first["id"]
        return self.installation_id

    def installation_token(self, force_refresh: bool = False) -> str:
        """Return a valid installation access token (cached, auto-refreshed)."""
        now = time.time()
        if (not force_refresh
                and self._cached_token
                and now < self._cached_token_expires_at - 60):
            return self._cached_token

        inst_id = self.discover_installation_id()
        path = f"/app/installations/{inst_id}/access_tokens"
        url = f"{GITHUB_API}{path}"
        req = urllib.request.Request(
            url, method="POST",
            headers={
                "Authorization": f"Bearer {self._sign_jwt()}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            data=b"",
        )
        try:
            with urllib.request.urlopen(req) as resp:
                payload = json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            raise RuntimeError(
                f"Failed to mint installation token: {e.code} {e.read().decode()}"
            ) from e

        self._cached_token = payload["token"]
        self._cached_token_expires_at = payload["expires_at"]
        # Compute refresh deadline as epoch
        from datetime import datetime, timezone
        dt = datetime.fromisoformat(
            payload["expires_at"].replace("Z", "+00:00")
        )
        self._cached_token_expires_at = dt.timestamp()
        return self._cached_token

    def installation_repos(self) -> dict:
        """List repos this installation can access."""
        token = self.installation_token()
        return self._api("GET", "/installation/repositories", token)

    def repo_info(self, owner: str, repo: str) -> dict:
        token = self.installation_token()
        return self._api("GET", f"/repos/{owner}/{repo}", token)


def _cli():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    cmd = sys.argv[1]
    auth = GitHubAppAuth.from_env()
    if cmd == "whoami":
        ident = auth.app_identity()
        print(f"App:        {ident['name']}  (slug={ident['slug']})")
        print(f"Owner:      {ident['owner']['login']}")
        print(f"URL:        {ident['html_url']}")
        print(f"Permissions: {ident['permissions']}")
    elif cmd == "token":
        print(auth.installation_token())
    elif cmd == "repos":
        try:
            data = auth.installation_repos()
            repos = data.get("repositories", [])
            if not repos:
                print("App is installed but has access to no repositories.")
                print("Check the installation's repository selection on GitHub.")
            for r in repos:
                print(f"  {r['full_name']}  (private={r['private']})")
        except SystemExit as e:
            print(e)
    elif cmd == "repo":
        if len(sys.argv) < 4:
            print("usage: github_app_auth.py repo <owner> <repo>")
            return 1
        info = auth.repo_info(sys.argv[2], sys.argv[3])
        print(f"  {info['full_name']}  default_branch={info['default_branch']}  "
              f"permissions={info['permissions']}")
    else:
        print(f"Unknown command: {cmd}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
