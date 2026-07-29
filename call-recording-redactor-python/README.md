---
name: call-recording-redactor
title: "AI Call Recording Redactor"
description: "AI Call Recording Redactor — transcribe call audio and redact PII (names, cards, SSNs, addresses, phones, emails) via Telnyx STT + AI Inference."
language: python
framework: flask
telnyx_products: [AI Inference]
---

# AI Call Recording Redactor

AI Call Recording Redactor — transcribe call audio and redact PII (names, credit cards, SSNs, addresses, phone numbers, emails) via Telnyx STT + AI Inference. Supports both direct transcript redaction and audio file upload.

## Telnyx API Endpoints Used

- **AI Audio Transcriptions**: `POST /v2/ai/audio/transcriptions` — [API reference](https://developers.telnyx.com/api/inference/create-transcription)
- **AI Inference**: `POST /v2/ai/chat/completions` — [API reference](https://developers.telnyx.com/api/inference/chat-completions)

## Architecture

```
  Audio file or transcript
        │
        ▼
  ┌──────────────────────────┐
  │ Your App                 │
  └────────┬─────────────────┘
           │
           ├──► Telnyx STT (audio → text)
           │
           ├──► Telnyx AI Inference (PII detection + redaction)
           │
           ▼
     Redacted transcript + redaction map (JSON)
```

## Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Type | Example | Required | Description | Where to get it |
|----------|------|---------|----------|-------------|-----------------|
| `TELNYX_API_KEY` | `string` | `KEY0123456789ABCDEF` | **yes** | Telnyx API v2 key | [Portal](https://portal.telnyx.com/api-keys) |
| `AI_MODEL` | `string` | `moonshotai/Kimi-K2.6` | no | Telnyx AI Inference model name | [Portal](https://developers.telnyx.com/docs/inference/models) |
| `PORT` | `integer` | `5000` | no | HTTP server port | — |

## Setup

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/call-recording-redactor-python
cp .env.example .env    # ← fill in your credentials
pip install -r requirements.txt
python app.py           # starts on http://localhost:5000
```

## API Reference

### `POST /redact`

Redact PII from a text transcript directly (no audio needed).

```bash
curl -X POST http://localhost:5000/redact \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "Hi, this is John Smith calling. My card number is 4532-1234-5678-9012 and my SSN is 123-45-6789."
  }'
```

**Response:**

```json
{
  "id": "red-1750280400",
  "original_transcript": "Hi, this is John Smith calling...",
  "redacted_transcript": "Hi, this is [NAME] calling. My card number is [CREDIT_CARD] and my SSN is [SSN].",
  "redactions": [
    {"type": "name", "original": "John Smith", "redacted": "[NAME]", "count": 1},
    {"type": "credit_card", "original": "4532-1234-5678-9012", "redacted": "[CREDIT_CARD]", "count": 1},
    {"type": "ssn", "original": "123-45-6789", "redacted": "[SSN]", "count": 1}
  ],
  "items_redacted": 3,
  "pii_types_found": ["name", "credit_card", "ssn"],
  "source": "text",
  "status": "done",
  "generated_at": "2026-07-29T11:21:15Z"
}
```

### `POST /redact/audio`

Upload an audio file → transcribe via STT → redact PII.

```bash
curl -X POST http://localhost:5000/redact/audio \
  -F "file=@recording.wav"
```

**Response:**

```json
{
  "id": "red-1750280401",
  "original_transcript": "Hello, this is Sarah Johnson from Acme Corp...",
  "redacted_transcript": "Hello, this is [NAME] from [ORGANIZATION]...",
  "redactions": [...],
  "items_redacted": 2,
  "source": "audio:recording.wav",
  "status": "done",
  "generated_at": "2026-07-29T11:24:18Z"
}
```

### `GET /redactions`

List recent redaction jobs.

```bash
curl http://localhost:5000/redactions
```

### `GET /redactions/<id>`

Fetch a specific redaction result.

```bash
curl http://localhost:5000/redactions/red-1750280400
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
  "redactions": 0,
  "version": "1.0.0"
}
```

## PII Types Redacted

| Type | Placeholder | Example |
|------|-------------|---------|
| Name | `[NAME]` | John Smith |
| Credit card | `[CREDIT_CARD]` | 4532-1234-5678-9012 |
| SSN | `[SSN]` | 123-45-6789 |
| Phone | `[PHONE]` | 555-867-5309 |
| Email | `[EMAIL]` | john.smith@email.com |
| Address | `[ADDRESS]` | 123 Main St, Springfield IL |
| Date of birth | `[DOB]` | 01/15/1990 |
| Account number | `[ACCOUNT_NUMBER]` | ACCT-12345 |

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Invalid or missing API key | Verify `TELNYX_API_KEY` in `.env` matches your key in the [Portal](https://portal.telnyx.com/api-keys) |
| `400 Bad Request` on audio | Wrong audio format or model | Use WAV format; `distil-whisper/distil-large-v2` supports most common formats |
| Slow response | Reasoning model needs more tokens | STT + inference can take 60-90s; be patient |
| `raw` returned instead of JSON | Model didn't return parseable JSON | Retry with shorter transcript or pin a stronger model |
| Empty transcript | Audio too short or silent | Use a longer audio clip with clear speech |

## Related Examples

- [AI Quiz Generator (Python)](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/quiz-generator-python/README.md)
- [AI Changelog Generator (Python)](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/changelog-generator-python/README.md)
- [AI Error Explainer (Python)](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/error-explainer-python/README.md)
- [AI Customer Churn Predictor (Python)](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/ai-customer-churn-predictor-python/README.md)

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
