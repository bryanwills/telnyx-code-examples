---
name: merge-recruitment-hotline
title: "Merge Recruitment Hotline"
description: "Job seekers call."
language: python
framework: flask
telnyx_products: [Voice, AI Inference, Messaging]
integrations: [Merge ATS]
channel: [voice, sms]
---

# Merge Recruitment Hotline

> Also known as: recruitment phone line, job application by phone, ATS voice interface.

Job seekers call. AI asks what role they want, searches open positions in ATS via Merge, describes top matches conversationally, and submits applications on their behalf with SMS confirmation.

## Telnyx API Endpoints Used

- **Call Control: Answer**: `POST /v2/calls/{id}/actions/answer` -- [API reference](https://developers.telnyx.com/api/call-control/answer-call)
- **Call Control: Gather Using Speak**: `POST /v2/calls/{id}/actions/gather_using_speak` -- [API reference](https://developers.telnyx.com/api/call-control/gather-using-speak)
- **Call Control: Speak (TTS)**: `POST /v2/calls/{id}/actions/speak` -- [API reference](https://developers.telnyx.com/api/call-control/speak)
- **Call Control: Hangup**: `POST /v2/calls/{id}/actions/hangup` -- [API reference](https://developers.telnyx.com/api/call-control/hangup)
- **AI Inference**: `POST /v2/ai/chat/completions` -- [API reference](https://developers.telnyx.com/api/inference/chat-completions)
- **Send Message (SMS)**: `POST /v2/messages` -- [API reference](https://developers.telnyx.com/api/messaging/send-message)

## Telnyx Webhook Events

This app handles these webhook events ([Call Control docs](https://developers.telnyx.com/docs/api/v2/call-control)):

- `call.initiated` -- New inbound or outbound call detected
- `call.answered` -- Call connected, app begins interaction with greeting
- `call.gather.ended` -- Caller input received (speech or DTMF), app processes response
- `call.speak.ended` -- TTS playback finished, transitions to next action
- `call.hangup` -- Call ended, cleans up session state and logs outcome

## Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Type | Example | Required | Description | Where to get it |
|----------|------|---------|----------|-------------|-----------------|
| `TELNYX_API_KEY` | `string` | `KEY0123456789` | **yes** | Telnyx API v2 key | [Portal](https://portal.telnyx.com/api-keys) |
| `TELNYX_PHONE_NUMBER` | `string` | `+18005551234` | **yes** | Telnyx phone number | [Portal](https://portal.telnyx.com/numbers/my-numbers) |
| `TELNYX_CONNECTION_ID` | `string` | `149440475714` | **yes** | Call Control app ID | [Portal](https://portal.telnyx.com/call-control/applications) |
| `MERGE_API_KEY` | `string` | `your-key` | **yes** | Merge.dev API key | [Merge](https://app.merge.dev/keys) |
| `MERGE_ACCOUNT_TOKEN` | `string` | `your-token` | **yes** | Merge linked account token | [Merge](https://app.merge.dev) |
| `AI_MODEL` | `string` | `moonshotai/Kimi-K2.6` | no | AI model | [Models](https://developers.telnyx.com/docs/inference/models) |
| `PORT` | `integer` | `5000` | no | Server port | -- |

## Setup

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/merge-recruitment-hotline-python
cp .env.example .env
pip install -r requirements.txt
python app.py
```

### Webhook Configuration

1. Expose your local server: `ngrok http 5000`
2. Configure in [Telnyx Portal](https://portal.telnyx.com/call-control/applications):
   - Call Control Application -> Webhook URL -> `https://<id>.ngrok.io/webhooks/voice`

## API Reference

### `GET /jobs`

Jobs.

```bash
curl http://localhost:5000/jobs
```

**Response:**

```json
{"status": "ok", "service": "merge-recruitment-hotline"}
```

### `GET /applications`

Applications.

```bash
curl http://localhost:5000/applications
```

**Response:**

```json
{"status": "ok", "service": "merge-recruitment-hotline"}
```

### `GET /health`

Health.

```bash
curl http://localhost:5000/health
```

**Response:**

```json
{"status": "ok", "service": "merge-recruitment-hotline"}
```


## Webhook Endpoints

### `POST /webhooks/voice`

Telnyx sends call events here. Your app processes them and responds with the next action.

**Events handled:**

- `call.initiated` -- New inbound or outbound call detected
- `call.answered` -- Call connected, app begins interaction with greeting
- `call.gather.ended` -- Caller input received (speech or DTMF), app processes response
- `call.speak.ended` -- TTS playback finished, transitions to next action
- `call.hangup` -- Call ended, cleans up session state and logs outcome

**Example payload:**

```json
{
  "data": {
    "event_type": "call.initiated",
    "id": "evt_123",
    "payload": {
      "call_control_id": "v3:abc123",
      "direction": "incoming",
      "from": "+12125551234",
      "to": "+18005559876"
    }
  }
}
```

## All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/webhooks/voice` | Voice |
| `GET` | `/jobs` | Jobs |
| `GET` | `/applications` | Applications |
| `GET` | `/health` | Health |

## Resources

- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Call Control quickstart](https://developers.telnyx.com/docs/voice/call-control)
- [AI Inference docs](https://developers.telnyx.com/docs/inference)
- [Merge.dev API docs](https://docs.merge.dev)
- [Telnyx Portal](https://portal.telnyx.com)
