---
name: chat-with-ai-assistant
title: "Chat with AI Assistant"
description: "Send messages to a Telnyx AI Assistant and receive responses. Supports conversation history and streaming."
language: python
framework: flask
telnyx_products: [AI Assistants, AI Inference]
---

# Chat with AI Assistant

Send messages to a Telnyx AI Assistant and receive responses. Supports conversation history and streaming.

## Telnyx API Endpoints Used

- **AI Chat Completions**: `POST /v2/ai/chat/completions` -- [API reference](https://developers.telnyx.com/api/inference/chat-completions)
- **AI Assistant Chat**: `POST /v2/ai/assistants/{id}/messages` -- [API reference](https://developers.telnyx.com/api/ai/create-assistant-message)

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
     SMS notification
```

## Why Telnyx

Telnyx is an **AI Communications Infrastructure** platform — voice, messaging, SIP, AI, and IoT on one private, global network.

- **Managed AI agents** — Telnyx handles conversation state, tool calling, and telephony integration.
- **Co-located inference** — LLM runs on the same network as voice traffic. Sub-200ms round trips.

## Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Type | Example | Required | Description | Where to get it |
|----------|------|---------|----------|-------------|-----------------|
| `TELNYX_API_KEY` | `string` | `KEY0123456789ABCDEF` | **yes** | Telnyx API v2 key | [Portal](https://portal.telnyx.com/api-keys) |
| `AI_ASSISTANT_ID` | `string` | `your_value` | **yes** | Ai assistant id | — |
| `FLASK_DEBUG` | `string` | `false` | no | Flask debug | — |

## Setup

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/chat-with-ai-assistant-python
cp .env.example .env    # ← fill in your credentials
pip install -r requirements.txt
python app.py           # starts on http://localhost:5000
```

## API Reference

### `POST /chat`

HTTP endpoint to chat with an AI Assistant.

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

## Testing

```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What can you help me with?"}'''''' 
```

```json
{"response": "I can help you with...", "status": "ok"}
```

## Troubleshooting

- **Connection refused on port 5000**: App isn't running. Run `python app.py` and check no other process uses port 5000.
- **401 Unauthorized**: Your `TELNYX_API_KEY` is invalid. Generate a new one at [portal.telnyx.com/api-keys](https://portal.telnyx.com/api-keys).
- **AI response slow/empty**: Verify model name. See available models at [developers.telnyx.com](https://developers.telnyx.com/docs/inference/list-models).
- **Assistant not found**: Verify `ASSISTANT_ID` at [portal.telnyx.com/ai/assistants](https://portal.telnyx.com/ai/assistants).

## Related Examples

- [create-ai-assistant-python](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/create-ai-assistant-python/README.md) - Create assistant
- [ai-assistant-phone-setup-python](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/ai-assistant-phone-setup-python/README.md) - Phone setup
- [run-llm-inference-python](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/run-llm-inference-python/README.md) - Standalone inference

## Resources

- [AI Assistants Guide](https://developers.telnyx.com/docs/ai/assistants)

- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Telnyx Portal](https://portal.telnyx.com)
