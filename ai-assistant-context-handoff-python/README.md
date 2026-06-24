---
name: ai-assistant-context-handoff
title: "AI Assistant Context Handoff"
description: "Hand off a Telnyx voice call from an IVR navigation assistant to a representative-facing assistant with preserved context."
language: python
framework: fastapi
telnyx_products: [Voice, AI Assistants]
channel: [voice]
---

# AI Assistant Context Handoff

Use two Telnyx AI Assistants in one outbound phone call: one assistant handles IVR navigation, then your backend stops it and starts a representative-facing assistant with the original objective and approved context.

This example is useful when people search for how to hand off between Telnyx AI voice agents, how to preserve context between phone call stages, or how to split IVR navigation from live representative conversations.

## Telnyx API Endpoints Used

- **Dial**: `POST /v2/calls` - [API reference](https://developers.telnyx.com/api-reference/call-commands/dial)
- **Start AI Assistant**: `POST /v2/calls/{call_control_id}/actions/ai_assistant_start` - [API reference](https://developers.telnyx.com/api-reference/call-commands/start-ai-assistant)
- **Stop AI Assistant**: `POST /v2/calls/{call_control_id}/actions/ai_assistant_stop` - [API reference](https://developers.telnyx.com/api-reference/call-commands/stop-ai-assistant)

## Telnyx Webhook Events

- `call.answered` - start the IVR navigation assistant.
- `call.hangup` - mark the local session ended.

## Architecture

```txt
┌──────────────────────────────┐
│ Client / Operator            │
│ starts outbound task          │
└──────────────┬───────────────┘
               │ POST /calls/outbound
               ▼
┌──────────────────────────────┐
│ FastAPI app                   │
│ app.py                        │
│ - stores objective/context    │
│ - starts IVR assistant        │
│ - performs handoff            │
└───────┬──────────────────────┘
        │ POST /v2/calls
        │ POST /calls/{id}/actions/ai_assistant_start
        ▼
      Telnyx API
        ▲
        │ POST /tools/representative-detected
        │ handoff trigger
┌───────┴──────────────────────┐
│ Assistant handoff             │
│ stop IVR assistant            │
│ start representative assistant│
│ pass objective + context      │
└──────────────────────────────┘
```

## Environment Variables

| Variable | Required for real calls | Description |
| --- | --- | --- |
| `TELNYX_API_KEY` | yes | Telnyx API key used for Voice API requests. |
| `TELNYX_CONNECTION_ID` | yes | Voice API / Call Control connection ID. |
| `TELNYX_FROM_NUMBER` | yes | Telnyx caller ID number in E.164 format. |
| `TELNYX_IVR_ASSISTANT_ID` | yes | Assistant used during IVR/menu navigation. |
| `TELNYX_REPRESENTATIVE_ASSISTANT_ID` | yes | Assistant used after representative pickup. |
| `PUBLIC_BASE_URL` | yes | Public HTTPS base URL for Telnyx webhooks. |
| `TELNYX_DRY_RUN` | no | Defaults to `true` so local curl commands return mock Telnyx responses. |
| `PORT` | no | Local server port. Defaults to `8000`. |

## Setup

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/ai-assistant-context-handoff-python
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

Keep `python app.py` running in this terminal. Open a second terminal in the same folder to run the curl commands.

`TELNYX_DRY_RUN=true` is enabled by default so the local curl commands return mock Telnyx responses. Set `TELNYX_DRY_RUN=false` when you want to use real Telnyx calls.

## Try It

```bash
curl -X POST http://127.0.0.1:8000/calls/outbound \
  -H "Content-Type: application/json" \
  -d '{"to":"+15551234567","objective":"book a service appointment","context":{"customer_name":"Alex Morgan"}}'
```

Then simulate handoff:

```bash
curl -X POST http://127.0.0.1:8000/tools/representative-detected \
  -H "Content-Type: application/json" \
  -d '{"reason":"representative answered"}'
```

Inspect local state:

```bash
curl http://127.0.0.1:8000/sessions
```

## API Reference

See [`API.md`](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/ai-assistant-context-handoff-python/API.md) for local endpoints exposed by this example.

## Going to Production

- Set `TELNYX_DRY_RUN=false`.
- Expose the app over public HTTPS and set `PUBLIC_BASE_URL`.
- Configure your Telnyx Voice API application webhook URL to `https://YOUR_PUBLIC_BASE_URL/webhooks/telnyx`.
- Verify Telnyx webhook signatures before trusting webhook payloads.
- Keep only approved customer context in `client_state`.
- Replace in-memory sessions with persistent storage.

## Troubleshooting

| Issue | Cause | Fix |
| --- | --- | --- |
| Curl works but no real call is placed | `TELNYX_DRY_RUN=true` | Set `TELNYX_DRY_RUN=false` after configuring Telnyx values. |
| Real call fails with authentication error | Missing or invalid API key | Check `TELNYX_API_KEY` in `.env`. |
| Assistant does not start | Missing assistant ID or no `call.answered` webhook | Check assistant IDs and webhook URL. |
| Handoff has no active call | No dry-run or real session exists | Call `POST /calls/outbound` before `/tools/representative-detected`. |

## Resources

- [Telnyx Dial API](https://developers.telnyx.com/api-reference/call-commands/dial)
- [Start AI Assistant API](https://developers.telnyx.com/api-reference/call-commands/start-ai-assistant)
- [Telnyx Voice API webhooks](https://developers.telnyx.com/docs/voice/programmable-voice/voice-api-webhooks)
- [Telnyx AI Assistant agent handoff guide](https://developers.telnyx.com/docs/inference/ai-assistants/agent-handoff)

## Why Telnyx

Telnyx AI Communications Infrastructure combines programmable voice, call-control webhooks, AI Assistants, and outbound calling in one platform, so your application can control the full phone-call lifecycle without stitching together multiple vendors.

## Related Examples

- [outbound-ai-assistant-call-python](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/outbound-ai-assistant-call-python/README.md) - start with the simplest outbound AI Assistant call flow.
- [hold-aware-ai-assistant-python](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/hold-aware-ai-assistant-python/README.md) - pause and resume assistants around hold time.
- [ai-ivr-dtmf-tool-python](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/ai-ivr-dtmf-tool-python/README.md) - let an assistant request backend-owned DTMF actions.
