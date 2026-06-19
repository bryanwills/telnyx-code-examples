---
name: merge-employee-onboarding
title: "Merge Employee Onboarding"
description: "New employee webhook from Merge HRIS triggers full provisioning: Telnyx phone number, AI voicemail greeting, welcome SMS with IT setup instructions, and IT ticket via Merge Ticketing."
language: python
framework: flask
telnyx_products: [Voice, AI Inference, Messaging, Numbers]
integrations: [Merge HRIS, Merge Ticketing]
channel: [voice, sms]
---

# Merge Employee Onboarding

> Also known as: employee onboarding, new hire automation, HR provisioning, onboarding workflow.

New employee webhook from Merge HRIS triggers full provisioning: Telnyx phone number, AI voicemail greeting, welcome SMS with IT setup instructions, and IT ticket via Merge Ticketing.

## Telnyx API Endpoints Used

- **AI Inference**: `POST /v2/ai/chat/completions` -- [API reference](https://developers.telnyx.com/api/inference/chat-completions)
- **Send Message (SMS)**: `POST /v2/messages` -- [API reference](https://developers.telnyx.com/api/messaging/send-message)
- **Search Available Numbers**: `GET /v2/available_phone_numbers` -- [API reference](https://developers.telnyx.com/api/numbers/list-available-phone-numbers)
- **Order Numbers**: `POST /v2/number_orders` -- [API reference](https://developers.telnyx.com/api/numbers/create-number-order)

## Telnyx Webhook Events

This app handles these webhook events ([Call Control docs](https://developers.telnyx.com/docs/api/v2/call-control)):



## Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Type | Example | Required | Description | Where to get it |
|----------|------|---------|----------|-------------|-----------------|
| `TELNYX_API_KEY` | `string` | `KEY0123456789` | **yes** | Telnyx API v2 key | [Portal](https://portal.telnyx.com/api-keys) |
| `TELNYX_PHONE_NUMBER` | `string` | `+18005551234` | **yes** | Telnyx phone number | [Portal](https://portal.telnyx.com/numbers/my-numbers) |
| `TELNYX_CONNECTION_ID` | `string` | `149440475714` | **yes** | Call Control app ID | [Portal](https://portal.telnyx.com/call-control/applications) |
| `MERGE_API_KEY` | `string` | `your-key` | **yes** | Merge.dev API key | [Merge](https://app.merge.dev/keys) |
| `MERGE_ACCOUNT_TOKEN` | `string` | `your-token` | **yes** | Merge linked account token | [Merge](https://app.merge.dev) |
| `IT_ADMIN_PHONE` | `string` | `+12125551234` | no | IT admin phone | -- |
| `AI_MODEL` | `string` | `moonshotai/Kimi-K2.6` | no | AI model | [Models](https://developers.telnyx.com/docs/inference/models) |
| `PORT` | `integer` | `5000` | no | Server port | -- |

## Setup

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/merge-employee-onboarding-python
cp .env.example .env
pip install -r requirements.txt
python app.py
```

### Webhook Configuration

1. Expose your local server: `ngrok http 5000`
2. Configure in [Telnyx Portal](https://portal.telnyx.com/call-control/applications):
   - Call Control Application -> Webhook URL -> `https://<id>.ngrok.io/webhooks/voice`

## API Reference

### `POST /onboard`

Onboard.

```bash
curl -X POST http://localhost:5000/onboard \
  -H "Content-Type: application/json" \
  -d '{"example": "value"}'
```

**Response:**

```json
{"status": "ok"}
```

### `GET /onboardings`

Onboardings.

```bash
curl http://localhost:5000/onboardings
```

**Response:**

```json
{"status": "ok", "service": "merge-employee-onboarding"}
```

### `GET /health`

Health.

```bash
curl http://localhost:5000/health
```

**Response:**

```json
{"status": "ok", "service": "merge-employee-onboarding"}
```


## Webhook Endpoints

### `POST /webhooks/voice`

Telnyx sends call events here. Your app processes them and responds with the next action.

**Events handled:**



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
| `POST` | `/webhooks/hris` | Hris |
| `POST` | `/onboard` | Onboard |
| `GET` | `/onboardings` | Onboardings |
| `GET` | `/health` | Health |

## Resources

- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Call Control quickstart](https://developers.telnyx.com/docs/voice/call-control)
- [AI Inference docs](https://developers.telnyx.com/docs/inference)
- [Merge.dev API docs](https://docs.merge.dev)
- [Telnyx Portal](https://portal.telnyx.com)
