---
name: send-mms-picture-message
title: "Send MMS Picture Message"
description: "Send an MMS message with image attachments using the Telnyx Messaging API."
language: python
framework: flask
telnyx_products: [Messaging]
---

# Send MMS Picture Message

Send an MMS message with image attachments using the Telnyx Messaging API.

## Telnyx API Endpoints Used

- **Send Message**: `POST /v2/messages` -- [API reference](https://developers.telnyx.com/api/messaging/send-message)

## Architecture

```
  API Request
        │
        ▼
  ┌──────────────────┐
  │ Telnyx Messaging  │
  └────────┬─────────┘
           │
           └──► JSON response
```

## Why Telnyx

- **Deliverability built in** — number reputation, 10DLC registration, and deliverability monitoring included.

## Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Type | Example | Required | Description | Where to get it |
|----------|------|---------|----------|-------------|-----------------|
| `TELNYX_API_KEY` | `string` | `KEY0123456789ABCDEF` | **yes** | Telnyx API v2 key | [Portal](https://portal.telnyx.com/api-keys) |
| `TELNYX_PHONE_NUMBER` | `string` | `your_value` | **yes** | Telnyx phone number | — |
| `FLASK_DEBUG` | `string` | `false` | no | Flask debug | — |

## Setup

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/send-mms-picture-message-python
cp .env.example .env    # ← fill in your credentials
pip install -r requirements.txt
python app.py           # starts on http://localhost:5000
```

### Docker

```bash
docker build -t send-mms-picture-message-python .
docker run --env-file .env -p 5000:5000 send-mms-picture-message-python
```

## API Reference

### `POST /mms/send`

HTTP endpoint to send MMS with media attachments.

```bash
curl -X POST http://localhost:5000/mms/send \
  -H "Content-Type: application/json" \
  -d '{
    "to": "+12125551234",
    "message": "Hello from Telnyx!"
  }'
```

**Response:**

```json
{
  "message_id": "msg-f5d7a7e0-1234-5678",
  "status": "queued",
  "to": "+12125551234",
  "segments": 1
}
```


## Troubleshooting

- **Connection refused on port 5000**: App isn't running. Run `python app.py` and check no other process uses port 5000.
- **401 Unauthorized**: Your `TELNYX_API_KEY` is invalid. Generate a new one at [portal.telnyx.com/api-keys](https://portal.telnyx.com/api-keys).
- **SMS not sending**: Check number has messaging enabled and a [Messaging Profile](https://portal.telnyx.com/messaging/profiles) assigned.

## Related Examples

- [send-sms-python](../send-sms-python/) - Basic SMS
- [sms-chatbot-with-conversation-memory-python](../sms-chatbot-with-conversation-memory-python/) - AI SMS chatbot

## Resources

- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Telnyx Portal](https://portal.telnyx.com)
