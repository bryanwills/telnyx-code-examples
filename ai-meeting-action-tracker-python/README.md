---
name: ai-meeting-action-tracker
title: "AI Meeting Action Tracker"
description: "Joins multi-party calls, identifies speakers, extracts action items with owners and deadlines, posts structured notes to Slack."
language: python
framework: flask
telnyx_products: [Voice, AI Inference, Conferencing]
integrations: [Slack]
channel: [voice]
---

# AI Meeting Action Tracker

Joins multi-party calls, identifies speakers, extracts action items with owners and deadlines, posts structured notes to Slack.

## Telnyx API Endpoints Used

- **Call Control: Answer**: `POST /v2/calls/{id}/actions/answer` -- [API reference](https://developers.telnyx.com/api/call-control/answer-call)
- **Call Control: Join Conference**: `POST /v2/calls/{id}/actions/join` -- [API reference](https://developers.telnyx.com/api/call-control/join-conference)
- **Call Control: Speak (TTS)**: `POST /v2/calls/{id}/actions/speak` -- [API reference](https://developers.telnyx.com/api/call-control/speak)
- **Call Control: Gather**: `POST /v2/calls/{id}/actions/gather_using_speak` -- [API reference](https://developers.telnyx.com/api/call-control/gather)
- **Create Call**: `POST /v2/calls` -- [API reference](https://developers.telnyx.com/api/call-control/create-call)
- **AI Inference**: `POST /v2/ai/chat/completions` -- [API reference](https://developers.telnyx.com/api/inference/chat-completions)

## Architecture

```text
Participant A --+
Participant B --+---> Telnyx Conference Bridge ---> Webhooks ---> Your App
Participant C --+           |                                       |
                       Media Stream                           AI Inference
                       (real-time audio)                      (analysis + response)
                                                                    |
                                                              TTS back into call
```

## Environment Variables

| Variable | Type | Example | Required | Description |
|----------|------|---------|----------|-------------|
| `TELNYX_API_KEY` | `string` | `KEY...` | **yes** | Telnyx API v2 key |
| `MAIN_NUMBER` | `string` | `+18005551234` | **yes** | Telnyx phone number |
| `CONNECTION_ID` | `string` | `1234567890` | **yes** | Call Control connection ID |
| `AI_MODEL` | `string` | `moonshotai/Kimi-K2.6` | no | Inference model |
| `SLACK_WEBHOOK` | `string` | `https://hooks.slack.com/...` | no | Slack webhook |

## Setup

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/ai-meeting-action-tracker-python
cp .env.example .env
pip install -r requirements.txt
python app.py
```

### Docker

```bash
docker build -t ai-meeting-action-tracker-python .
docker run --env-file .env -p 5000:5000 ai-meeting-action-tracker-python
```

## Resources

- [Call Control Conference Guide](https://developers.telnyx.com/docs/voice/call-control/conference)
- [Media Streaming Guide](https://developers.telnyx.com/docs/voice/media-streaming)
- [AI Inference](https://developers.telnyx.com/api/inference/chat-completions)
- [Telnyx Developer Docs](https://developers.telnyx.com)
