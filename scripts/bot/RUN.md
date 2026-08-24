# Run the DevRel code-sample bot

## One-time setup (per machine)

```bash
# 1. Clone the repo + create the bot venv
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples
python3 -m venv .omo/bot-venv
.omo/bot-venv/bin/pip install -q pyjwt cryptography pyyaml telnyx requests

# 2. Get the GitHub App private key (ask Sonam / Stephen)
#    Save the .pem somewhere, e.g. ~/Downloads/telnyx-devrel-bot.private-key.pem
#    App ID: 4704723

# 3. Confirm Linear + Telnyx API keys are in your env (agent reads them)
echo "$LINEAR_API_KEY" && echo "$TELNYX_API_KEY"  # both must be non-empty
```

## Run the bot (paste this into opencode / Claude Code / Codex)

> Run the telnyx-devrel-bot against Linear ticket **DEV-XXX**. Open a real PR (not a dry-run).
>
> Use a fresh clean clone at `/tmp/bot-run` so the bot doesn't touch my working tree:
>
> ```bash
> git clone https://github.com/team-telnyx/telnyx-code-examples.git /tmp/bot-run
> cp -r scripts/bot /tmp/bot-run/scripts/
> cd /tmp/bot-run
> git switch -c bot-bootstrap && git add scripts/bot/ && git -c user.email=bot@local -c user.name=bot commit -m bootstrap
> ```
>
> Then run the runner with these env vars:
>
> ```bash
> export GH_APP_ID=4704723
> export GH_APP_PRIVATE_KEY_PATH=~/Downloads/telnyx-devrel-bot.private-key.pem
> export LINEAR_API_KEY=$LINEAR_API_KEY
> export TELNYX_API_KEY=$TELNYX_API_KEY
> export BOT_REPO_ROOT=/tmp/bot-run
> export AI_MODEL=deepseek-ai/DeepSeek-V4-Flash-0731
> .omo/bot-venv/bin/python scripts/bot/runner.py --ticket DEV-XXX --no-dry-run
> ```
>
> Report the PR URL when it's done. If verify.py fails, check whether the failures are pre-existing on main (run `verify.py` on a clean main checkout to compare) — only fix failures caused by the new sample, not pre-existing ones.

## Dry-run (no PR, no Linear state change — for review before opening)

Same as above but drop `--no-dry-run`:

```bash
.omo/bot-venv/bin/python scripts/bot/runner.py --ticket DEV-XXX
```

Files land in `/tmp/bot-run/<sample-name>/` for you to inspect. No branch, no PR, no Linear update.

## What the bot does

1. Reads Linear ticket, parses `## Sample: <name>` from the description
2. Calls Telnyx Inference (DeepSeek-V4-Flash, two-phase: code → docs)
3. Runs repo gates (`verify.py`, `rewrite_repo_links`, `sync_readme`, `gen_llms_txt`) with auto-fix
4. Branches `linear/<TICKET>-<sample>`, commits as `telnyx-devrel-bot[bot]`, opens PR with `code-samples` label
5. Updates Linear: moves ticket to "In Review" + comments PR URL

Takes ~3 minutes per ticket.

## What you need to provide

| Thing | Where to get it |
|---|---|
| `GH_APP_ID` | `4704723` (Sonam has this) |
| `GH_APP_PRIVATE_KEY_PATH` | Path to `telnyx-devrel-bot.<date>.private-key.pem` (Sonam/Stephen has the original; rotate via App settings if needed) |
| `LINEAR_API_KEY` | Your existing Linear key (already in your env if you use Linear via the agent) |
| `TELNYX_API_KEY` | Your Telnyx API key (already in your env if you use Telnyx APIs) |
| Ticket ID | e.g. `DEV-808` — must be on the DEV team's "Code Samples Week N" project, with `## Sample: \`name\`` in the description |

## Troubleshooting

- **"Working tree is dirty"** — you're running from your real checkout, not `/tmp/bot-run`. Use the clone command above.
- **Inference 524 timeout** — model is too slow. Stick with `deepseek-ai/DeepSeek-V4-Flash-0731` (4-15s per phase). Don't use `moonshotai/Kimi-K2.6` (reasoning model, times out).
- **"label 'code-samples' not found"** — already created on the repo, won't recur. If it does: `curl -X POST -H "Authorization: token <token>" https://api.github.com/repos/team-telnyx/telnyx-code-examples/labels -d '{"name":"code-samples","color":"0E8FB3"}'`
- **`verify.py` red but my sample passes** — pre-existing unregistered folders on main. Not your problem; merge the PR anyway or open a separate PR to register them.
- **Bot identity wrong** — confirm commits show `telnyx-devrel-bot[bot]`. If they show your name, the `GH_*` env vars aren't being picked up.
