---
name: ai-ivr-dtmf-tool
title: "AI IVR DTMF Tool"
description: "Use a Telnyx AI Assistant custom tool to navigate IVR menus while your backend sends DTMF with Call Control."
language: python
framework: fastapi
telnyx_products: [Voice, AI Assistants]
channel: [voice]
---

# AI IVR DTMF Tool

Let a Telnyx AI Assistant listen to an IVR menu and request keypad input through a backend tool. The backend owns the actual `send_dtmf` Call Control command, making menu navigation constrained and auditable.

This example is optimized for searches like "Telnyx AI assistant send DTMF", "AI voice agent navigate IVR", and "backend-owned DTMF tool for phone agents".

## Telnyx API Endpoints Used

- **Dial**: `POST /v2/calls` - [API reference](https://developers.telnyx.com/api-reference/call-commands/dial)
- **Start AI Assistant**: `POST /v2/calls/{call_control_id}/actions/ai_assistant_start` - [API reference](https://developers.telnyx.com/api-reference/call-commands/start-ai-assistant)
- **Send DTMF**: `POST /v2/calls/{call_control_id}/actions/send_dtmf` - [API reference](https://developers.telnyx.com/api-reference/call-commands/send-dtmf)
- **Playback Start**: `POST /v2/calls/{call_control_id}/actions/playback_start` - [API reference](https://developers.telnyx.com/api-reference/call-commands/play-audio-url) - optional demo feedback tone.

## Telnyx Webhook Events

- `call.answered` - start the IVR navigation assistant.
- `call.hangup` - mark the local session ended.

## Architecture

```txt
┌──────────────────────────────┐
│ Client / Workflow             │
│ starts outbound IVR call      │
└──────────────┬───────────────┘
               │ POST /calls/outbound
               ▼
┌──────────────────────────────┐
│ FastAPI app                   │
│ app.py                        │
│ - dials target number         │
│ - starts IVR assistant        │
│ - exposes send_dtmf tool      │
└───────┬──────────────────────┘
        │ POST /v2/calls
        │ POST /calls/{id}/actions/ai_assistant_start
        ▼
      Telnyx API
        ▲
        │ POST /tools/send-dtmf
        │ assistant requests digit
┌───────┴──────────────────────┐
│ Telnyx AI Assistant           │
│ listens to IVR menu           │
└──────────────────────────────┘
        │
        │ backend sends:
        │ POST /calls/{id}/actions/send_dtmf
        ▼
      Phone IVR
```

## Assistant Tool

Configure a Telnyx AI Assistant tool named `send_dtmf` that posts to:

```txt
https://YOUR_PUBLIC_BASE_URL/tools/send-dtmf
```

Tool parameters:

```json
{
  "type": "object",
  "properties": {
    "call_control_id": {"type": "string"},
    "digits": {"type": "string"},
    "reason": {"type": "string"}
  },
  "required": ["digits"]
}
```

## Environment Variables

| Variable | Required for real calls | Description |
| --- | --- | --- |
| `TELNYX_API_KEY` | yes | Telnyx API key used for Voice API requests. |
| `TELNYX_CONNECTION_ID` | yes | Voice API / Call Control connection ID. |
| `TELNYX_FROM_NUMBER` | yes | Telnyx caller ID number in E.164 format. |
| `TELNYX_IVR_ASSISTANT_ID` | yes | Assistant that listens to IVR prompts and calls `/tools/send-dtmf`. |
| `PUBLIC_BASE_URL` | yes | Public HTTPS base URL for webhooks, assistant tools, and demo DTMF audio. |
| `TELNYX_DRY_RUN` | no | Defaults to `true` for local testing without Telnyx credentials. |
| `PORT` | no | Local server port. Defaults to `8000`. |

## Setup

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/ai-ivr-dtmf-tool-python
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

Keep `python app.py` running in this terminal. Open a second terminal in the same folder to run the curl commands.

`TELNYX_DRY_RUN=true` is set in `.env.example`, so the local curl commands return mock Telnyx responses until you are ready to place real calls.

## Try It

```bash
curl -X POST http://127.0.0.1:8000/calls/outbound \
  -H "Content-Type: application/json" \
  -d '{"to":"+15551234567","objective":"reach the support department"}'
```

Test the assistant tool locally:

```bash
curl -X POST http://127.0.0.1:8000/tools/send-dtmf \
  -H "Content-Type: application/json" \
  -d '{"digits":"1","reason":"support menu option"}'
```

## API Reference

See [`API.md`](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/ai-ivr-dtmf-tool-python/API.md) for local endpoints exposed by this example.

## Going to Production

- Set `TELNYX_DRY_RUN=false`.
- Configure the assistant tool URL as `https://YOUR_PUBLIC_BASE_URL/tools/send-dtmf`.
- Validate requested digits and restrict allowed options for your IVR use case.
- Verify Telnyx webhook signatures before trusting call lifecycle events.
- Store DTMF tool calls for auditability.

## Troubleshooting

| Issue | Cause | Fix |
| --- | --- | --- |
| Tool returns `no active call_control_id` | No session exists | Start a call first with `POST /calls/outbound`. |
| Real call does not receive DTMF | Assistant tool URL is wrong or not public | Use an HTTPS tunnel and configure the exact `/tools/send-dtmf` URL. |
| Telnyx API rejects DTMF | Invalid digit string | Use valid DTMF characters supported by Telnyx: `0-9`, `A-D`, `*`, `#`, `w`, `W`. |
| Curl works but no real call is placed | Dry-run mode is enabled | Set `TELNYX_DRY_RUN=false`. |

## Resources

- [Telnyx Dial API](https://developers.telnyx.com/api-reference/call-commands/dial)
- [Telnyx Send DTMF API](https://developers.telnyx.com/api-reference/call-commands/send-dtmf)
- [Start AI Assistant API](https://developers.telnyx.com/api-reference/call-commands/start-ai-assistant)
- [Telnyx Voice API webhooks](https://developers.telnyx.com/docs/voice/programmable-voice/voice-api-webhooks)

## Why Telnyx

Telnyx AI Communications Infrastructure lets an application send DTMF and control live calls through Call Control webhooks, while Telnyx AI Assistants provide the speech interface for deciding which menu option to choose.

## Related Examples

- [outbound-ai-assistant-call-python](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/outbound-ai-assistant-call-python/README.md) - place an outbound call and start an AI Assistant after answer.
- [ai-assistant-context-handoff-python](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/ai-assistant-context-handoff-python/README.md) - hand off from IVR navigation to a representative-facing assistant.
- [ai-voice-agent-test-harness-python](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/ai-voice-agent-test-harness-python/README.md) - test DTMF and IVR behavior against mock scenarios.
