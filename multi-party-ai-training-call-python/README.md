---
name: multi-party-ai-training-call
title: "Multi-Party AI Training Call"
description: "AI plays customer roles for sales/support practice. Multiple trainees join, AI rotates scenarios and scores each trainee."
language: python
framework: flask
telnyx_products: [Voice, AI Inference, Conferencing]
integrations: [Slack]
channel: [voice]
---

# Multi-Party AI Training Call

AI plays customer roles for sales/support practice. Multiple trainees join, AI rotates scenarios and scores each trainee.

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
cd telnyx-code-examples/multi-party-ai-training-call-python
cp .env.example .env
pip install -r requirements.txt
python app.py
```

### Docker

```bash
docker build -t multi-party-ai-training-call-python .
docker run --env-file .env -p 5000:5000 multi-party-ai-training-call-python
```

## Resources

- [Call Control Conference Guide](https://developers.telnyx.com/docs/voice/call-control/conference)
- [Media Streaming Guide](https://developers.telnyx.com/docs/voice/media-streaming)
- [AI Inference](https://developers.telnyx.com/api/inference/chat-completions)
- [Telnyx Developer Docs](https://developers.telnyx.com)
