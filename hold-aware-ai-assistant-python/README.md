---
name: hold-aware-ai-assistant
title: "Hold-Aware AI Assistant"
description: "Stop a Telnyx AI Assistant during hold, monitor the call with transcription, and restart the assistant when a representative answers."
language: python
framework: fastapi
telnyx_products: [Voice, AI Assistants, Transcription]
channel: [voice]
---

# Hold-Aware AI Assistant

Build a hold-aware outbound Telnyx AI voice agent that pauses the active assistant during long hold periods, keeps the phone call connected, uses real-time transcription to detect representative pickup, and resumes the assistant with call context.

This example is intended for searches like "pause AI voice agent while on hold", "Telnyx hold detection AI assistant", and "resume voice AI assistant when representative answers".

## Telnyx API Endpoints Used

- **Dial**: `POST /v2/calls` - [API reference](https://developers.telnyx.com/api-reference/call-commands/dial)
- **Start AI Assistant**: `POST /v2/calls/{call_control_id}/actions/ai_assistant_start` - [API reference](https://developers.telnyx.com/api-reference/call-commands/start-ai-assistant)
- **Stop AI Assistant**: `POST /v2/calls/{call_control_id}/actions/ai_assistant_stop` - [API reference](https://developers.telnyx.com/api-reference/call-commands/stop-ai-assistant)
- **Transcription Start**: `POST /v2/calls/{call_control_id}/actions/transcription_start` - [API reference](https://developers.telnyx.com/api-reference/call-commands/transcription-start)
- **Transcription Stop**: `POST /v2/calls/{call_control_id}/actions/transcription_stop` - [API reference](https://developers.telnyx.com/api-reference/call-commands/transcription-stop)

## Webhook Events

- `call.answered`
- `call.hold`
- `call.unhold`
- `call.transcription`
- `call.hangup`

## Architecture

```txt
┌──────────────────────────────┐
│ Client / Operator            │
│ starts outbound call          │
└──────────────┬───────────────┘
               │ POST /calls/outbound
               ▼
┌──────────────────────────────┐
│ FastAPI app                   │
│ app.py                        │
│ - owns call state             │
│ - starts/stops assistants     │
│ - detects hold and pickup     │
└───────┬──────────────────────┘
        │ POST /v2/calls
        │ POST /calls/{id}/actions/ai_assistant_start
        ▼
      Telnyx API
        │
        │ call.answered, call.hold,
        │ call.unhold, call.transcription
        ▼
┌──────────────────────────────┐
│ Hold-aware orchestrator       │
│ 1. IVR assistant active       │
│ 2. stop assistant on hold     │
│ 3. transcription monitors     │
│ 4. representative detected    │
│ 5. representative assistant   │
└──────────────────────────────┘
```

## Environment Variables

| Variable | Required for real calls | Description |
| --- | --- | --- |
| `TELNYX_API_KEY` | yes | Telnyx API key used for Voice API requests. |
| `TELNYX_CONNECTION_ID` | yes | Voice API / Call Control connection ID. |
| `TELNYX_FROM_NUMBER` | yes | Telnyx caller ID number in E.164 format. |
| `TELNYX_IVR_ASSISTANT_ID` | yes | Assistant used before hold is detected. |
| `TELNYX_REPRESENTATIVE_ASSISTANT_ID` | yes | Assistant started after representative pickup. |
| `PUBLIC_BASE_URL` | yes | Public HTTPS base URL for Telnyx webhooks and assistant tools. |
| `TRANSCRIPTION_ENGINE` | no | Defaults to `Deepgram`. |
| `TRANSCRIPTION_MODEL` | no | Defaults to `nova-2`. |
| `TRANSCRIPTION_LANGUAGE` | no | Defaults to `en`. |
| `TELNYX_DRY_RUN` | no | Defaults to `true` for local testing. |
| `PORT` | no | Local server port. Defaults to `8000`. |

## Setup

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/hold-aware-ai-assistant-python
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

Keep `python app.py` running in this terminal. Open a second terminal in the same folder to run the curl commands.

This example defaults to `TELNYX_DRY_RUN=true`, so the curl command below works locally without making a real Telnyx API request. Set `TELNYX_DRY_RUN=false` only after your Telnyx values and webhook URL are configured.

## Try It

```bash
curl -X POST http://127.0.0.1:8000/calls/outbound \
  -H "Content-Type: application/json" \
  -d '{"to":"+15551234567","objective":"verify account status","target_company":"example company"}'
```

Test hold detection locally:

```bash
curl -X POST http://127.0.0.1:8000/tools/hold-detected \
  -H "Content-Type: application/json" \
  -d '{"reason":"please hold for the next available representative","confidence":0.9}'
```

Inspect local state:

```bash
curl http://127.0.0.1:8000/sessions
```

## API Reference

See [`API.md`](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/hold-aware-ai-assistant-python/API.md) for local endpoints exposed by this example.

## Going to Production

- Set `TELNYX_DRY_RUN=false`.
- Configure the IVR assistant tool URL as `https://YOUR_PUBLIC_BASE_URL/tools/hold-detected`.
- Tune the phrase detectors for your target industries and call-center scripts.
- Verify Telnyx webhook signatures before trusting call lifecycle and transcription events.
- Replace in-memory sessions with persistent storage.
- Review outbound calling, recording, transcription, and AI disclosure requirements.

## Troubleshooting

| Issue | Cause | Fix |
| --- | --- | --- |
| Hold tool returns no active session | No call was started | Call `POST /calls/outbound` first. |
| Representative assistant never starts | No `call.unhold` or pickup phrase was detected | Tune representative pickup phrases or trigger a test webhook. |
| Transcription does not start on real calls | Missing or unsupported transcription settings | Check `TRANSCRIPTION_ENGINE`, model, and Telnyx account capabilities. |
| Curl works but no real call is placed | Dry-run mode is enabled | Set `TELNYX_DRY_RUN=false`. |

## Resources

- [Telnyx Dial API](https://developers.telnyx.com/api-reference/call-commands/dial)
- [Start AI Assistant API](https://developers.telnyx.com/api-reference/call-commands/start-ai-assistant)
- [Transcription Start API](https://developers.telnyx.com/api-reference/call-commands/transcription-start)
- [Telnyx Voice API webhooks](https://developers.telnyx.com/docs/voice/programmable-voice/voice-api-webhooks)

## Why Telnyx

Telnyx AI Communications Infrastructure exposes call lifecycle webhooks, AI Assistants, and real-time transcription through the same Voice API, which makes it possible to pause expensive assistant interaction during long hold periods without dropping the call.

## Related Examples

- [outbound-ai-assistant-call-python](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/outbound-ai-assistant-call-python/README.md) - place an outbound call and start an AI Assistant after answer.
- [ai-assistant-context-handoff-python](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/ai-assistant-context-handoff-python/README.md) - switch between assistants while preserving call context.
- [ai-voice-agent-test-harness-python](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/ai-voice-agent-test-harness-python/README.md) - test hold and IVR behavior with mock scenarios.
