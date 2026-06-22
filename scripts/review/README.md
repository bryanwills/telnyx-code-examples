# PR-review toolkit

Composable gates that codify the manual review patterns behind the recent
correctness PRs, so contributor PRs get auto-screened before a human reads them.
Each script exits non-zero on findings and takes `--path` (any checkout/PR
worktree) plus `--changed-against <ref>` for **diff-aware** mode.

| Script | Gates |
|--------|-------|
| `check_pinning.py` | unpinned / `latest` dependencies across npm · pip · Go · Ruby · PHP · .NET · Maven |
| `check_required_files.py` | per-example required files (README/API.md/GUIDE.md/.env.example + code + dep) and no forbidden `Dockerfile`/`Makefile` |
| `check_legacy_sdk.py` | references to dead/old Telnyx SDK APIs in code **and docs** (e.g. `messages.create`, `Telnyx.APIStatusError`, `ai_assistants`, the wrong Go module) |
| `review_pr.sh` | runs all gates + `verify.py` against a base ref |

## Diff-aware gating

`main` carries pre-existing backlog (unpinned deps, some folders missing docs).
A hard repo-wide gate would block every PR on that debt, so CI runs the gates in
**diff-aware** mode — they only check the example folders a PR actually changes.
`verify.py` (which already passes on `main`) runs full as the authoritative gate.

```bash
# everything, the way CI runs it:
scripts/review/review_pr.sh origin/main

# a single gate, diff-aware:
python scripts/review/check_pinning.py --changed-against origin/main

# a single gate, whole repo (shows the full backlog):
python scripts/review/check_pinning.py
```

CI wiring: `.github/workflows/pr-review-gates.yml`.
