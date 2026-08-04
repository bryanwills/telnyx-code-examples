---
name: edge-agri-crop-advisory
title: "Edge Agri Crop Advisory"
description: "Agriculture crop advisory on Telnyx Edge Compute Stateful Actors — classify crop issues (disease, pest, nutrient, water, weather) and recommend treatment via AI Inference. Escalates critical cases."
language: nodejs
framework: telnyx-edge (Stateful Actors)
telnyx_products: [Edge Compute, AI Inference]
---

# Edge Agri Crop Advisory

Agriculture crop advisory on Telnyx Edge Compute Stateful Actors — classify crop issues (disease, pest, nutrient, water, weather) and recommend treatment via AI Inference. Escalates critical cases to an agronomist. No ngrok, no external server — runs at `*.telnyxcompute.com`. Continuation of the URL fetch + summarize pattern from the [Edge URL Summarizer](../edge-url-summarizer/README.md).

## Telnyx API Endpoints Used

- **AI Inference**: `POST /v2/ai/chat/completions` — [API reference](https://developers.telnyx.com/api/inference/chat-completions)

## Architecture

```
  POST /advisory  {"description": "..."} or {"url": "..."}
        │
        ▼
  ┌──────────────────────────────┐
  │ Edge Stateful Actor           │
  │  1. Fetch URL (if provided)   │
  │  2. AI Inference              │
  │     → classify issue type     │
  │     → severity                │
  │     → treatment               │
  │  3. Escalate if critical      │
  │  4. Store in durable storage  │
  └────────┬─────────────────────┘
           │
     Advisories + stats persist
     across requests
```

## Environment Variables / Secrets

Set secrets via the Edge CLI:

```bash
telnyx-edge secrets add TELNYX_API_KEY "KEY0123..."
```

| Variable | Type | Example | Required | Description | Where to get it |
|----------|------|---------|----------|-------------|-----------------|
| `TELNYX_API_KEY` | `string` | `KEY0123...` | **yes** | Telnyx API v2 key (secret) | [Portal](https://portal.telnyx.com/api-keys) |
| `AI_MODEL` | `string` | `zai-org/GLM-5.2` | no | Inference model (in `telnyx.toml`) | [Models](https://developers.telnyx.com/docs/inference/models) |

## Setup

### Prerequisites

- [Telnyx Edge CLI](https://github.com/team-telnyx/edge-compute/releases) v0.2.2+
- Node.js 18+
- [API key](https://portal.telnyx.com/api-keys)

### 1. Set secrets

```bash
telnyx-edge auth api-key set <YOUR_API_KEY>
telnyx-edge secrets add TELNYX_API_KEY "KEY0123..."
```

### 2. Deploy

```bash
npm install
telnyx-edge ship
```

`ship` prints a URL like `edge-agri-crop-advisory-<id>.telnyxcompute.com`.

### 3. Test

Health check first:

```bash
curl -sS --retry 30 --retry-delay 5 https://edge-agri-crop-advisory-<id>.telnyxcompute.com/health/liveness
```

## API Reference

### `POST /advisory`

Classify a crop issue from a description (or fetch from a URL) and return a structured advisory.

```bash
curl -X POST https://edge-agri-crop-advisory-<id>.telnyxcompute.com/advisory \
  -H "Content-Type: application/json" \
  -d '{"description":"My corn has yellow streaks on bottom leaves with dark brown spots. About 30% of plants affected."}'
```

**Response:**

```json
{
  "id": "adv-msf1zxyc-0",
  "farmer_description": "My corn has yellow streaks...",
  "source": "text",
  "crop_type": "corn",
  "issue_type": "disease",
  "severity": "medium",
  "confidence": 0.7,
  "recommendation": "Yellow streaks with dark brown spots are consistent with a fungal leaf blight. Apply a foliar fungicide and scout weekly.",
  "escalate": false,
  "generated_at": "2026-08-04T19:31:04Z"
}
```

Escalation (critical severity):

```json
{
  "issue_type": "locust swarm",
  "severity": "critical",
  "escalate": true,
  "escalated_to": "agronomist-on-call",
  "recommendation": "Contact local authorities immediately for emergency spraying. Report to regional locust monitoring."
}
```

With a URL input:

```bash
curl -X POST https://edge-agri-crop-advisory-<id>.telnyxcompute.com/advisory \
  -H "Content-Type: application/json" \
  -d '{"url":"https://extension.umn.edu/news/something-about-aphids"}'
```

### `GET /advisories`

List recent advisories (most recent first).

```bash
curl https://edge-agri-crop-advisory-<id>.telnyxcompute.com/advisories
curl "https://edge-agri-crop-advisory-<id>.telnyxcompute.com/advisories?limit=10"
```

### `GET /advisories/<id>`

Get a specific advisory by ID.

```bash
curl https://edge-agri-crop-advisory-<id>.telnyxcompute.com/advisories/adv-msf1zxyc-0
```

### `GET /stats`

Cumulative advisory stats.

```bash
curl https://edge-agri-crop-advisory-<id>.telnyxcompute.com/stats
```

**Response:**

```json
{
  "total_advisories": 8,
  "by_issue_type": {"disease": 3, "pest": 2, "water": 2, "nutrient": 1},
  "by_severity": {"low": 1, "medium": 3, "high": 2, "critical": 2},
  "escalations": 2,
  "recent_crop_types": ["corn", "soybean", "wheat"]
}
```

### `GET /health/{liveness,readiness}`

Health checks.

```bash
curl https://edge-agri-crop-advisory-<id>.telnyxcompute.com/health/liveness
```

## Issue Categories

| Type | Signs | Typical Severity |
|------|-------|------------------|
| `disease` | Spots, mildew, blight, wilt | low → medium |
| `pest` | Insects, holes, larvae, damage | low → critical (swarm) |
| `nutrient` | Yellowing, purpling, stunting | low → medium |
| `water` | Wilting, curling, drought/flood | medium → high |
| `weather` | Frost, hail, heat stress | medium |

## Escalation Rules

- `severity: critical` → `escalate: true` and `escalated_to`
- `severity: high` → flagged in stats but no auto-escalation
- The agronomist escalation shows how a critical-case flag could drive downstream alerts (SMS, webhook, phone call) without needing live call control

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| `404 page not found` | Function still deploying | Wait ~30s, then retry |
| `TELNYX_API_KEY not configured` | Secret missing | `telnyx-edge secrets add TELNYX_API_KEY "<key>"` |
| `failed to fetch URL` | URL unreachable or blocked | Provide a text description instead |
| Slow response | Cache miss hitting model | First call per URL takes ~2s |
| `no content from model` | Unparseable response | Retry or use a different model |

## Related Examples

- [Edge URL Summarizer (TypeScript)](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/edge-url-summarizer/README.md)
- [AI Voicemail Smart Router (Python)](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/voicemail-smart-router-python/README.md)
- [AI Call Recording Redactor (Python)](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/call-recording-redactor-python/README.md)
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
- [AI Inference Guide](https://developers.telnyx.com/docs/inference)
- [Available Inference Models](https://developers.telnyx.com/docs/inference/models)
- [Edge Compute CLI](https://github.com/team-telnyx/edge-compute/releases)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Telnyx Portal](https://portal.telnyx.com)

## Why Telnyx

Telnyx is an **AI Communications Infrastructure** platform — voice, messaging, SIP, AI, and IoT on one private, global network.
