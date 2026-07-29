---
name: voicemail-smart-router
title: "AI Voicemail Smart Router"
description: "AI Voicemail Smart Router — transcribe voicemails, classify intent (urgent, billing, support, sales, spam, routine), and route to the right channel via Telnyx STT + AI Inference."
language: python
framework: flask
telnyx_products: [AI Inference]
---

# AI Voicemail Smart Router

AI Voicemail Smart Router — transcribe voicemails, classify intent (urgent, billing, support, sales, spam, routine), and route to the right channel via Telnyx STT + AI Inference. Supports both direct transcript and audio file upload.

## Telnyx API Endpoints Used

- **AI Audio Transcriptions**: `POST /v2/ai/audio/transcriptions` — [API reference](https://developers.telnyx.com/api/inference/create-transcription)
- **AI Inference**: `POST /v2/ai/chat/completions` — [API reference](https://developers.telnyx.com/api/inference/chat-completions)

## Architecture

```
  Voicemail (audio or transcript)
        │
        ▼
  ┌──────────────────────────┐
  │ Your App                 │
  └────────┬─────────────────┘
           │
           ├──► Telnyx STT (audio → text)
           │
           ├──► Telnyx AI Inference (classify intent)
           │
           ▼
     Route to channel
       ├── urgent  → Slack alert
       ├── billing → Email
       ├── support → Ticket queue
       ├── sales   → CRM lead
       ├── spam    → Blocklist + archive
       └── routine → Daily digest
```

## Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Type | Example | Required | Description | Where to get it |
|----------|------|---------|----------|-------------|-----------------|
| `TELNYX_API_KEY` | `string` | `KEY0123456789ABCDEF` | **yes** | Telnyx API v2 key | [Portal](https://portal.telnyx.com/api-keys) |
| `AI_MODEL` | `string` | `zai-org/GLM-5.2` | no | Primary inference model | [Models](https://developers.telnyx.com/docs/inference/models) |
| `FALLBACK_MODEL` | `string` | `meta-llama/Llama-3.3-70B-Instruct` | no | Fallback model if primary fails | [Models](https://developers.telnyx.com/docs/inference/models) |
| `SLACK_WEBHOOK` | `string` | `https://hooks.slack.com/...` | no | Slack webhook for urgent alerts | [Slack API](https://api.slack.com/messaging/webhooks) |
| `PORT` | `integer` | `5000` | no | HTTP server port | — |

## Setup

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/voicemail-smart-router-python
cp .env.example .env    # ← fill in your credentials
pip install -r requirements.txt
python app.py           # starts on http://localhost:5000
```

## API Reference

### `POST /voicemails/transcript`

Classify a voicemail transcript and determine routing (no audio needed).

```bash
curl -X POST http://localhost:5000/voicemails/transcript \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "This is an emergency. Our production system is down and we need help immediately.",
    "caller_number": "+17177247292"
  }'
```

**Response:**

```json
{
  "id": "vm-1750280400",
  "transcript": "This is an emergency...",
  "category": "urgent",
  "confidence": 1.0,
  "priority": "high",
  "reason": "The caller reports a production system outage requiring immediate attention.",
  "suggested_action": "Escalate immediately to the on-call engineering team.",
  "route": "slack",
  "routed_to": "#oncall-alerts",
  "routing_status": "delivered",
  "caller_number": "+17177247292",
  "model_used": "zai-org/GLM-5.2",
  "generated_at": "2026-07-29T12:23:52Z"
}
```

### `POST /voicemails/process`

Upload a voicemail audio file → STT → classify → route.

```bash
curl -X POST http://localhost:5000/voicemails/process \
  -F "file=@voicemail.wav" \
  -F "caller_number=+17177247292"
```

### `GET /voicemails`

List all processed voicemails (filter by `?category=urgent`).

```bash
curl http://localhost:5000/voicemails
curl "http://localhost:5000/voicemails?category=billing"
```

### `GET /voicemails/<id>`

Fetch a specific voicemail with its routing decision.

```bash
curl http://localhost:5000/voicemails/vm-1750280400
```

### `GET /routes`

List all routing decisions.

```bash
curl http://localhost:5000/routes
```

### `GET /health`

Returns service health.

```bash
curl http://localhost:5000/health
```

**Response:**

```json
{
  "status": "ok",
  "voicemails": 0,
  "primary_model": "zai-org/GLM-5.2",
  "fallback_model": "meta-llama/Llama-3.3-70B-Instruct",
  "version": "1.0.0"
}
```

## Routing Categories

| Category | Route | Destination | Priority | Example |
|----------|-------|-------------|----------|---------|
| `urgent` | Slack | `#oncall-alerts` | high | "System is down!" |
| `billing` | Email | `billing@company.com` | medium | "Charged twice" |
| `support` | Ticket | `support-queue` | medium | "Calls dropping" |
| `sales` | CRM | `sales-leads` | medium | "Pricing inquiry" |
| `spam` | Blocklist | `archive` | low | "Win a free iPhone" |
| `routine` | Digest | `daily-digest` | low | "Just checking in" |

## Model Fallback

The app tries the primary model (`zai-org/GLM-5.2`) first. If it fails or times out, it automatically falls back to `meta-llama/Llama-3.3-70B-Instruct`. Both are fast non-reasoning models that respond in 1-3 seconds.

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Invalid or missing API key | Verify `TELNYX_API_KEY` in `.env` |
| `400 Bad Request` on audio | Wrong audio format | Use WAV format |
| Slow response | Model timeout | Both models respond in 1-3s; if slow, check network |
| `raw` returned instead of JSON | Model didn't return parseable JSON | Retry or check model name |
| Slack alert not delivered | `SLACK_WEBHOOK` not set | Set the webhook URL in `.env` |

## Related Examples

- [AI Call Recording Redactor (Python)](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/call-recording-redactor-python/README.md)
- [AI Quiz Generator (Python)](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/quiz-generator-python/README.md)
- [AI Customer Churn Predictor (Python)](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/ai-customer-churn-predictor-python/README.md)
- [Semantic Search for Support Tickets (Python)](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/semantic-search-python/README.md)

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

- [AI Inference Guide](https://developers.telnyx.com/docs/inference)
- [Chat Completions API Reference](https://developers.telnyx.com/api/inference/chat-completions)
- [Audio Transcriptions API Reference](https://developers.telnyx.com/api/inference/create-transcription)
- [Available Inference Models](https://developers.telnyx.com/docs/inference/models)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Telnyx Portal](https://portal.telnyx.com)

## Why Telnyx

Telnyx is an **AI Communications Infrastructure** platform — voice, messaging, SIP, AI, and IoT on one private, global network.
