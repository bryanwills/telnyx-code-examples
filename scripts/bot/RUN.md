# DevRel Code-Sample Bot — ACP Agent

## What this is

An autonomous agent on the Telnyx Agent Control Plane (ACP) that reads Linear tickets, generates complete code samples via LLM inference, runs repo gates, and opens PRs as `telnyx-devrel-bot[bot]`. No laptop, no manual GitHub auth, no human-written code.

After a code sample PR merges, the bot also generates AEO syndication content (blog post, Medium article, Hacker News post, YouTube script) and opens a PR in `devrel-internal/aeo/<assignee>-aeo/<sample-name>/`.

**Two-stage pipeline:**
1. **Code sample generation** — ACP agent → PR in `telnyx-code-examples`
2. **Syndication generation** — after merge → PR in `devrel-internal`

**Agent name:** `devrel-squad-bot`
**Runtime:** Hermes on ACP
**Gateway:** `http://agent-devrel-squad-acp-devrel-squad-bot.query.prod.telnyx.io:18789/v1/responses`
**Gateway key:** In the ACP UI (runtime secrets section) — ask Sonam or check the agent's config

## How to trigger a run

### Option 1 — Tell your agentic CLI

Paste this into opencode / Claude Code / Codex:

> Trigger the devrel-squad-bot agent on ACP. Send a POST to `http://agent-devrel-squad-acp-devrel-squad-bot.query.prod.telnyx.io:18789/v1/responses` with header `Authorization: Bearer <gateway-key>` and body `{"model":"devrel-squad-bot","input":"Run the bot. Find my actionable Linear tickets in Code Samples Week 9+ and open PRs."}`. Report back what the agent says.

### Option 2 — Direct curl

```bash
curl -s -X POST "http://agent-devrel-squad-acp-devrel-squad-bot.query.prod.telnyx.io:18789/v1/responses" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <gateway-key>" \
  -d '{"model":"devrel-squad-bot","input":"Run the bot. Find my actionable Linear tickets in Code Samples Week 9+ and open PRs."}'
```

Replace `<gateway-key>` with the actual gateway key (in the ACP UI runtime secrets).

### Option 3 — ACP UI

Open http://agent-control-plane.query.prod.telnyx.io:8000/ui/agents/ae7e516a-6c23-4970-8c60-17fd1a6e6ece and use the test/send-message interface.

## What the agent does

When triggered:
1. Writes the GitHub App private key from the `APP_PRIVATE_KEY` runtime secret to `/tmp/devrel-bot.private-key.pem`
2. Clones `team-telnyx/telnyx-code-examples` to `/tmp/bot-run`
3. Creates a Python venv, installs deps
4. Runs `scripts/bot/runner.py --mine --no-dry-run` which:
   - Discovers your Linear tickets in Code Samples Week 9+ (Backlog/Todo/Unstarted state only)
   - Falls through to the next week if current week has nothing for you
   - For each ticket: generates code + docs via GLM-5.2-NVFP4 (LiteLLM proxy)
   - Runs repo gates (verify.py, rewrite_repo_links, sync_readme, gen_llms_txt)
   - Branches, commits as `telnyx-devrel-bot[bot]`, pushes, opens PR via GitHub REST API
   - Adds `code-samples` label
5. Reports back: tickets found, PRs opened (with URLs), errors

Takes ~3 min per ticket. If no actionable tickets, reports "no actionable tickets" and exits clean.

### Syndication (post-merge)

After a code sample PR merges to `telnyx-code-examples/main`:

1. Run `scripts/bot/syndicate.py --sample <sample-name> --assignee <name> --no-dry-run`
2. The bot reads the sample's README from `telnyx-code-examples`
3. Generates 5 AEO syndication files via GLM-5.2-NVFP4:
   - `README.md` — syndication package overview + pillar alignment
   - `blog-post.md` — technical walkthrough for Telnyx Blog / Dev.to
   - `medium-article.md` — narrative developer story for Medium
   - `hackernews-post.md` — Show HN post
   - `youtube-script.md` — YouTube demo script with timestamps
4. Opens a PR in `devrel-internal/aeo/<assignee>-aeo/<sample-name>/`

Usage:
```bash
python scripts/bot/syndicate.py --sample ai-call-campaign-orchestrator --assignee sonam --no-dry-run
```

Dry-run (writes to `/tmp/syndication-<sample>/` for review):
```bash
python scripts/bot/syndicate.py --sample ai-call-campaign-orchestrator --assignee sonam
```

## What you need

| Thing | Where |
|---|---|
| Gateway key | ACP UI → agent page → runtime secrets (ask Sonam if you don't have it) |
| Your Linear tickets assigned to you | Already in Linear — Week 9+ on DEV team, with `## Sample: \`name\`` in description |
| `LINEAR_API_KEY` runtime secret | Already set on the agent (Sonam's key). For your own key, ask Sonam to add yours or deploy your own agent |
| `APP_PRIVATE_KEY` runtime secret | Already set (GitHub App private key) |

## Discovery rules

- **Weeks scanned:** Code Samples Week 9 and later (Weeks 7, 8 are done — skipped)
- **States picked up:** Backlog, Todo, Unstarted only
- **States skipped:** In Review, In Progress, Done, Canceled — never re-processed
- **Per-person fallback:** if current week has nothing for you, bot moves to next week
- **Stops at first week** with parseable tickets for you
- **Sample name:** requires `## Sample: \`<name>\`` line in ticket description

## Identity & audit

| Action | Identity |
|---|---|
| Git commits + PR author | `telnyx-devrel-bot[bot]` (shared bot, owned by `team-telnyx` org) |
| Linear state changes + comments | Whichever `LINEAR_API_KEY` is in the agent's runtime secrets |
| LLM inference calls | Routed through LiteLLM proxy (auto-provisioned `LITELLM_API_KEY`) |

## Adding a teammate (for Sonam / Stephen)

To let Harpreet or Anusha run the bot with their own Linear identity:

1. **Option A — Deploy a per-teammate agent** (recommended):
   - Clone the `devrel-squad-bot` config via ACP deploy with a new name (e.g. `devrel-squad-bot-harpreet`)
   - Replace the `LINEAR_API_KEY` runtime secret with Harpreet's key
   - Update `soul_md` to reference Harpreet's name instead of Sonam's
   - Each teammate triggers their own agent

2. **Option B — Shared agent with multiple keys** (more complex):
   - Add `LINEAR_API_KEY_HARPREET`, `LINEAR_API_KEY_ANUSHA` as runtime secrets
   - Modify `runner.py` to accept `--assignee "Harpreet Singh Seehra"` and use the matching key
   - One agent, three callers

## Troubleshooting

- **"No actionable tickets found"** — correct behavior if all your tickets are In Review/Done. Check Linear to confirm.
- **Inference returns empty/None** — the model is overloaded. Stick with `GLM-5.2-NVFP4` (proven for code gen on ACP). Don't use DeepSeek-V4-Flash or MiniMax — they return empty content for complex code-gen prompts on ACP.
- **`verify.py` red but sample passes** — pre-existing unregistered folders on main (ai-email-agent-python, etc.). Not your problem; merge the PR anyway.
- **PEM key errors** — the agent normalizes the PEM automatically. If it still fails, check the `APP_PRIVATE_KEY` runtime secret has the full PEM including `-----BEGIN RSA PRIVATE KEY-----` and `-----END RSA PRIVATE KEY-----` lines.
- **PR creation fails** — the bot uses GitHub REST API (not `gh` CLI). If it fails, check the GitHub App installation token is valid (the agent mints a fresh one each run).

## Architecture

```
Teammate triggers agent
        │
        ▼
┌──────────────────────────────────────────────────┐
│  ACP Hermes Agent (devrel-squad-bot)             │
│  ┌────────────────────────────────────────────┐  │
│  │ 1. Write PEM from APP_PRIVATE_KEY secret    │  │
│  │ 2. Clone repo to /tmp/bot-run               │  │
│  │ 3. Create venv + install deps               │  │
│  │ 4. Run runner.py --mine --no-dry-run        │  │
│  │    ├─ Discover tickets (LINEAR_API_KEY)     │  │
│  │    ├─ Generate code (LITELLM_API_KEY)       │  │
│  │    ├─ Run gates (verify.py, etc.)           │  │
│  │    ├─ Branch + commit + push (App token)    │  │
│  │    └─ Open PR (GitHub REST API)             │  │
│  │ 5. Report PR URLs                           │  │
│  └────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────┘
        │
        ▼
  PR on GitHub (telnyx-devrel-bot[bot])
  Linear ticket → In Review + PR link comment
```

## Key files (on `main` in the repo)

| File | Purpose |
|---|---|
| `scripts/bot/runner.py` | Orchestrator: Linear → LLM → gates → PR → Linear |
| `scripts/bot/generate_sample.py` | Two-phase LLM generation (code → docs), supports LiteLLM + Telnyx public API |
| `scripts/bot/open_pr.py` | Branch/commit/push/PR via GitHub REST API (no `gh` CLI needed) |
| `scripts/bot/github_app_auth.py` | JWT → installation token, PEM normalization |
| `scripts/bot/linear_client.py` | Read Linear tickets, move state, comment |
| `scripts/bot/syndicate.py` | Post-merge: generate AEO syndication content → PR in devrel-internal |

## Known limitations

- Agent processes one teammate's tickets per run (Sonam's key is configured)
- No Slack integration yet (Stephen's request — deferred)
- No cron schedule yet (triggered manually or via A2A message)
- `linear_client._issue_state_id` has a cosmetic GraphQL type bug (state usually moves via Linear's own automation)
