# DevRel Code-Sample Bot — setup & usage

## What this is

Automation that reads a Linear ticket, generates a complete code sample via Telnyx Inference, runs the repo's quality gates, and opens a PR as `telnyx-devrel-bot[bot]`. No human writes the code; no human GitHub auth.

Live proof: [PR #120](https://github.com/team-telnyx/telnyx-code-examples/pull/120) was generated from Linear ticket DEV-808 in ~3 minutes.

## Prerequisites (one-time, ~5 minutes)

You need **two secrets** before running the bot. Both are in the DevRel 1Password vault — ask Sonam Gupta for access if you don't have it.

1. **GitHub App private key** — file named `telnyx-devrel-bot.<date>.private-key.pem`
   - Save it to `~/Downloads/telnyx-devrel-bot.private-key.pem`
   - This is the App's signing key (App ID `4704723`); it lets the bot authenticate as `telnyx-devrel-bot[bot]`

2. **Your Linear API key** and **your Telnyx API key** — these are personal, not shared
   - They should already be in your shell env as `LINEAR_API_KEY` and `TELNYX_API_KEY`
   - The bot reads them from env; you never paste them anywhere

## Setup (agent-readable — paste the block below into your CLI agent)

> Set up the telnyx-devrel-bot on this machine. Steps:
> 1. Run `git clone https://github.com/team-telnyx/telnyx-code-examples.git ~/telnyx-code-examples` (skip if already cloned)
> 2. `cd ~/telnyx-code-examples`
> 3. Run `python3 -m venv .omo/bot-venv && .omo/bot-venv/bin/pip install -q pyjwt cryptography pyyaml telnyx requests`
> 4. Verify `~/Downloads/telnyx-devrel-bot.private-key.pem` exists; if not, tell me to download it from 1Password first
> 5. Verify `$LINEAR_API_KEY` and `$TELNYX_API_KEY` are set in env; if not, tell me to set them
> 6. Run a smoke test: `GH_APP_ID=4704723 GH_APP_PRIVATE_KEY_PATH=~/Downloads/telnyx-devrel-bot.private-key.pem .omo/bot-venv/bin/python scripts/bot/github_app_auth.py whoami`
> 7. Report whether the bot identity shows as `telnyx-devrel-bot`

## Run the bot on a ticket (agent-readable — paste into your CLI agent)

> Run the telnyx-devrel-bot against Linear ticket **DEV-XXX**. Open a real PR (not a dry-run). Use a fresh clean clone at `/tmp/bot-run` so my working tree isn't touched:
> ```bash
> git clone https://github.com/team-telnyx/telnyx-code-examples.git /tmp/bot-run
> cp -r ~/telnyx-code-examples/scripts/bot /tmp/bot-run/scripts/
> cd /tmp/bot-run
> git switch -c bot-bootstrap && git add scripts/bot/ && git -c user.email=bot@local -c user.name=bot commit -m bootstrap
> export GH_APP_ID=4704723
> export GH_APP_PRIVATE_KEY_PATH=~/Downloads/telnyx-devrel-bot.private-key.pem
> export BOT_REPO_ROOT=/tmp/bot-run
> export AI_MODEL=deepseek-ai/DeepSeek-V4-Flash-0731
> ~/telnyx-code-examples/.omo/bot-venv/bin/python scripts/bot/runner.py --ticket DEV-XXX --no-dry-run
> ```
> Report the PR URL when done. If `verify.py` fails, check whether the failures are pre-existing on main (run `verify.py` on a clean main checkout to compare) — only fix failures caused by the new sample, not pre-existing ones.

## Dry-run (review generated files before opening a PR)

Same as above, but drop `--no-dry-run`:

> Run the telnyx-devrel-bot against Linear ticket **DEV-XXX** in dry-run mode (no PR, no Linear state change). Use `/tmp/bot-run` as the working directory. When done, show me the contents of the generated sample folder so I can review before opening a real PR.

## What the bot does

1. Reads Linear ticket, parses `## Sample: <name>` from the description
2. Calls Telnyx Inference (`deepseek-ai/DeepSeek-V4-Flash-0731`, two-phase: code → docs)
3. Runs repo gates (`verify.py`, `rewrite_repo_links`, `sync_readme`, `gen_llms_txt`) with auto-fix
4. Branches `linear/<TICKET>-<sample>`, commits as `telnyx-devrel-bot[bot]`, opens PR with `code-samples` label
5. Updates Linear: moves ticket to "In Review" + comments PR URL

~3 minutes per ticket.

## Identity & audit (what shows up where)

| Action | Identity |
|---|---|
| Git commits + PR author | `telnyx-devrel-bot[bot]` (shared bot account, owned by `team-telnyx` org) |
| Linear state changes + comments | You (whichever Linear API key is in your env) |
| Telnyx Inference API calls | You (whichever Telnyx API key is in your env) |

So the PR is always from the bot; the Linear ticket updates are from whoever ran it. No personal GitHub account is used.

## Ticket requirements

The Linear ticket must:
- Be on the **DEV** team's "Code Samples Week N" project (current active week: `Code Samples Week 9`, ID `c96d42d7-bc43-45db-a4c0-2518fc63e290`)
- Contain a line like `## Sample: \`<name>\`` in the description (look at [DEV-808](https://linear.app/telnyx/issue/DEV-808/sprint-2-ai-call-campaign-orchestrator) for the format)
- Have a description that explains the architecture / key APIs / acceptance criteria — the LLM uses this as the spec

## Troubleshooting

- **"Working tree is dirty"** — you ran from your real checkout instead of `/tmp/bot-run`. Use the clone command in the run recipe.
- **Inference 524 timeout** — stick with `deepseek-ai/DeepSeek-V4-Flash-0731` (4-15s per phase). Don't use `moonshotai/Kimi-K2.6` (reasoning model, times out at the edge proxy).
- **`verify.py` red but the new sample passes** — pre-existing unregistered folders on `main` (e.g. `ai-email-agent-python`, `audio-transcribe-summarize-sms`). Not caused by your run; merge the PR anyway or open a separate PR to register those folders.
- **Bot identity wrong (commits show your name, not `telnyx-devrel-bot[bot]`)** — the `GH_APP_ID` / `GH_APP_PRIVATE_KEY_PATH` env vars aren't being picked up. Confirm they're exported in the shell where the agent runs.
- **"label 'code-samples' not found"** — already created on the repo, won't recur. If it does: `curl -X POST -H "Authorization: token <token>" https://api.github.com/repos/team-telnyx/telnyx-code-examples/labels -d '{"name":"code-samples","color":"0E8FB3"}'`
- **Linear "Invalid GraphQL" error** — known cosmetic bug in `linear_client._issue_state_id` (type mismatch between `ID!` and `String!`). The ticket state usually already moves via Linear's own automation; the comment with the PR URL still lands. Fix is queued.

## What's already done (you don't need to redo)

- ✅ GitHub App `telnyx-devrel-bot` created, transferred to `team-telnyx` org, installed on `telnyx-code-examples` with scoped permissions (Contents/Pull requests/Issues/Statuses = write)
- ✅ `code-samples` label created on the repo
- ✅ Bot tested end-to-end on DEV-808 → [PR #120](https://github.com/team-telnyx/telnyx-code-examples/pull/120)
- ✅ All 5 bot modules in `scripts/bot/` proven working

## What's deferred (separate work, not blocking usage)

- Post-merge DevRel repo sync (blocked on confirming the DevRel repo URL)
- Slack `#what-is-new-today` ingest (creating Linear tickets from Slack — deferred)
- Fix the `linear_client._issue_state_id` GraphQL type bug (cosmetic)
