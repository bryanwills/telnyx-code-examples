---
name: ai-receptionist-with-booking-tools
title: "AI Receptionist with Booking Tools"
description: "AI Receptionist with Booking Tools - AI Assistant with tool_use for real calendar booking actions."
language: python
framework: flask
telnyx_products: [AI Inference]
---

# AI Receptionist with Booking Tools

AI Receptionist with Booking Tools - AI Assistant with tool_use for real calendar booking actions.

## Telnyx API Endpoints Used

- **AI Inference**: `POST /v2/ai/chat/completions` - [API reference](https://developers.telnyx.com/api/inference/chat-completions)

## Architecture

```
  API Request
        │
        ▼
  ┌──────────────────┐
  │ Your App          │
  └────────┬─────────┘
           │
           ├──► Telnyx AI Inference
           │
           ├──► Appointment scheduling
           │
           ▼
     JSON response
```

## Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Type | Example | Required | Description | Where to get it |
|----------|------|---------|----------|-------------|-----------------|
| `TELNYX_API_KEY` | `string` | `KEY0123456789ABCDEF` | **yes** | Telnyx API v2 key | [Portal](https://portal.telnyx.com/api-keys) |
| `ASSISTANT_ID` | `string` | `asst_abc123` | no | Telnyx AI Assistant ID | [Portal](https://portal.telnyx.com/ai/assistants) |
| `AI_MODEL` | `string` | `moonshotai/Kimi-K2.6` | no | Telnyx AI Inference model name | [Portal](https://developers.telnyx.com/docs/inference/models) |
| `PORT` | `integer` | `5000` | no | HTTP server port | - |

## Setup

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/ai-receptionist-with-booking-tools-python
cp .env.example .env    # ← fill in your credentials
pip install -r requirements.txt
python app.py           # starts on http://localhost:5000
```

## API Reference

### `POST /chat`

Triggers chat

```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "How do I set up a voice AI agent with Telnyx?"
  }'
```

**Response:**

```json
{
  "response": "Based on the Telnyx API documentation, you can implement programmable voice using Call Control...",
  "model": "moonshotai/Kimi-K2.6",
  "tokens_used": 284
}
```

### `GET /bookings`

Returns bookings

```bash
curl http://localhost:5000/bookings
```

**Response:**

```json
{
  "appointments": [
    {
      "id": "appt-7821",
      "date": "2026-07-18",
      "time": "14:30",
      "provider": "Dr. Smith",
      "patient_phone": "+1212555****",
      "status": "confirmed"
    }
  ]
}
```

### `GET /health`

Returns health

```bash
curl http://localhost:5000/health
```

**Response:**

```json
{
  "status": "ok",
  "uptime_seconds": 3842,
  "active_sessions": 2,
  "version": "1.0.0"
}
```

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
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Telnyx Portal](https://portal.telnyx.com)

## Why Telnyx

Telnyx is an **AI Communications Infrastructure** platform - voice, messaging, SIP, AI, and IoT on one private, global network.
