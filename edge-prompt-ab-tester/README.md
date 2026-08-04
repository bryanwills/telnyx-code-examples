---
name: edge-prompt-ab-tester
title: "Edge Prompt A/B Tester"
description: "Prompt A/B tester on Telnyx Edge Compute Stateful Actors — run two prompt variants against the same task, collect user votes, and track which prompt wins."
language: nodejs
framework: telnyx-edge (Stateful Actors)
telnyx_products: [Edge Compute, AI Inference]
---

# Edge Prompt A/B Tester

Prompt A/B tester on Telnyx Edge Compute Stateful Actors — run two prompt variants against the same task, collect user votes, and track which prompt wins. No ngrok, no external server — runs at `*.telnyxcompute.com`.

## Telnyx API Endpoints Used

- **AI Inference**: `POST /v2/ai/chat/completions` — [API reference](https://developers.telnyx.com/api/inference/chat-completions)

## Architecture

```
  POST /experiments  {"task": "...", "variant_a": "...", "variant_b": "..."}
        │
        ▼
  ┌──────────────────────────────┐
  │ Edge Stateful Actor           │
  │  1. Run both prompts vs task  │
  │  2. Return promptA + promptB  │
  │  3. Track votes per variant   │
  │  4. Declare leader            │
  └──────────────────────────────┘
        │
     open experiment
       │       │
     vote A   vote B
       │       │
     close → winner declared
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

`ship` prints a URL like `edge-prompt-ab-tester-<id>.telnyxcompute.com`.

### 3. Test

Health check first:

```bash
curl -sS --retry 30 --retry-delay 5 https://edge-prompt-ab-tester-<id>.telnyxcompute.com/health/liveness
```

## API Reference

### `POST /experiments`

Create an A/B experiment — run both prompt variants against the same task, return both responses so the user can compare and vote.

```bash
curl -X POST https://edge-prompt-ab-tester-<id>.telnyxcompute.com/experiments \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Write a one-sentence tagline for an edge compute platform.",
    "variant_a": "You are a concise marketing copywriter. Return just the tagline.",
    "variant_b": "You are a technical explainer. Return just the tagline, focus on latency."
  }'
```

**Response:**

```json
{
  "id": "exp-msf712rs-0",
  "task": "Write a one-sentence tagline for an edge compute platform.",
  "variant_a": {
    "prompt": "You are a concise marketing copywriter. Return just the tagline.",
    "response": "Real-time compute, right where your data lives."
  },
  "variant_b": {
    "prompt": "You are a technical explainer. Return just the tagline, focus on latency.",
    "response": "Execute code milliseconds from your users to eliminate network latency."
  },
  "votes_a": 0,
  "votes_b": 0,
  "status": "open",
  "created_at": "2026-08-04T21:51:55Z"
}
```

### `POST /experiments/<id>/vote`

Vote for a variant. The experiment continues accumulating votes until closed.

```bash
curl -X POST https://edge-prompt-ab-tester-<id>.telnyxcompute.com/experiments/exp-msf712rs-0/vote \
  -H "Content-Type: application/json" \
  -d '{"variant":"a"}'
```

### `POST /experiments/<id>/close`

Close the experiment — no more votes accepted.

```bash
curl -X POST https://edge-prompt-ab-tester-<id>.telnyxcompute.com/experiments/exp-msf712rs-0/close
```

### `GET /experiments`

List experiments (most recent first).

```bash
curl https://edge-prompt-ab-tester-<id>.telnyxcompute.com/experiments
```

### `GET /experiments/<id>`

Get a specific experiment with its variants and vote counts.

```bash
curl https://edge-prompt-ab-tester-<id>.telnyxcompute.com/experiments/exp-msf712rs-0
```

### `GET /stats`

Cumulative stats across all experiments.

```bash
curl https://edge-prompt-ab-tester-<id>.telnyxcompute.com/stats
```

**Response:**

```json
{
  "total_experiments": 3,
  "open_experiments": 2,
  "closed_experiments": 1,
  "total_votes": 15,
  "leader": "variant_a",
  "leader_votes": 9
}
```

### `GET /health/{liveness,readiness}`

Health checks.

```bash
curl https://edge-prompt-ab-tester-<id>.telnyxcompute.com/health/liveness
```

## Demo Flow

1. Create experiment → both responses returned (user reads and compares)
2. User votes A or B → count increments
3. More users/votes → actor state accumulates in durable storage
4. Close experiment → see final vote breakdown
5. Check stats → see which variant is winning across all experiments

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| `404 page not found` | Function still deploying | Wait ~30s, then retry |
| `TELNYX_API_KEY not configured` | Secret missing | `telnyx-edge secrets add TELNYX_API_KEY "<key>"` |
| Slow to return | Two inference calls in parallel | Expected (~2s for both) |
| Votes not accumulating | Actor state not persisting | Check actor deployment status at `telnyx-edge list` |
| `experiment not found or closed` | Voting on closed/nonexistent ID | Create new experiment first |

## Related Examples

- [Edge URL Summarizer (TypeScript)](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/edge-url-summarizer/README.md)
- [Edge Agri Crop Advisory (TypeScript)](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/edge-agri-crop-advisory/README.md)
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
