#!/usr/bin/env python3
"""Generate a complete code-sample folder from a Linear ticket spec using Telnyx Inference.

Two-phase generation:
  Phase 1 — code: app.py + requirements.txt + .env.example
  Phase 2 — docs: README.md + API.md + GUIDE.md  (conditioned on phase 1's code)

Env vars:
    TELNYX_API_KEY   Telnyx API v2 key (already in your env)
    AI_MODEL         Inference model (default: moonshotai/Kimi-K2.6)
    AI_TEMPERATURE   Sampling temperature (default: 0.3)

CLI:
    python scripts/bot/generate_sample.py \\
        --ticket-id DEV-808 \\
        --folder ai-call-campaign-orchestrator \\
        --language python \\
        --framework flask \\
        --out /tmp/bot-run/ai-call-campaign-orchestrator
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

# Two inference backends — the bot auto-detects which one to use based on
# which API key is available in the environment. See _resolve_inference_config()
# below. On ACP (Hermes agent), LITELLM_API_KEY is auto-provisioned so no
# TELNYX_API_KEY runtime secret is needed. On a laptop, TELNYX_API_KEY is
# used with the public Telnyx API.
TELNYX_INFERENCE_URL = "https://api.telnyx.com/v2/ai/chat/completions"
LITELLM_DEFAULT_BASE = "http://litellm-aiswe.query.prod.telnyx.io:4000/v1"


# ---------------------------------------------------------------------------
# Repo conventions baked into the prompt (kept short — full CLAUDE.md is too long)
# ---------------------------------------------------------------------------

CONVENTIONS = """\
You are generating a code sample for the `team-telnyx/telnyx-code-examples` repo.

Repo conventions (non-negotiable):
- Code loads credentials from environment variables via `dotenv` (Python: `from dotenv import load_dotenv; load_dotenv()`). NEVER hardcode API keys.
- Production-safe error handling: log via `app.logger.exception(...)`, return generic HTTP error messages. Do not leak exception details in HTTP responses.
- Inbound webhook handlers MUST verify the Telnyx Ed25519 signature using `client.webhooks.unwrap` and read event fields from `data.payload`.
- Use the Telnyx SDK (`import telnyx`) for API calls where applicable, not raw HTTP, unless the spec specifically calls for raw HTTP.
- Python: Flask app named `app`, file named `app.py`, deps in `requirements.txt` (flask>=3.0, requests>=2.31, python-dotenv>=1.0, telnyx>=2.0 + any others).
- `.env.example` contains `TELNYX_API_KEY=your_telnyx_api_key_here` plus any other env vars the app reads. Placeholder values only — NEVER real credentials.
- Do NOT add Dockerfile, Makefile, or other deployment scaffolding. Folder contains only: README.md, API.md, GUIDE.md, app.py, requirements.txt, .env.example.

README.md must include these sections in order:
  H1 title, one-line description, ## Why Telnyx (must contain the phrase "AI Communications Infrastructure"), ## Telnyx API Endpoints Used, ## Architecture, ## Environment Variables (markdown table), ## Setup, ## API Reference, ## Troubleshooting, ## Agent Discovery, ## Related Examples, ## Resources

README.md frontmatter (YAML between --- fences at top):
  name, title, description, language, framework, telnyx_products

API.md is a typed endpoint reference: routes, params, request/response shapes, status codes.
GUIDE.md is a standalone tutorial walking through how the example works.
"""


# ---------------------------------------------------------------------------
# Inference call — supports two backends:
#   1. LiteLLM proxy (preferred on ACP): LITELLM_API_KEY + LITELLM_BASE_URL
#   2. Telnyx public API (laptop/dev):    TELNYX_API_KEY + https://api.telnyx.com/v2/ai/chat/completions
# The agent on ACP has LITELLM_API_KEY auto-provisioned, so no TELNYX_API_KEY
# runtime secret is needed when running on ACP.
# ---------------------------------------------------------------------------

TELNYX_INFERENCE_URL = "https://api.telnyx.com/v2/ai/chat/completions"
LITELLM_DEFAULT_BASE = "http://litellm-aiswe.query.prod.telnyx.io:4000/v1"


def _resolve_inference_config() -> tuple[str, str, str]:
    """Return (api_url, auth_token, default_model) based on which env vars are available.

    Prefers LiteLLM (LITELLM_API_KEY) when set — this is the ACP path where
    the agent has the key auto-provisioned and doesn't need TELNYX_API_KEY.
    Falls back to the Telnyx public API (TELNYX_API_KEY) for laptop/dev use.

    The default model differs between backends:
      - LiteLLM proxy:       "DeepSeek-V4-Flash" (bare metal name, no prefix)
      - Telnyx public API:   "deepseek-ai/DeepSeek-V4-Flash-0731" (provider-prefixed)
    """
    litellm_key = os.environ.get("LITELLM_API_KEY") or os.environ.get("LITELLM_KEY")
    if litellm_key:
        base = os.environ.get("LITELLM_BASE_URL", LITELLM_DEFAULT_BASE)
        url = f"{base.rstrip('/')}/chat/completions"
        return url, litellm_key, "DeepSeek-V4-Flash"
    telnyx_key = os.environ.get("TELNYX_API_KEY")
    if telnyx_key:
        return TELNYX_INFERENCE_URL, telnyx_key, "deepseek-ai/DeepSeek-V4-Flash-0731"
    raise SystemExit(
        "No inference credentials found. Set either LITELLM_API_KEY (ACP) "
        "or TELNYX_API_KEY (laptop/dev) in the environment."
    )


def call_inference(messages: list[dict], max_tokens: int = 8000,
                   temperature: float = 0.3) -> str:
    url, key, default_model = _resolve_inference_config()
    model = os.environ.get("AI_MODEL", default_model)
    body = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        method="POST",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            data = json.loads(resp.read().decode())
        return data["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        raise RuntimeError(f"Inference API error {e.code}: {err}") from e


# ---------------------------------------------------------------------------
# File-extraction from LLM response
# ---------------------------------------------------------------------------

FILE_BLOCK = re.compile(
    r"```[a-zA-Z0-9_+-]*:filename:([^\s`]+\.[a-z]+)\n(.*?)```",
    re.DOTALL | re.IGNORECASE,
)
FILE_HEADER = re.compile(
    r"^#+\s*(?:File|FILE)[: ]*`?([^\n]+\.[a-z]+)`?\s*$",
    re.MULTILINE | re.IGNORECASE,
)
SIMPLE_FENCE = re.compile(
    r"```([a-zA-Z0-9_+-]+)?\n(.*?)```",
    re.DOTALL,
)
# Sentinel format: === FILE: name.ext ===\n<content until next sentinel or EOF>
SENTINEL = re.compile(
    r"^=== FILE:\s*([^\s]+\.[a-z]+)\s*===\s*\n(.*?)(?=^=== FILE:|\Z)",
    re.MULTILINE | re.DOTALL | re.IGNORECASE,
)


def _strip_wrapping_fence(content: str, expected_lang: str = "") -> str:
    """If the entire content is wrapped in a single markdown fence, strip it.

    The LLM sometimes wraps content in ` ```python ... ``` ` even when we
    ask for raw. Detect this by checking if the content starts AND ends
    with a fence line, and there are no other fence lines in between.
    """
    # Strip trailing whitespace/newlines so the closing fence is the last
    # meaningful line. Otherwise `lines[-1]` is '' and our index math breaks.
    stripped = content.rstrip()
    lines = stripped.split("\n")
    if len(lines) < 2:
        return content
    first = lines[0].strip()
    last = lines[-1].strip()
    if not (first.startswith("```") and last == "```"):
        return content
    # Look for any other fence lines between the outer two. If there are
    # none, this is a single wrap → strip it.
    inner = [l for l in lines[1:-1] if l.strip().startswith("```")]
    if not inner:
        return "\n".join(lines[1:-1]) + "\n"
    return content


def extract_files_from_response(text: str, fallback_name: str,
                                fallback_ext: str) -> dict[str, str]:
    """Parse the LLM response into a {filename: content} dict.

    Recognizes (in priority order):
      Sentinel:  === FILE: name.ext ===\n<content>
      Fenced:    ```lang:filename:name.ext\n<content>```
      Header:    ### File: name.ext\n```<content>```
      Single:    one fenced block

    Also handles degenerate cases: if the LLM loops and never closes the
    final fence, we still capture the content up to the loop start.
    """
    files: dict[str, str] = {}

    # Pattern 0 (preferred): sentinel format — immune to nested fences
    for m in SENTINEL.finditer(text):
        fname = m.group(1).strip().split("/")[-1].strip()
        content = _strip_repetition_loops(m.group(2))
        files[fname] = content.strip() + "\n"
    if files:
        return files

    # Pattern 1: fenced blocks with filename tag (greedy match to capture
    # everything up to a close fence, but also handle unclosed final block).
    file_block_re = re.compile(
        r"```[a-zA-Z0-9_+-]*:filename:([^\s`]+\.[a-z]+)\n(.*?)```",
        re.DOTALL | re.IGNORECASE,
    )
    for m in file_block_re.finditer(text):
        fname = m.group(1).strip().split("/")[-1].strip()
        content = m.group(2)
        # Strip degenerate repetition: detect runs of the same ~10-char
        # chunk repeated >5 times and cut to the first occurrence
        content = _strip_repetition_loops(content)
        files[fname] = content.strip() + "\n"

    if files:
        return files

    # Pattern 1b: opener with filename tag but no close fence (truncated/looped)
    unclosed_re = re.compile(
        r"```[a-zA-Z0-9_+-]*:filename:([^\s`]+\.[a-z]+)\n(.*)$",
        re.DOTALL | re.IGNORECASE,
    )
    m = unclosed_re.search(text)
    if m:
        fname = m.group(1).strip().split("/")[-1].strip()
        content = _strip_repetition_loops(m.group(2))
        files[fname] = content.strip() + "\n"
        return files

    # Pattern 2: ### File: <name> headers followed by a fenced block
    headers = list(FILE_HEADER.finditer(text))
    for i, h in enumerate(headers):
        fname = h.group(1).strip().split("/")[-1].strip()
        rest = text[h.end():]
        fence = SIMPLE_FENCE.search(rest)
        if fence:
            files[fname] = _strip_repetition_loops(fence.group(2)).strip() + "\n"

    if files:
        return files

    # Pattern 3: single fenced block — use fallback name
    fences = list(SIMPLE_FENCE.finditer(text))
    if len(fences) == 1:
        files[fallback_name + fallback_ext] = _strip_repetition_loops(
            fences[0].group(2)
        ).strip() + "\n"
    elif len(fences) > 1:
        defaults = ["app.py", "requirements.txt", ".env.example"]
        for i, f in enumerate(fences[:3]):
            name = defaults[i] if i < len(defaults) else f"file{i}.{fallback_ext}"
            files[name] = _strip_repetition_loops(f.group(2)).strip() + "\n"

    # Post-process: strip a single wrapping fence from each file's content.
    # The LLM often wraps content in ` ```python ... ``` ` even when asked
    # for raw — this catches that and leaves inner fences intact.
    for fname, content in files.items():
        files[fname] = _strip_wrapping_fence(content)

    return files


def _strip_repetition_loops(text: str, min_run: int = 6,
                            chunk_size: int = 12) -> str:
    """Cut degenerate autoregressive repetition.

    If the same ~12-char chunk repeats 6+ times in a row, keep only the
    first occurrence and truncate the rest. This catches the
    `get_exec = get_exec = get_exec = ...` failure mode without
    touching legitimate code.
    """
    # Look for a single token followed by ' = ' repeated many times
    # Pattern: <word>( = <word>){5,}
    rep_re = re.compile(
        r"(\b[\w\.]{1,40}\s*=\s)\1{5,}\1?",
        re.MULTILINE,
    )
    cleaned = rep_re.sub(r"\1", text, count=1)
    if cleaned != text:
        # Truncate after the first occurrence + a marker
        idx = cleaned.find(r"\1") if r"\1" in cleaned else len(cleaned)
        return cleaned + "\n# [truncated: degenerate repetition detected]\n"
    return text


# ---------------------------------------------------------------------------
# Two-phase generation
# ---------------------------------------------------------------------------

def build_phase1_prompt(ticket_id: str, ticket_title: str,
                        ticket_description: str, folder_name: str,
                        language: str, framework: str) -> str:
    return f"""Generate the CODE FILES for a Telnyx code sample.

Linear ticket: {ticket_id} — {ticket_title}

Ticket spec (Linear description):
---
{ticket_description}
---

Target folder: `{folder_name}/`
Language: {language}
Framework: {framework}

Output the following three files. For EACH file, use this EXACT format (sentinel-based, NOT fenced — this is critical so inner code fences don't break parsing):

=== FILE: app.py ===
<full content of app.py here>

=== FILE: requirements.txt ===
<full content of requirements.txt here>

=== FILE: .env.example ===
<full content of .env.example here>

The sentinel line `=== FILE: <filename> ===` must appear EXACTLY once per file, on its own line, before that file's content. Output the three files in the order above. The file content goes verbatim between one sentinel and the next — do not wrap it in additional markdown fences.

{CONVENTIONS}

Return ONLY the three sentinel-delimited files. No prose before the first sentinel or after the last file's content.
"""


def build_phase2_prompt(ticket_id: str, ticket_title: str,
                         ticket_description: str, folder_name: str,
                         language: str, framework: str,
                         app_py: str, env_vars: list[str],
                         doc_file: str) -> str:
    """Build a prompt for ONE doc file (README.md | API.md | GUIDE.md)."""
    env_table = "\n".join(
        f"| `{v}` | `string` | `your_{v.lower()}_here` | **yes** | {v} | — |"
        for v in env_vars
    )

    file_specific = {
        "README.md": f"""README.md is the AEO-structured overview + run docs. It MUST contain these sections in this order:
1. YAML frontmatter (between --- fences, BEFORE the H1 title):
```
---
name: {folder_name}
title: "<Human-readable title>"
description: "<one-line description>"
language: {language}
framework: {framework}
telnyx_products: [<infer from spec>]
---
```
2. H1 title + one-line description
3. ## Why Telnyx — must contain the exact phrase "AI Communications Infrastructure"
4. ## Telnyx API Endpoints Used
5. ## Architecture (with an ASCII diagram in a fenced code block)
6. ## Environment Variables — markdown table with this exact header row and these env vars:
| Variable | Type | Example | Required | Description | Where to get it |
|----------|------|---------|----------|-------------|-----------------|
{env_table if env_table else "| `TELNYX_API_KEY` | `string` | `your_telnyx_api_key_here` | **yes** | Telnyx API v2 key | [Portal](https://portal.telnyx.com/api-keys) |"}
7. ## Setup — local clone + .env + install + run commands (no Docker, no make)
8. ## API Reference
9. ## Troubleshooting — common issues table
10. ## Agent Discovery — links to telnyx.com/agent-signup.md, github.com/team-telnyx/ai, llms.txt
11. ## Related Examples
12. ## Resources — dev-docs, API reference, SDK, product page, pricing links
""",
        "API.md": """API.md is the typed endpoint reference. For each route in app.py include:
- HTTP method + path
- Request body schema (table of fields, types, required, description)
- Example request (curl)
- Response schema (status code → JSON shape)
- Status codes table (200, 400, 404, 500)
Do NOT repeat the README. This is purely the API contract.
""",
        "GUIDE.md": f"""GUIDE.md is a standalone tutorial walking a developer through how the example works.
- Step-by-step narrative explaining each piece of the code
- Reference `app.py` line ranges by feature, not line number
- Explain the Telnyx primitives used (queue, schedule, Call Control, SMS, SQL)
- Include prerequisites, env setup, and run instructions
- End with a "Next steps" section linking to dev docs
""",
    }[doc_file]

    return f"""Generate ONE documentation file: `{doc_file}` for a Telnyx code sample. The code is already written (below).

Linear ticket: {ticket_id} — {ticket_title}

Ticket spec:
---
{ticket_description}
---

Target folder: `{folder_name}/`
Language: {language}
Framework: {framework}

Generated `app.py` (DO NOT modify, just describe it):
```{language}
{app_py}
```

Env vars detected: {env_vars}

{file_specific}

Output the file using this EXACT sentinel format (NOT fenced — this is critical so inner markdown fences don't break parsing):

=== FILE: {doc_file} ===
<full content of {doc_file} here>

The sentinel line `=== FILE: {doc_file} ===` must appear EXACTLY once, on its own line, before the file content. The file content goes verbatim after the sentinel — do NOT wrap it in an outer markdown fence. Output the sentinel and then the raw file content. No prose before or after.

{CONVENTIONS}
"""


def extract_env_vars_from_app(app_py: str) -> list[str]:
    """Find os.getenv/os.environ references in app.py."""
    vars_ = set()
    for m in re.finditer(r"os\.(?:getenv|environ\.get|environ\[)\(['\"]([A-Z_][A-Z0-9_]*)", app_py):
        vars_.add(m.group(1))
    # Always include TELNYX_API_KEY per repo conventions
    vars_.add("TELNYX_API_KEY")
    return sorted(vars_)


def generate_sample(ticket_id: str, ticket_title: str, ticket_description: str,
                    folder_name: str, language: str = "python",
                    framework: str = "flask",
                    out_dir: Path = Path("."),
                    max_tokens: int = 8000,
                    temperature: float = 0.3) -> Path:
    """Generate a complete example folder from a Linear ticket spec."""
    out_dir.mkdir(parents=True, exist_ok=True)

    # ---- Phase 1: code ----
    print(f"[phase 1] Generating code for {folder_name}/...")
    phase1_prompt = build_phase1_prompt(
        ticket_id, ticket_title, ticket_description, folder_name, language, framework
    )
    phase1_resp = call_inference(
        [
            {"role": "system",
             "content": "You generate production-ready code samples for Telnyx APIs."},
            {"role": "user", "content": phase1_prompt},
        ],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    code_files = extract_files_from_response(phase1_resp, "app", ".py")
    if not code_files:
        # Save raw response for debugging
        (out_dir / "_phase1_raw.md").write_text(phase1_resp)
        raise RuntimeError(
            f"Phase 1 produced no parseable files. Raw response saved to {out_dir/'_phase1_raw.md'}"
        )

    written: list[str] = []
    for fname, content in code_files.items():
        (out_dir / fname).write_text(content)
        written.append(fname)
        print(f"  wrote {fname} ({len(content)} bytes)")

    # ---- Phase 2: docs (one LLM call per doc file) ----
    app_py = code_files.get("app.py", "")
    if not app_py:
        # Try any *.py file
        app_py = next((c for f, c in code_files.items() if f.endswith(".py")), "")
    env_vars = extract_env_vars_from_app(app_py)

    doc_files_to_gen = ["README.md", "API.md", "GUIDE.md"]
    print(f"[phase 2] Generating docs for {folder_name}/  (env vars: {env_vars})")
    for doc_file in doc_files_to_gen:
        print(f"  → {doc_file}...")
        phase2_prompt = build_phase2_prompt(
            ticket_id, ticket_title, ticket_description, folder_name,
            language, framework, app_py, env_vars, doc_file,
        )
        phase2_resp = call_inference(
            [
                {"role": "system",
                 "content": "You generate AEO-structured documentation for Telnyx code samples."},
                {"role": "user", "content": phase2_prompt},
            ],
            # Phase-2 prompts embed the full app.py + conventions, so docs
            # need more output room than the phase-1 default. 12K tokens is
            # plenty for a single ~3-5K-token doc file.
            max_tokens=max(max_tokens, 12000),
            temperature=temperature,
        )
        # Extract just this one file from the response
        single = extract_files_from_response(phase2_resp, doc_file.rsplit(".", 1)[0], ".md")
        if doc_file in single:
            (out_dir / doc_file).write_text(single[doc_file])
            written.append(doc_file)
            print(f"    wrote {doc_file} ({len(single[doc_file])} bytes)")
        else:
            # Save raw for debugging
            (out_dir / f"_phase2_{doc_file}_raw.md").write_text(phase2_resp)
            print(f"    ✗ failed to parse {doc_file}; raw saved to _phase2_{doc_file}_raw.md")

    print(f"\nGenerated {len(written)} files in {out_dir}/:")
    for f in sorted(out_dir.iterdir()):
        if f.is_file() and not f.name.startswith("_phase"):
            print(f"  {f.name:20} {f.stat().st_size:6} bytes")

    return out_dir


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    p = argparse.ArgumentParser(
        description="Generate a code sample folder from a Linear ticket via Telnyx Inference.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--ticket-id", required=True, help="Linear ticket ID (e.g. DEV-808)")
    p.add_argument("--ticket-title", required=True, help="Linear ticket title")
    p.add_argument("--ticket-description", required=True,
                   help="Linear ticket description (or path to a .md file with it)")
    p.add_argument("--folder", required=True, help="Target folder name")
    p.add_argument("--language", default="python")
    p.add_argument("--framework", default="flask")
    p.add_argument("--out", default=".", help="Output directory")
    p.add_argument("--max-tokens", type=int, default=6000)
    p.add_argument("--temperature", type=float, default=0.3)
    args = p.parse_args()

    # Allow --ticket-description to be a path
    desc = args.ticket_description
    if Path(desc).exists():
        desc = Path(desc).read_text()

    out = generate_sample(
        ticket_id=args.ticket_id,
        ticket_title=args.ticket_title,
        ticket_description=desc,
        folder_name=args.folder,
        language=args.language,
        framework=args.framework,
        out_dir=Path(args.out),
        max_tokens=args.max_tokens,
        temperature=args.temperature,
    )
    print(f"\nDone. Output: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
