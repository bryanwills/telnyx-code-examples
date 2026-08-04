---
name: edge-url-summarizer
title: "Edge URL Summarizer"
description: "URL summarizer on Telnyx Edge Compute Stateful Actors — fetch a URL, summarize via AI Inference, cache the result for instant repeat requests."
language: nodejs
framework: telnyx-edge (Stateful Actors)
telnyx_products: [Edge Compute, AI Inference]
---

# Edge URL Summarizer

URL summarizer on Telnyx Edge Compute Stateful Actors — fetch a URL, summarize via AI Inference, cache the result for instant repeat requests. No ngrok, no external server — runs at `*.telnyxcompute.com`.

## Telnyx API Endpoints Used

- **AI Inference**: `POST /v2/ai/chat/completions` — [API reference](https://developers.telnyx.com/api/inference/chat-completions)

## Architecture

```
  POST /summarize  {"url": "..."}
        │
        ▼
  ┌──────────────────────────────┐
  │ Edge Stateful Actor           │
  │  1. Check cache (hit?)        │
  │  2. Fetch URL → extract text  │
  │  3. AI Inference → summarize  │
  │  4. Cache result              │
  └────────┬─────────────────────┘
           │
     miss  → summarize (~2s)
     hit   → instant return from cache
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

`ship` prints a URL like `edge-url-summarizer-<id>.telnyxcompute.com`.

### 3. Test

Health check first:

```bash
curl -sS --retry 30 --retry-delay 5 https://edge-url-summarizer-<id>.telnyxcompute.com/health/liveness
```

## API Reference

### `POST /summarize`

Summarize a URL. First call hits the model, repeat calls return from cache.

```bash
curl -X POST https://edge-url-summarizer-<id>.telnyxcompute.com/summarize \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/article"}'
```

**First call (cache miss):**

```json
{
  "url": "https://example.com/article",
  "title": "Example Article",
  "bullets": [
    "The article discusses...",
    "A key finding is...",
    "The author argues..."
  ],
  "word_count": 1234,
  "generated_at": "2026-08-04T12:00:00Z",
  "cached": false
}
```

**Second call (cache hit — instant, no model):**

```json
{
  "url": "https://example.com/article",
  ...
  "cached": true
}
```

### `GET /summarize/cached?url=...`

Get a cached summary by URL (no model call, 404 if not cached).

```bash
curl "https://edge-url-summarizer-<id>.telnyxcompute.com/summarize/cached?url=https://example.com/article"
```

### `POST /summarize/refresh`

Invalidate cache for a URL and re-summarize.

```bash
curl -X POST https://edge-url-summarizer-<id>.telnyxcompute.com/summarize/refresh \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/article"}'
```

### `GET /stats`

Cache hit/miss stats.

```bash
curl https://edge-url-summarizer-<id>.telnyxcompute.com/stats
```

**Response:**

```json
{
  "total_requests": 10,
  "cache_hits": 6,
  "cache_misses": 4,
  "unique_urls": 4,
  "top_urls": ["https://example.com/article"]
}
```

### `GET /cached`

List all cached URLs.

```bash
curl https://edge-url-summarizer-<id>.telnyxcompute.com/cached
```

### `GET /health/{liveness,readiness}`

Health checks.

```bash
curl https://edge-url-summarizer-<id>.telnyxcompute.com/health/liveness
```

## How the Cache Works

The `Summarizer` actor stores each summary in `this.ctx.storage` keyed by URL. When a request comes in:

1. Check `ctx.storage` for the URL — if found, return instantly (cache hit)
2. If not found, fetch the URL, call AI Inference, store the summary, return it (cache miss)
3. Stats track hits vs. misses in the same storage

The actor instance (`idFromName("global")`) is shared across all requests — all summaries live in one place.

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| `404 page not found` | Function still deploying | Wait ~30s, then retry |
| `TELNYX_API_KEY not configured` | Secret missing | `telnyx-edge secrets add TELNYX_API_KEY "<key>"` |
| `failed to fetch URL` | URL unreachable or blocked | Try a publicly accessible URL |
| Slow response | Cache miss hitting model | First call per URL takes ~2s; repeat calls are instant |
| `no content from model` | Empty page or extraction failed | Try a text-rich page |

## Related Examples

- [AI URL Quiz Generator (Python)](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/quiz-generator-python/README.md)
- [AI Call Recording Redactor (Python)](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/call-recording-redactor-python/README.md)
- [AI Voicemail Smart Router (Python)](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/voicemail-smart-router-python/README.md)
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
