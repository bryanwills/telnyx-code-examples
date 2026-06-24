---
name: ai-voice-agent-test-harness
title: "AI Voice Agent Test Harness"
description: "Test a Telnyx outbound AI voice agent against predictable mock IVR scenarios with menu prompts, hold simulation, representative pickup, and call-ending behavior."
language: python
framework: fastapi
telnyx_products: [Voice, AI Assistants, TeXML]
channel: [voice]
---

# AI Voice Agent Test Harness

Test a Telnyx outbound AI voice agent against predictable mock IVR scenarios before calling real businesses. This example gives you a repeatable target for validating IVR navigation, backend-owned DTMF, hold detection, representative pickup, and end-call behavior.

This example is useful for searches like "test Telnyx AI voice agent", "mock IVR for AI phone agent", and "Telnyx AI assistant regression test harness".

## Telnyx APIs and Features Used

- **Dial**: `POST /v2/calls` - [API reference](https://developers.telnyx.com/api-reference/call-commands/dial)
- **Start AI Assistant**: `POST /v2/calls/{call_control_id}/actions/ai_assistant_start` - [API reference](https://developers.telnyx.com/api-reference/call-commands/start-ai-assistant)
- **Send DTMF**: `POST /v2/calls/{call_control_id}/actions/send_dtmf` - [API reference](https://developers.telnyx.com/api-reference/call-commands/send-dtmf)
- **Hangup**: `POST /v2/calls/{call_control_id}/actions/hangup` - [API reference](https://developers.telnyx.com/api-reference/call-commands/hangup-call)
- **TeXML Gather**: `<Gather>` collects keypad input in the mock IVR - [docs](https://developers.telnyx.com/docs/voice/programmable-voice/texml-verbs/gather)

## Telnyx Webhook Events

- `call.answered` - start the assistant under test.
- `call.hangup` - mark the local test session ended.

## Architecture

```txt
┌──────────────────────────────┐
│ Developer / CI test           │
│ starts outbound test run      │
└──────────────┬───────────────┘
               │ POST /calls/outbound
               ▼
┌──────────────────────────────┐
│ FastAPI test harness          │
│ app.py                        │
│ - stores expected scenario    │
│ - serves mock IVR TeXML       │
│ - records assistant tools     │
│ - exposes test results        │
└───────┬──────────────────────┘
        │ POST /v2/calls
        ▼
      Telnyx API
        │
        │ outbound call to test number
        ▼
┌──────────────────────────────┐
│ Mock IVR target               │
│ /mock-ivr/{scenario}/start    │
│ - presents menu               │
│ - simulates hold              │
│ - simulates representative    │
└──────────────────────────────┘
        ▲
        │ POST /tools/send-dtmf
        │ POST /tools/end-call
        │ assistant tool callbacks
        ▼
┌──────────────────────────────┐
│ Telnyx AI Assistant under test│
│ IVR navigation + handoff      │
└──────────────────────────────┘
```

## What This Tests

- Whether the assistant chooses the expected IVR digit.
- Whether the backend receives and records the DTMF tool call.
- Whether the mock target emits hold phrases for hold detection.
- Whether the mock target emits representative pickup phrases.
- Whether the assistant calls the end-call tool when the scenario is complete.

## Scenarios

| Scenario | Expected Digit | Purpose |
| --- | --- | --- |
| `support_hold` | `1` | Menu navigation followed by queue/hold language and representative pickup. |
| `billing_fast_pickup` | `2` | Menu navigation followed by immediate representative pickup. |

## Environment Variables

| Variable | Required for real calls | Description |
| --- | --- | --- |
| `TELNYX_API_KEY` | yes | Telnyx API key used for Voice API requests. |
| `TELNYX_CONNECTION_ID` | yes | Voice API / Call Control connection ID. |
| `TELNYX_FROM_NUMBER` | yes | Telnyx caller ID number in E.164 format. |
| `TELNYX_IVR_ASSISTANT_ID` | yes | Assistant under test. |
| `PUBLIC_BASE_URL` | yes | Public HTTPS base URL for Telnyx webhooks, tools, and mock IVR TeXML. |
| `TELNYX_DRY_RUN` | no | Defaults to `true` for local testing. |
| `PORT` | no | Local server port. Defaults to `8000`. |

## Setup

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/ai-voice-agent-test-harness-python
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

Keep `python app.py` running in this terminal. Open a second terminal in the same folder to run the curl commands.

This example defaults to `TELNYX_DRY_RUN=true`, so local curl commands work before you connect real Telnyx numbers and assistants.

## Try It Locally

Start a dry-run test session:

```bash
curl -X POST http://127.0.0.1:8000/calls/outbound \
  -H "Content-Type: application/json" \
  -d '{"to":"+15551234567","scenario":"support_hold","objective":"reach support and ask for account status"}'
```

Inspect mock IVR TeXML:

```bash
curl http://127.0.0.1:8000/mock-ivr/support_hold/start
```

Simulate the assistant choosing the expected DTMF digit:

```bash
curl -X POST http://127.0.0.1:8000/tools/send-dtmf \
  -H "Content-Type: application/json" \
  -d '{"digits":"1","reason":"support menu option"}'
```

Read test results:

```bash
curl http://127.0.0.1:8000/test-results
```

## API Reference

See [`API.md`](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/ai-voice-agent-test-harness-python/API.md) for local endpoints exposed by this example.

## Use With Real Telnyx Calls

Set `TELNYX_DRY_RUN=false`, configure the Telnyx values in `.env`, expose the app with a public HTTPS URL, and point a Telnyx TeXML application or test number at:

```txt
https://YOUR_PUBLIC_BASE_URL/mock-ivr/support_hold/start
```

## Troubleshooting

| Issue | Cause | Fix |
| --- | --- | --- |
| `matched_expected` is `false` | Assistant selected the wrong IVR option | Update the assistant prompt or scenario expected digit. |
| Mock IVR returns 404 | Unknown scenario name | Call `GET /scenarios` and use one of the returned keys. |
| Real assistant cannot call tools | Tool URLs are not public | Expose the app with HTTPS and configure the assistant tool URLs. |
| Curl works but no real call is placed | Dry-run mode is enabled | Set `TELNYX_DRY_RUN=false`. |

## Resources

- [Telnyx Dial API](https://developers.telnyx.com/api-reference/call-commands/dial)
- [Telnyx Send DTMF API](https://developers.telnyx.com/api-reference/call-commands/send-dtmf)
- [TeXML Gather docs](https://developers.telnyx.com/docs/voice/programmable-voice/texml-verbs/gather)
- [Telnyx Voice API webhooks](https://developers.telnyx.com/docs/voice/programmable-voice/voice-api-webhooks)
- [Testing and traffic distribution for AI Assistants](https://developers.telnyx.com/docs/inference/ai-assistants/version-testing-traffic-distribution)

## Why Telnyx

Telnyx AI Communications Infrastructure lets you build repeatable AI voice-agent tests around real Voice API primitives: outbound calls, TeXML, DTMF, assistant tool calls, and call lifecycle webhooks.

## Related Examples

- [ai-ivr-dtmf-tool-python](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/ai-ivr-dtmf-tool-python/README.md) - expose a backend tool for assistant-driven DTMF.
- [outbound-ai-assistant-call-python](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/outbound-ai-assistant-call-python/README.md) - place a baseline outbound AI Assistant call.
- [hold-aware-ai-assistant-python](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/hold-aware-ai-assistant-python/README.md) - validate hold detection and representative pickup behavior.
