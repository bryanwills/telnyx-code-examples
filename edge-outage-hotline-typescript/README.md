---
name: edge-outage-hotline-typescript
title: "Regional Outage-Reporting Hotline"
description: "Regional outage-reporting hotline on Telnyx Edge Compute — one Stateful Actor per region aggregates callers' reports into SQL, dedupes them with Durable KV, classifies each report with Telnyx's decision model endpoint in one call, and serves a live incident dashboard with a measured model accuracy report card."
language: typescript
framework: telnyx-edge (Stateful Actors, Durable KV, SQLDB)
telnyx_products: [Edge Compute, Decision Model]
---

# Regional Outage-Reporting Hotline

Callers report outages by region; a region-keyed Stateful Actor classifies each report with one call to Telnyx's hosted decision model endpoint, aggregates them in actor-local SQL, keeps dedupe context in Durable KV, and serves a live incident dashboard — with a **measured** model accuracy report card, not an assumed one. No ngrok, no external hosting — runs at `*.telnyxcompute.com`.

## Why Telnyx

Telnyx is an **AI Communications Infrastructure** platform. This demo leans on three Edge Compute primitives — Stateful Actors, Durable KV, and SQLDB — plus the hosted decision model endpoint, and each one earns its place:

- **Stateful Actor keyed by region (not by caller)** — during an outage, many callers report the *same* problem. Keying the actor by region means their reports converge into one actor's storage, which is what makes aggregation, dedupe, and escalation meaningful at all.
- **SQLDB (actor-local SQLite)** — the dashboard needs `GROUP BY` counts, "reports in the last hour", and severity breakdowns. That's relational work; a KV dump can't answer it without reading everything.
- **Durable KV** — a tiny "current known issue" blob read on *every* incoming report to build the model's dedupe context. One KV read beats a SQL query for a question you ask on every single report. (The ablation in the report card section shows the context measurably changes the model's duplicate judgment: same text, `is_duplicate` 0.75 without context vs 0.997 with it.)
- **Decision model endpoint** — during a real outage the report firehose is exactly when you need classification to be fast and cheap. One request answers three questions (issue type, severity, duplicate?) in ~400 input tokens / 4 output tokens — no LLM call per question.

## Telnyx API Endpoints Used

- **Decision model (BETA)**: `POST https://api.telnyx.com/v2/ai/typesafe/v1/systemone` — typed answers (`choice` / `score` / `noul`) for multiple questions in one request, with a Bearer API key. No SDK needed — plain `fetch`.

Edge Compute primitives (Stateful Actors, Durable KV, SQLDB) are runtime surfaces (`this.ctx.storage.*`), not REST endpoints — declared in `telnyx.toml` and shipped by the Edge CLI.

## Architecture

```
   POST /intake?region=415  {"reporter": "...", "text": "Internet is down"}
         │
         ▼
   ┌─────────────────────────────────────────────────────────┐
   │  RegionAgent actor — ONE INSTANCE PER REGION            │
   │  (env.REGIONS.idFromName("region-415"))                 │
   │                                                         │
   │  1. KV read   → active_issue {issue_type, first_seen}   │
   │  2. Decision model (one call, 3 questions):             │
   │        issue_type   → choice (no_service|degraded|      │
   │                              billing|other)             │
   │        severity     → score (fractional 0–3)            │
   │        is_duplicate → noul (0–1, no confidence field)   │
   │  3. SQL write → reports table (raw + rounded values)    │
   │  4. KV policy → same type: bump last_seen               │
   │                  new type:  overwrite slot              │
   │                  billing:   never own the slot          │
   │  5. Escalate if sev ≥ High AND noul < 0.35              │
   │        AND issue_type ≠ billing (app logic, not model)  │
   └─────────────────────────────────────────────────────────┘
         │
         ▼
   GET /  (dashboard)  ←── polls ──  GET /api/summary?regions=415,212
                                     GET /api/eval?region=415

   loadgen.mjs — fires a labeled 13-report scenario at one region:
   seed outage → pile-on burst → billing noise → new degraded issue
   → distinct critical incident. Ground truth is stored alongside the
   model's answer, powering the dashboard's report card.
```

All state is **per actor**: each region actor owns a private SQLite database (`this.ctx.storage.sql`) and its own KV namespace (`this.ctx.storage.get/put`). Both survive redeploys — the demo proves it on camera. Cross-region aggregation is a fan-out from the HTTP layer (`/api/summary`) because per-actor SQL is private by design.

## Environment Variables

Secrets are set on the function via the Edge CLI (never committed):

```bash
telnyx-edge secrets add TELNYX_API_KEY "KEY0123..."
```

| Variable | Type | Example | Required | Description | Where to get it |
|----------|------|---------|----------|-------------|-----------------|
| `TELNYX_API_KEY` | `string` | `KEY0123...` | **yes** | Telnyx API v2 key (secret) — authorizes the decision model endpoint | [Portal](https://portal.telnyx.com/api-keys) |

> **Agent / CLI access**
>
> ```bash
> # Deploy the Edge function (Stateful Actor + Durable KV + SQLDB, no external hosting)
> npm install && telnyx-edge ship          # URL: https://edge-outage-hotline-typescript-<id>.telnyxcompute.com
>
> # Provision the API key the function uses (no phone number needed for the core demo)
> telnyx-edge secrets add TELNYX_API_KEY "<your key>"
> ```

For full API discovery, point your agent at [`llms-full.txt`](https://developers.telnyx.com/llms-full.txt).

## Setup

### Prerequisites

- [Telnyx Edge CLI](https://github.com/team-telnyx/edge-compute/releases) v0.4+
- Node.js 18+ (for the load script)
- [API key](https://portal.telnyx.com/api-keys)

<details>
<summary>Programmatic / CLI setup</summary>

```bash
# Install CLI — https://developers.telnyx.com/development/cli
go install github.com/team-telnyx/telnyx-cli/cmd/telnyx@latest
telnyx auth login

# Provision resources
telnyx-edge auth api-key set <YOUR_API_KEY>
telnyx-edge secrets add TELNYX_API_KEY "<YOUR_API_KEY>"
```

For full API discovery, point your agent at [`llms-full.txt`](https://developers.telnyx.com/llms-full.txt).

</details>

### 1. Set the secret

```bash
telnyx-edge secrets add TELNYX_API_KEY "KEY0123..."
```

### 2. Create + deploy the function

```bash
telnyx-edge new-func --actor -l ts -n edge-outage-hotline-typescript   # registers the function, prints func_id
# copy the printed [edge_compute] block into telnyx.toml
npm install
telnyx-edge ship
```

`ship` prints the public URL: `https://edge-outage-hotline-typescript-<id>.telnyxcompute.com`.

### 3. Fire the demo load and watch the dashboard

```bash
node loadgen.mjs --url https://edge-outage-hotline-typescript-<id>.telnyxcompute.com --region 415 --reset
```

Then open `https://edge-outage-hotline-typescript-<id>.telnyxcompute.com/` in a browser — region cards, severity breakdown, the deduplicated issue list, escalation flags, and the model report card update live every 4 seconds while the load script runs.

## API Reference

Full typed reference in [API.md](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/edge-outage-hotline-typescript/API.md). Summary:

### `POST /intake?region=<r>`

Classify + store one report. Body: `{"reporter": "...", "text": "...", "expected_issue_type": "no_service"?, "expected_severity": "High"?, "expected_duplicate": 1?}` — the `expected_*` fields are demo-only ground truth used by the eval.

Response echoes the model's answers and every application decision taken:

```json
{
  "region": "415",
  "id": 4,
  "report_count": 4,
  "active_issue": { "issue_type": "no_service", "first_seen": 1790107956527, "last_seen": 1790107956527 },
  "model": {
    "issue_type": "no_service",
    "issue_type_confidence": 0.9918,
    "severity_raw": 2.5534,
    "severity_bucket": 3,
    "is_duplicate": 0.0032
  },
  "escalated": true,
  "kv_updated": true,
  "usage": { "input_tokens": 413, "output_tokens": 4 }
}
```

### `GET /api/summary?regions=415,212`

Fan-out across region actors. Returns per-region `report_count`, `last_hour_count`, `severity_breakdown`, `distinct_issues` (deduplicated), `escalations`, `recent_reports`, and the KV `active_issue`.

### `GET /api/eval?region=<r>`

The model's measured report card for one region: issue-type accuracy + confusion matrix, severity MAE / exact / within-one, duplicate accuracy across a decision-threshold sweep (0.2 / 0.35 / 0.5 / 0.7), and confidence-vs-correctness bins. Computed only over rows carrying ground truth.

### `GET /`, `GET /health/{liveness,readiness}`, `POST /debug/{ingest,reset}`

Dashboard HTML, health checks, and demo affordances (raw ingest without the model; wipe one region's demo state).

## Demo Flow

1. `node loadgen.mjs --url <URL> --region 415 --reset` — fires 13 labeled reports in ~5 seconds
2. Watch the dashboard: severity bar fills, the distinct-issues table rolls forward as new issue types arrive, the seed outage escalates, pile-ons don't
3. Click **Region 212** — a fully isolated actor (private SQL + KV)
4. Read the report card — measured accuracy, not a marketing number

## What the numbers say (measured, not assumed)

One 13-report labeled run against region 415:

| Metric | Result |
|--------|--------|
| Issue-type accuracy | **13/13 (100%)** — confusion matrix entirely diagonal |
| Severity | MAE **0.38** on 0–3 · exact 69% · within-one-bucket 92% |
| Duplicate accuracy | 69% at thresholds 0.2–0.5 · **77% at 0.7** |
| Confidence calibration | monotone with correctness at n=13 (1/1, 4/4, 8/8) — small n, measure your own |

Findings the run surfaced (all visible in the report card):

1. **Severity anchors on context.** With a known `no_service` issue in the KV context, even billing reports scored ~High — the model keys off the state string, not just the report. First run had billing at severity 2.55 without context but High with it.
2. **A billing complaint escalated on the first run** — severity was High and `is_duplicate` was near-zero. The model classified it correctly; the *naive escalation rule* was the bug. This demo now gates escalation on the model's own issue type (billing never escalates).
3. **Related-but-distinct issues get merged by dedupe.** "WiFi keeps dropping" during a known `no_service` outage scored `is_duplicate` 0.93 — the model treats it as the same problem. Honest limitation of one-slot dedupe.
4. **The one-slot KV design forgets older issues.** A second wave of the original outage arriving after a different issue took the slot gets judged against the wrong context — the SQL history still shows both issues, the KV slot only knows the newest one.
5. **A taxonomy gap masqueraded as a model failure.** The downed-pole report classified as `other` at low confidence (0.62) and failed to escalate. Adding a `power_outage` category via one config `PUT` — no redeploy — reclassified the same text at 0.99 confidence and escalated it. See "Live taxonomy" below.

## Docs → code mapping

Every concept on the [Decision Models (beta)](https://developers.telnyx.com/docs/inference/decision-models) page maps to a specific place in this demo:

| Docs concept | Where it lives in this demo |
|---|---|
| **Choose question types**: `choice` selects one option (2–64 option keys) | `issue_type` question — criteria `{no_service, degraded, billing, other}` in `QUESTION_PAYLOAD` (`src/decisionModel.ts`) |
| **Choose question types**: `noul` — "use separate `noul` questions when several independent conditions can be true at once"; no confidence field | `is_duplicate` — deliberately its own question ("is this the SAME already-known outage?"), not folded into the choice; parsed with no confidence field |
| **Choose question types**: `score` — ordered array; answer is the expected zero-based index and **can be fractional** | `severity` — ordered `["Low","Normal","High","Critical"]`; the demo is the docs' own support-incident example (`team`/`production_incident`/`urgency`) with different labels |
| **Use scores in application logic**: "do not treat [the fractional score] as an array index without an application-specific decision rule" | `intakeReport` (`src/regionAgent.ts`): raw float kept in SQL (`severity_raw`) for eval; `clamp(round(score), 0, 3)` applied only for the alerting bucket (`severity_bucket`) |
| **Use scores in application logic**: option scores "are not calibrated probabilities that a decision is correct" | No logic gates on `confidence` anywhere. Escalation uses the model's chosen `issue_type`, the rounded bucket, and the `noul` threshold — confidence is only *measured* in `/api/eval` confidence bins |
| **Use scores in application logic**: "choose review thresholds using representative examples" | The threshold sweep on the report card (69% @ 0.2–0.5 vs 77% @ 0.7) + the first-run billing-escalation finding that motivated the issue-type gate |
| **Response shape**: `model`/`answers`/`usage` top-level, no wrapper; `model` is an opaque identifier | Verified against the live endpoint during the build (probe responses); `runDecisionModel` asserts the shape on every call so silent drift fails loudly |

## Live taxonomy (config-driven, no redeploy)

The classification categories, severity rubric, and escalation thresholds are **data, not code** — stored as a versioned doc in the shared `HotlineConfig` actor and editable at runtime:

```bash
# Read the active taxonomy
curl <URL>/api/config

# Add a category (or change rubric/thresholds) — takes effect on the NEXT report
curl -X PUT <URL>/admin/config -H "Content-Type: application/json" -d '{...config with new issue_type...}'
```

Each category carries its own policy flags (`is_outage`, `may_own_kv_slot`, `escalatable`) — the escalation and KV-dedupe rules read those flags instead of any hardcoded category name. Every report row is stamped with the `schema_version` it was classified under, so historical data stays interpretable when the taxonomy evolves; retired categories still appear in the dashboard (marked retired) if they exist in history.

This isn't decorative — it fixed a real finding. The same utility-pole report that previously classified as `other` (confidence 0.62, and it *failed to escalate* because the model leaned duplicate) classified as a new `power_outage` category at **0.992 confidence → Critical → escalated**, after a one-`PUT` config edit with zero deploys. The model was never the problem; the taxonomy was missing a category.

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| `intake failed` / HTTP 401 from the model | `TELNYX_API_KEY` secret missing from the function | `telnyx-edge secrets add TELNYX_API_KEY "<key>"`, re-ship |
| `409 Function Busy` on `ship` | A previous ship is still running server-side | Wait 1–2 min, or `telnyx-edge reset-func <name> --yes` if stuck in `failed` |
| `404 page not found` | Function still deploying | Wait ~30s, then retry |
| Dashboard shows "refresh failed" | Function redeploying | It reconnects on the next 4s tick |
| Empty report card | No labeled rows yet | Run `loadgen.mjs` (labels come from `expected_*` fields) |
| Eval numbers look stale | Previous run's data | `POST /debug/reset?region=415`, re-run the load |

## Related Examples

- [Edge Call Transcription Agent (TypeScript)](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/edge-call-transcription-agent/README.md) — per-call actors + a shared registry actor; the cross-actor pattern this dashboard's fan-out replaces
- [Edge Prompt A/B Tester (TypeScript)](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/edge-prompt-ab-tester/README.md) — StatefulActor + actor-local KV for experiment state
- [Network Incident Agent](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/network-incident-agent/README.md) — incident timeline in actor SQL + KV
- [Edge Robo-Call Screener (TypeScript)](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/edge-robo-call-screener-typescript/README.md)

## Agent Discovery

This example is part of the [Telnyx Code Examples](https://github.com/team-telnyx/telnyx-code-examples) catalog.

- **Agent signup**: [telnyx.com/agent-signup.md](https://telnyx.com/agent-signup.md) — automated account provisioning via agent mail; get an API key with no human intervention
- **Agent CLI**: [github.com/team-telnyx/ai/tree/main/cli](https://github.com/team-telnyx/ai/tree/main/cli) — composite commands for agents ([commands reference](https://github.com/team-telnyx/ai/tree/main/cli/src/commands))
- **Agent skills**: [github.com/team-telnyx/ai/tree/main/skills](https://github.com/team-telnyx/ai/tree/main/skills)
- **Telnyx AI repo**: [github.com/team-telnyx/ai](https://github.com/team-telnyx/ai)
- **LLM-optimized docs**: [`llms-full.txt`](https://developers.telnyx.com/llms-full.txt)
- **Example index**: [`llms.txt`](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/llms.txt)
- **Telnyx CLI (human)**: [developers.telnyx.com/development/cli](https://developers.telnyx.com/development/cli) — `go install github.com/team-telnyx/telnyx-cli/cmd/telnyx@latest`

## Resources

- [Stateful Actors Quick Start](https://developers.telnyx.com/docs/edge-compute/stateful-actors/quick-start)
- [Edge Compute](https://telnyx.com/products/edge-compute) — deploy functions and Stateful Actors to `*.telnyxcompute.com`
- [AI Inference Guide](https://developers.telnyx.com/docs/inference)
- [Telnyx API Reference](https://developers.telnyx.com/api-reference)
- [TypeScript SDK](https://developers.telnyx.com/development/sdk/javascript)
- [Telnyx Pricing](https://telnyx.com/pricing)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Telnyx Portal](https://portal.telnyx.com)

## Why Telnyx

Telnyx is an **AI Communications Infrastructure** platform — voice, messaging, SIP, AI, and IoT on one private, global network. Stateful Actors, Durable KV, and SQLDB let an Edge Compute function hold real application state next to the phone network, and the hosted decision model classifies a report in one cheap request — no orchestration layer, no model hosting, no cold LLM bills during an incident.
