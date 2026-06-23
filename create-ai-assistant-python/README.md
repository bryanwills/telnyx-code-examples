---
name: create-ai-assistant
title: "Create AI Assistant"
description: "Create a new Telnyx AI Assistant with a system prompt, model selection, and tool configuration."
language: python
framework: flask
telnyx_products: [AI Assistants]
---

# Create AI Assistant

Create a new Telnyx AI Assistant with a system prompt, model selection, and tool configuration.

## Telnyx API Endpoints Used

- **Create AI Assistant**: `POST /v2/ai/assistants` -- [API reference](https://developers.telnyx.com/api/ai/create-assistant)

## Architecture

```
  API Request
        │
        ▼
  ┌──────────────────┐
  │ Your App          │
  └────────┬─────────┘
           │
           ▼
  ┌──────────────────┐
  │ Telnyx AI         │
  │ Assistants API    │
  └────────┬─────────┘
           │
           ▼
     JSON response
```

## Why Telnyx

Telnyx is an **AI Communications Infrastructure** platform - voice, messaging, SIP, AI, and IoT on one private, global network.

- **Managed AI agents** - Telnyx handles conversation state, tool calling, and telephony integration.

## Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Type | Example | Required | Description | Where to get it |
|----------|------|---------|----------|-------------|-----------------|
| `TELNYX_API_KEY` | `string` | `KEY0123456789ABCDEF` | **yes** | Telnyx API v2 key | [Portal](https://portal.telnyx.com/api-keys) |
| `FLASK_DEBUG` | `string` | `false` | no | Flask debug | - |

## Setup

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/create-ai-assistant-python
cp .env.example .env    # ← fill in your credentials
pip install -r requirements.txt
python app.py           # starts on http://localhost:5000
```

## API Reference

### `POST /ai/assistants`

HTTP endpoint to create AI assistant.

```bash
curl -X POST http://localhost:5000/ai/assistants \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Response:**

```json
{
  "id": "item-1750280400",
  "status": "created",
  "created_at": "2026-07-15T14:30:00Z"
}
```

## Troubleshooting

- **Connection refused on port 5000**: App isn't running. Run `python app.py` and check no other process uses port 5000.
- **401 Unauthorized**: Your `TELNYX_API_KEY` is invalid. Generate a new one at [portal.telnyx.com/api-keys](https://portal.telnyx.com/api-keys).
- **Assistant not found**: Verify `ASSISTANT_ID` at [portal.telnyx.com/ai/assistants](https://portal.telnyx.com/ai/assistants).

## Related Examples

- [ai-assistant-phone-setup-python](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/ai-assistant-phone-setup-python/README.md) - Phone setup

## Resources

- [AI Assistants Guide](https://developers.telnyx.com/docs/ai/assistants)

- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Telnyx Portal](https://portal.telnyx.com)
