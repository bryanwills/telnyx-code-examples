# Build an Edge Prompt A/B Tester

Prompt A/B tester on Telnyx Edge Compute Stateful Actors — run two prompt variants against the same task, collect votes, and see which prompt wins.

## How It Works

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

## Telnyx Products Used

- **Edge Compute (Stateful Actors)** — Durable vote tracking per experiment
- **AI Inference** — Both prompt variants run against the same task in parallel

## API Endpoints

- **AI Inference**: `POST /v2/ai/chat/completions` — [API reference](https://developers.telnyx.com/api/inference/chat-completions)

## Prerequisites

- [Telnyx Edge CLI](https://github.com/team-telnyx/edge-compute/releases) v0.2.2+
- Node.js 18+
- [API key](https://portal.telnyx.com/api-keys)

## Step 1: Understand the Code

### `src/abTester.ts` — The Stateful Actor

Tracks experiments and votes in durable storage:

```typescript
export class ABTester extends StatefulActor {
  async createExperiment(experiment) {
    // store experiment in this.ctx.storage
  }
  async vote(experimentId, variant) {
    // increment votes_a or votes_b
    // update per-experiment vote counts
    // update global vote counts
  }
  async closeExperiment(experimentId) {
    // mark as closed
  }
  async getStats() {
    // return experiments, votes, leader
  }
}
```

### `src/index.ts` — The Fetch Handler

Two inference calls run in parallel:

```typescript
const [respA, respB] = await Promise.all([
  runPrompt(apiKey, promptA, task),
  runPrompt(apiKey, promptB, task),
]);
```

Both responses are returned so the user can compare and vote.

### All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/experiments` | Create A/B experiment |
| `POST` | `/experiments/<id>/vote` | Vote for variant A or B |
| `POST` | `/experiments/<id>/close` | Close experiment |
| `GET` | `/experiments` | List experiments |
| `GET` | `/experiments/<id>` | Get specific experiment |
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

### Create experiment

```bash
curl -X POST $FUNC_URL/experiments \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Write a one-sentence tagline for an edge compute platform.",
    "variant_a": "You are a concise marketing copywriter. Return just the tagline.",
    "variant_b": "You are a technical explainer. Return just the tagline, focus on latency."
  }'
```

### Vote on variants

```bash
# Vote for variant A
curl -X POST $FUNC_URL/experiments/exp-XXXX/vote \
  -H "Content-Type: application/json" \
  -d '{"variant":"a"}'

# Vote for variant B
curl -X POST $FUNC_URL/experiments/exp-XXXX/vote \
  -H "Content-Type: application/json" \
  -d '{"variant":"b"}'
```

### Close and see who's winning

```bash
curl -X POST $FUNC_URL/experiments/exp-XXXX/close
curl $FUNC_URL/stats
```

## Going to Production

- **Blind evaluation** — return both responses in random order with labels hidden, user picks without knowing which is which
- **Multi-variant** — run prompts A/B/C/D and use a Swiss-style tournament to eliminate losers
- **Threshold winner** — auto-close the experiment when one variant reaches a confidence threshold (e.g., 95% at 10+ votes)
- **Webhook on close** — notify a webhook when the experiment closes with the winning prompt
- **Persistent leaderboard** — track winning prompt templates over time and auto-promote them
- **Cost tracking** — track tokens used per variant to favor cheaper prompts

## Run

```bash
npm install
telnyx-edge ship
```

## Resources

- [Source code and reference](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/edge-prompt-ab-tester/README.md)
- [Stateful Actors Quick Start](https://developers.telnyx.com/docs/edge-compute/stateful-actors/quick-start)
- [AI Inference docs](https://developers.telnyx.com/docs/inference)
- [Edge Compute CLI](https://github.com/team-telnyx/edge-compute/releases)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Telnyx Portal](https://portal.telnyx.com)
