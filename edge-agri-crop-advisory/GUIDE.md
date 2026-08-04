# Build an Edge Agri Crop Advisory

Agriculture crop advisory on Telnyx Edge Compute Stateful Actors — classify crop issues and recommend treatment via AI Inference. Continuation of the URL fetch + summarize pattern from the URL summarizer.

## How It Works

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
  └──────────────────────────────┘
```

## Telnyx Products Used

- **Edge Compute (Stateful Actors)** — Durable storage for advisories and cumulative stats
- **AI Inference** — LLM classifies the crop issue into disease, pest, nutrient, water, or weather, plus severity and treatment

## API Endpoints

- **AI Inference**: `POST /v2/ai/chat/completions` — [API reference](https://developers.telnyx.com/api/inference/chat-completions)

## Prerequisites

- [Telnyx Edge CLI](https://github.com/team-telnyx/edge-compute/releases) v0.2.2+
- Node.js 18+
- [API key](https://portal.telnyx.com/api-keys)

## Step 1: Understand the Code

### `src/cropAdvisory.ts` — The Stateful Actor

Stores advisories and stats in durable `ctx.storage`:

```typescript
export class CropAdvisory extends StatefulActor {
  async addAdvisory(advisory: Advisory) {
    // store the advisory
    // update stats: total, by issue type, by severity, escalations, recent crops
  }
  async getAdvisory(id: string) { /* fetch one */ }
  async listAdvisories(limit: number) { /* recent first */ }
  async getCropStats() { /* cumulative stats */ }
}
```

### `src/index.ts` — The Fetch Handler

Two paths:
- **Text**: `POST /advisory` with `description` → directly classify
- **URL**: `POST /advisory` with `url` → fetch the article → use the text as the description

The classification prompt asks the LLM to act as an extension agronomist and return:

```json
{
  "crop_type": "corn",
  "issue_type": "disease | pest | nutrient | water | weather",
  "severity": "low | medium | high | critical",
  "confidence": 0.0-1.0,
  "recommendation": "treatment in 1-2 sentences"
}
```

If the severity is `critical`, the advisory gets `escalate: true` and `escalated_to: "agronomist-on-call"`.

### Declared storage

```toml
[[actors]]
binding = "CROP_ADVISORY"
type    = "CropAdvisory"

[[secrets]]
binding = "TELNYX_API_KEY"
name    = "TELNYX_API_KEY"
```

### All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/advisory` | Classify a crop issue (text or URL) |
| `GET` | `/advisories` | List recent advisories |
| `GET` | `/advisories/<id>` | Get a specific advisory |
| `GET` | `/stats` | Cumulative stats |
| `GET` | `/health/{liveness,readiness}` | Health probes |

## Step 2: Deploy

```bash
telnyx-edge auth api-key set <YOUR_API_KEY>
telnyx-edge secrets add TELNYX_API_KEY "KEY0123..."
npm install
telnyx-edge ship
```

## Step 3: Test

### Health

```bash
curl -sS --retry 30 --retry-delay 5 \
  https://edge-agri-crop-advisory-<id>.telnyxcompute.com/health/liveness
```

### Disease (text)

```bash
curl -X POST https://edge-agri-crop-advisory-<id>.telnyxcompute.com/advisory \
  -H "Content-Type: application/json" \
  -d '{"description":"My corn has yellow streaks on bottom leaves and dark brown spots. About 30% affected."}'
```

### Drought (text)

```bash
curl -X POST https://edge-agri-crop-advisory-<id>.telnyxcompute.com/advisory \
  -H "Content-Type: application/json" \
  -d '{"description":"My wheat is wilting after 3 weeks without rain. Half the field affected."}'
```

### Pest (should escalate if critical)

```bash
curl -X POST https://edge-agri-crop-advisory-<id>.telnyxcompute.com/advisory \
  -H "Content-Type: application/json" \
  -d '{"description":"Locust swarm just arrived yesterday. My entire soybean field is being devoured. 90% already destroyed."}'
```

### URL (fetch article and analyze)

```bash
curl -X POST https://edge-agri-crop-advisory-<id>.telnyxcompute.com/advisory \
  -H "Content-Type: application/json" \
  -d '{"url":"https://extension.umn.edu/news/aphid-control"}'
```

### Check stats

```bash
curl https://edge-agri-crop-advisory-<id>.telnyxcompute.com/stats
```

## Going to Production

- **SMS notifications** — if `escalate: true`, send an SMS to the agronomist instead of just flagging
- **Image analysis** — accept a photo of the affected plant and pass to a vision model
- **Location-aware** — use the farmer's location to pull local disease pressure, weather, and spraying windows
- **Trend tracking** — actor alarms to detect infestations spreading across regions
- **Interactive advising** — follow-up questions via a second LLM pass to gather more detail before classifying
- **Commodity tracking** — correlate advisories with crop market prices for context-aware advice

## Run

```bash
npm install
telnyx-edge ship
```

## Resources

- [Source code and reference](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/edge-agri-crop-advisory/README.md)
- [Stateful Actors Quick Start](https://developers.telnyx.com/docs/edge-compute/stateful-actors/quick-start)
- [AI Inference docs](https://developers.telnyx.com/docs/inference)
- [Edge Compute CLI](https://github.com/team-telnyx/edge-compute/releases)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Telnyx Portal](https://portal.telnyx.com)
