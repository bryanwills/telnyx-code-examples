---
name: ai-podcast-producer
title: "AI Podcast Producer"
description: "Record a multi-host podcast via conference call, transcribe each speaker with STT, generate show notes + chapters + social clips via AI Inference, and produce TTS intro/outro bumpers."
language: python
framework: flask
telnyx_products: [Voice, AI Inference, Conferencing, Media Streaming, Call Recording]
integrations: [Slack]
channel: [voice, api]
---

# AI Podcast Producer

Record a multi-host podcast via conference call, transcribe each speaker with STT, generate show notes + chapters + social clips via AI Inference, and produce TTS intro/outro bumpers.

## Telnyx API Endpoints Used

- **Create Call**: `POST /v2/calls` -- [ref](https://developers.telnyx.com/api/call-control/create-call)
- **Gather (STT)**: `POST /v2/calls/{id}/actions/gather_using_speak` -- [ref](https://developers.telnyx.com/api/call-control/gather)
- **AI Inference**: `POST /v2/ai/chat/completions` -- [ref](https://developers.telnyx.com/api/inference/chat-completions)
- **TTS Generate**: `POST /v2/ai/generate` -- [ref](https://developers.telnyx.com/api/inference/generate)

## Telnyx Webhook Events

- `call.answered` -- Host joined conference
- `call.gather.ended` -- Speaker segment transcribed
- `conference.recording.saved` -- Recording URL available
- `call.hangup` -- Participant disconnected

## External Service Integrations

- **Slack** -- Team notifications via incoming webhooks

## Architecture

```
  Inbound Phone Call
        │
        ▼
  ┌──────────────────┐
  │ AI Inference      │ ── direction cues, rewrites
  └────────┬─────────┘
           │
           ▼
  ┌──────────────────┐
  │ TTS Generation    │ ── render audio
  │ (multiple takes/  │
  │  voices/languages)│
  └────────┬─────────┘
           │
           ├──► Voice response
           ├──► Slack alert
           └──► Download / stream
```

## Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Type | Example | Required | Description | Where to get it |
|----------|------|---------|----------|-------------|------------------|
| `TELNYX_API_KEY` | `string` | `KEY0123456789ABCDEF` | **yes** | Telnyx API v2 key | [Portal](https://portal.telnyx.com/api-keys) |
| `MAIN_NUMBER` | `string` | `+18005551234` | **yes** | Telnyx phone number (E.164) | [Portal](https://portal.telnyx.com/numbers/my-numbers) |
| `CONNECTION_ID` | `string` | `1494404757140276705` | **yes** | Call Control connection ID | [Portal](https://portal.telnyx.com/call-control/applications) |
| `AI_MODEL` | `string` | `moonshotai/Kimi-K2.6` | no | AI Inference model | [Docs](https://developers.telnyx.com/docs/inference/models) |
| `TTS_MODEL` | `string` | `telnyx/tts` | no | TTS model name | [Docs](https://developers.telnyx.com/docs/inference) |
| `TTS_VOICE` | `string` | `nova` | no | TTS voice | [Docs](https://developers.telnyx.com/docs/inference) |
| `SLACK_WEBHOOK` | `string` | `https://hooks.slack.com/...` | no | Slack webhook | [Docs](https://api.slack.com/messaging/webhooks) |

## Setup

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/ai-podcast-producer-python
cp .env.example .env
pip install -r requirements.txt
python app.py
```

### Webhook Configuration

```bash
ngrok http 5000
```

Set webhook URL in [Telnyx Portal](https://portal.telnyx.com):
- Call Control Application -> `https://<id>.ngrok.io/webhooks/voice`

## API Reference

### `POST /episodes/start`

```bash
curl -X POST http://localhost:5000/episodes/start \
  -H "Content-Type: application/json" \
  -d '{"hosts": ["+12125551234", "+13105559876"], "title": "AI Deep Dive"}'
```

**Response:**

```json
{"episode_id": "ep-a1b2c3d4", "title": "AI Deep Dive", "hosts_dialed": 2, "status": "dialing"}
```

### `GET /health`

```bash
curl http://localhost:5000/health
```

```json
{"status": "ok"}
```

## Webhook Endpoints

### `POST /webhooks/voice`

Handles Telnyx Call Control webhook events. Called automatically by Telnyx - do not call directly.

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Invalid or missing API key | Verify `TELNYX_API_KEY` in `.env` matches your key in the [Portal](https://portal.telnyx.com/api-keys) |
| Webhook not received | Local server not publicly reachable | Expose it with a tunnel (e.g. ngrok) and set the webhook URL in the [Telnyx Portal](https://portal.telnyx.com) |
| `422 Unprocessable Entity` | Missing or malformed request fields | Check the request body against the API Reference above |

## Related Examples

- [AI After Hours Emergency Triage (Python)](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/ai-after-hours-emergency-triage-python/README.md)
- [AI Assistant Knowledge Base (Python)](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/ai-assistant-knowledge-base-python/README.md)
- [AI Assistant Multi Tool (Python)](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/ai-assistant-multi-tool-python/README.md)
- [AI Assistant Phone Setup (Python)](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/ai-assistant-phone-setup-python/README.md)
- [AI Audiobook Narrator (Python)](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/ai-audiobook-narrator-python/README.md)

## Resources

- [AI Inference Guide](https://developers.telnyx.com/docs/inference)
- [Call Control Guide](https://developers.telnyx.com/docs/voice/call-control)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Telnyx Portal](https://portal.telnyx.com)

## Why Telnyx

Telnyx is an **AI Communications Infrastructure** platform - voice, messaging, SIP, AI, and IoT on one private, global network.
