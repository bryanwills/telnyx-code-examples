---
name: outbound-ai-assistant-call
title: "Outbound AI Assistant Call"
description: "Place an outbound call with Telnyx Call Control and start a Telnyx AI Assistant when the call is answered."
language: python
framework: fastapi
telnyx_products: [Voice, AI Assistants]
channel: [voice]
---

# Outbound AI Assistant Call

Place an outbound phone call with Telnyx Call Control, receive call lifecycle webhooks, and start a Telnyx AI Assistant when the call is answered.

This is the smallest useful starting point for searches like "make an outbound AI phone call with Telnyx", "start a Telnyx AI Assistant on an outbound call", and "Telnyx Call Control AI assistant Python".

## Telnyx API Endpoints Used

- **Dial**: `POST /v2/calls` - [API reference](https://developers.telnyx.com/api-reference/call-commands/dial)
- **Start AI Assistant**: `POST /v2/calls/{call_control_id}/actions/ai_assistant_start` - [API reference](https://developers.telnyx.com/api-reference/call-commands/start-ai-assistant)

## Telnyx Webhook Events

- `call.answered` - start the configured AI Assistant.
- `call.hangup` - clean up local call state.

## Architecture

```txt
┌──────────────────────────────┐
│ Client / Operator            │
│ curl, CRM, workflow system    │
└──────────────┬───────────────┘
               │ POST /calls/outbound
               ▼
┌──────────────────────────────┐
│ FastAPI app                   │
│ app.py                        │
│ - creates outbound call       │
│ - tracks in-memory session    │
│ - starts AI Assistant         │
└───────┬──────────────────────┘
        │ POST /v2/calls
        │ POST /calls/{id}/actions/ai_assistant_start
        ▼
      Telnyx API
        │
        │ POST /webhooks/telnyx
        │ call.answered, call.hangup
        ▼
┌──────────────────────────────┐
│ FastAPI webhook handler       │
│ updates session state         │
└──────────────────────────────┘
```

## Environment Variables

| Variable | Required for real calls | Description |
| --- | --- | --- |
| `TELNYX_API_KEY` | yes | Telnyx API key. |
| `TELNYX_CONNECTION_ID` | yes | Voice API / Call Control connection ID. |
| `TELNYX_FROM_NUMBER` | yes | Outbound caller ID number in E.164 format. |
| `TELNYX_ASSISTANT_ID` | yes | Telnyx AI Assistant ID to start after answer. |
| `PUBLIC_BASE_URL` | yes | Public HTTPS base URL for webhooks. |
| `TELNYX_DRY_RUN` | no | Defaults to `true`; returns mock Telnyx responses for local curl testing. |
| `PORT` | no | Local server port. Defaults to `8000`. |

## Setup

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/outbound-ai-assistant-call-python
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

Keep `python app.py` running in this terminal. Open a second terminal in the same folder to run the curl commands.

By default this runs in dry-run mode. The curl request below works locally without Telnyx credentials. To place a real call, fill in `.env` and set:

```bash
TELNYX_DRY_RUN=false
```

Expose the local server:

```bash
ngrok http 8000
```

Set `PUBLIC_BASE_URL` to the ngrok HTTPS URL.

## Try It

```bash
curl -X POST http://127.0.0.1:8000/calls/outbound \
  -H "Content-Type: application/json" \
  -d '{"to":"+15551234567"}'
```

Inspect local state:

```bash
curl http://127.0.0.1:8000/sessions
```

## API Reference

See [`API.md`](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/outbound-ai-assistant-call-python/API.md) for local endpoints exposed by this example.

## Going to Production

- Set `TELNYX_DRY_RUN=false`.
- Configure a Telnyx Voice API application and set the webhook URL to `https://YOUR_PUBLIC_BASE_URL/webhooks/telnyx`.
- Use a Telnyx number as `TELNYX_FROM_NUMBER`.
- Confirm outbound voice permissions for the destination country.
- Verify Telnyx webhook signatures before trusting events.
- Replace in-memory sessions with persistent storage.

## Troubleshooting

| Issue | Cause | Fix |
| --- | --- | --- |
| Curl works but no real call is placed | `TELNYX_DRY_RUN=true` | Set `TELNYX_DRY_RUN=false` after configuring `.env`. |
| Telnyx returns authentication error | Invalid API key | Check `TELNYX_API_KEY`. |
| No `call.answered` webhook arrives | Webhook URL is not public or not configured | Use ngrok and set the Voice API application webhook URL. |
| Assistant does not start | Missing assistant ID | Check `TELNYX_ASSISTANT_ID`. |

## Resources

- [Telnyx Dial API](https://developers.telnyx.com/api-reference/call-commands/dial)
- [Start AI Assistant API](https://developers.telnyx.com/api-reference/call-commands/start-ai-assistant)
- [Telnyx Voice API webhooks](https://developers.telnyx.com/docs/voice/programmable-voice/voice-api-webhooks)
- [Voice Assistant Quickstart](https://developers.telnyx.com/docs/inference/ai-assistants/no-code-voice-assistant)

## Why Telnyx

Telnyx AI Communications Infrastructure provides programmable voice, Call Control webhooks, and AI Assistants on one communications platform, so your app can place calls and control the assistant lifecycle from one API.

## Related Examples

- [ai-ivr-dtmf-tool-python](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/ai-ivr-dtmf-tool-python/README.md) - let an assistant request backend-owned DTMF actions.
- [hold-aware-ai-assistant-python](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/hold-aware-ai-assistant-python/README.md) - pause and resume an assistant around hold time.
- [ai-assistant-context-handoff-python](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/ai-assistant-context-handoff-python/README.md) - hand off between assistants with preserved context.
