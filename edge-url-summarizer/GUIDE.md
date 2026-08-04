# Build an Edge URL Summarizer

URL summarizer on Telnyx Edge Compute Stateful Actors — fetch a URL, summarize via AI Inference, cache the result for instant repeat requests. No ngrok, no external server.

## How It Works

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

## Telnyx Products Used

- **Edge Compute (Stateful Actors)** — Durable per-request state: stores summaries in `ctx.storage`, persists across invocations
- **AI Inference** — LLM generates the 3-bullet-point summary per unique URL

## API Endpoints

- **AI Inference**: `POST /v2/ai/chat/completions` — [API reference](https://developers.telnyx.com/api/inference/chat-completions)

## Prerequisites

- [Telnyx Edge CLI](https://github.com/team-telnyx/edge-compute/releases) v0.2.2+
- Node.js 18+
- [API key](https://portal.telnyx.com/api-keys)

## Step 1: Understand the Code

### `src/summarizer.ts` — The Stateful Actor

Each actor instance stores summaries and stats in `this.ctx.storage`:

```typescript
export class Summarizer extends StatefulActor {
  async getSummary(url: string) {
    const map = await this.getMap();
    return map[url];            // undefined or CachedSummary
  }
  async cacheSummary(url: string, summary: CachedSummary) {
    const map = await this.getMap();
    map[url] = summary;
    await this.saveMap(map);
    // also update stats
  }
  async recordHit()  { /* increment cache_hits */ }
  async recordMiss() { /* increment cache_misses */ }
  async invalidate(url: string) { /* delete from cache */ }
  async getSummaryStats() { /* return hits/misses */ }
}
```

### `src/index.ts` — The Fetch Handler

Routes HTTP to actor methods. The key decision: check cache first, only call the model on a miss:

```typescript
if (url.pathname === "/summarize" && req.method === "POST") {
  // 1. Check cache
  const cached = await stub.getSummary(targetUrl);
  if (cached) {
    await stub.recordHit();
    return Response.json({ ...cached, cached: true });
  }
  // 2. Cache miss → fetch + summarize + cache
  const text = await fetchUrlText(targetUrl);
  const bullets = await summarizeViaInference(text);
  await stub.cacheSummary(targetUrl, summary);
  return Response.json({ ...summary, cached: false }, { status: 201 });
}
```

### `telnyx.toml` — Config

```toml
[[actors]]
binding = "SUMMARIZER"
type    = "Summarizer"

[[secrets]]
binding = "TELNYX_API_KEY"
name    = "TELNYX_API_KEY"

[edge_compute]
func_id   = "8585aaaa-cf1e-4f44-9f4d-eccd7526f8f0"
func_name = "edge-url-summarizer"
```

### All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/summarize` | Summarize a URL (cached for repeats) |
| `GET` | `/summarize/cached` | Get cached summary by URL |
| `POST` | `/summarize/refresh` | Invalidate cache for a URL |
| `GET` | `/stats` | Cache hit/miss stats |
| `GET` | `/cached` | List all cached URLs |
| `GET` | `/health/liveness` | Liveness probe |
| `GET` | `/health/readiness` | Readiness probe |

## Step 2: Deploy

```bash
telnyx-edge auth api-key set <YOUR_API_KEY>
telnyx-edge secrets add TELNYX_API_KEY "KEY0123..."
npm install
telnyx-edge ship
```

## Step 3: Test

### Health check

```bash
curl -sS --retry 30 --retry-delay 5 \
  https://edge-url-summarizer-<id>.telnyxcompute.com/health/liveness
```

### First call (slow — model call)

```bash
curl -X POST https://edge-url-summarizer-<id>.telnyxcompute.com/summarize \
  -H "Content-Type: application/json" \
  -d '{"url":"https://telnyx.com/blog/edge-compute"}'
```

### Second call (instant — from cache)

```bash
curl -X POST https://edge-url-summarizer-<id>.telnyxcompute.com/summarize \
  -H "Content-Type: application/json" \
  -d '{"url":"https://telnyx.com/blog/edge-compute"}'
# → "cached": true
```

### Check stats

```bash
curl https://edge-url-summarizer-<id>.telnyxcompute.com/stats
```

### Invalidate and re-summarize

```bash
curl -X POST https://edge-url-summarizer-<id>.telnyxcompute.com/summarize/refresh \
  -H "Content-Type: application/json" \
  -d '{"url":"https://telnyx.com/blog/edge-compute"}'
```

## Going to Production

- **URL normalization** — strip query params and fragments before caching (`?utm_source=...` shouldn't create separate entries)
- **TTL** — auto-expire summaries after N hours to pick up updated content
- **Word-level caching** — share summaries across URLs with similar content (semantic dedup)
- **Custom summary styles** — accept a `style` param (bullets, paragraph, tldr)
- **Rate limiting** — protect against abuse on the inference calls
- **Webhooks** — notify when a new URL is summarized (product update for your team)
- **Multi-model** — let users choose which model summarizes (fast vs. deep)

## Run

```bash
npm install
telnyx-edge ship
```

## Resources

- [Source code and reference](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/edge-url-summarizer/README.md)
- [Stateful Actors Quick Start](https://developers.telnyx.com/docs/edge-compute/stateful-actors/quick-start)
- [AI Inference docs](https://developers.telnyx.com/docs/inference)
- [Edge Compute CLI](https://github.com/team-telnyx/edge-compute/releases)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Telnyx Portal](https://portal.telnyx.com)
