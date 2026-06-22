---
name: merge-invoice-collector
title: "Merge Invoice Collector"
description: "Pulls overdue invoices from accounting via Merge sorted by amount."
language: python
framework: flask
telnyx_products: [Voice, AI Inference, Messaging]
integrations: [Merge Accounting]
channel: [voice, sms]
---

# Merge Invoice Collector

> Also known as: accounts receivable, invoice collection, payment reminders, AR automation.

Pulls overdue invoices from accounting via Merge sorted by amount. AI calls debtors in priority order, negotiates payment terms conversationally, and sends SMS payment links mid-call.

## Why Telnyx

This collector places outbound calls, runs conversational AI inference, and fires SMS payment links from a single provider — Telnyx, the AI Communications Infrastructure that delivers voice, messaging, and AI inference over one private global network. Keeping Call Control, the inference API, and the messaging API on the same backbone means low-latency AI responses mid-call and a single API key to manage instead of stitching together separate voice, SMS, and LLM vendors.

## Telnyx API Endpoints Used

- **Call Control: Gather Using Speak**: `POST /v2/calls/{id}/actions/gather_using_speak` -- [API reference](https://developers.telnyx.com/api/call-control/gather-using-speak)
- **Call Control: Speak (TTS)**: `POST /v2/calls/{id}/actions/speak` -- [API reference](https://developers.telnyx.com/api/call-control/speak)
- **Call Control: Hangup**: `POST /v2/calls/{id}/actions/hangup` -- [API reference](https://developers.telnyx.com/api/call-control/hangup)
- **AI Inference**: `POST /v2/ai/chat/completions` -- [API reference](https://developers.telnyx.com/api/inference/chat-completions)
- **Send Message (SMS)**: `POST /v2/messages` -- [API reference](https://developers.telnyx.com/api/messaging/send-message)
- **Create Outbound Call**: `POST /v2/calls` -- [API reference](https://developers.telnyx.com/api/call-control/create-call)

## Telnyx Webhook Events

This app handles these webhook events ([Call Control docs](https://developers.telnyx.com/docs/api/v2/call-control)):

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
cd telnyx-code-examples/merge-invoice-collector-python
cp .env.example .env
pip install -r requirements.txt
python app.py
```

### Webhook Configuration

1. Expose your local server: `ngrok http 5000`
2. Configure in [Telnyx Portal](https://portal.telnyx.com/call-control/applications):
   - Call Control Application -> Webhook URL -> `https://<id>.ngrok.io/webhooks/voice`

## API Reference

### `POST /collect`

Collect.

```bash
curl -X POST http://localhost:5000/collect \
  -H "Content-Type: application/json" \
  -d '{"example": "value"}'
```

**Response:**

```json
{"status": "ok"}
```

### `GET /invoices`

Invoices.

```bash
curl http://localhost:5000/invoices
```

**Response:**

```json
{"status": "ok", "service": "merge-invoice-collector"}
```

### `GET /collections`

Collections.

```bash
curl http://localhost:5000/collections
```

**Response:**

```json
{"status": "ok", "service": "merge-invoice-collector"}
```

### `GET /health`

Health.

```bash
curl http://localhost:5000/health
```

**Response:**

```json
{"status": "ok", "service": "merge-invoice-collector"}
```


## Webhook Endpoints

### `POST /webhooks/voice`

Telnyx sends call events here. Your app processes them and responds with the next action.

**Events handled:**

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
| `POST` | `/collect` | Collect |
| `POST` | `/webhooks/voice` | Voice |
| `GET` | `/invoices` | Invoices |
| `GET` | `/collections` | Collections |
| `GET` | `/health` | Health |

## Troubleshooting

| Issue | Likely cause | Fix |
|-------|--------------|-----|
| `401 invalid signature` on `/webhooks/voice` | `TELNYX_PUBLIC_KEY` is missing or wrong, so Ed25519 verification fails (the app rejects every webhook when it's unset) | Set `TELNYX_PUBLIC_KEY` from the [Telnyx Portal](https://portal.telnyx.com) public key; ensure no whitespace was added when copying the base64 value |
| `401 invalid signature` only on replays | Webhook timestamp is older than 5 minutes (`MAX_SKEW_SECONDS`) | Make sure your server clock is in sync (NTP); Telnyx must reach your endpoint promptly |
| `Failed to fetch invoices` from `POST /collect` | `MERGE_API_KEY` or `MERGE_ACCOUNT_TOKEN` is missing/invalid, or the linked account has no accounting integration | Verify both values in the [Merge dashboard](https://app.merge.dev); confirm the linked account exposes `/accounting/v1/invoices` |
| Calls never arrive / webhooks not received | Webhook URL not publicly reachable, or `TELNYX_CONNECTION_ID` / `TELNYX_PHONE_NUMBER` unset | Expose the server with `ngrok http 5000` and set the Call Control Application webhook URL; confirm all three Telnyx env vars are populated |
| Invoices skipped (`skipped_no_phone` high) | Merge contacts lack a phone number | Ensure contacts in the accounting system have phone numbers synced through Merge |

## Related Examples

- [merge-expense-by-phone-python](../merge-expense-by-phone-python/) — voice + Merge accounting workflow over the phone
- [merge-deal-desk-alerts-python](../merge-deal-desk-alerts-python/) — Merge-driven alerts routed through Telnyx
- [merge-employee-hotline-python](../merge-employee-hotline-python/) — Merge data backing an AI voice hotline
- [edge-merge-ai-receptionist-python](../edge-merge-ai-receptionist-python/) — AI receptionist combining Merge data with Telnyx voice

## Resources

- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Call Control quickstart](https://developers.telnyx.com/docs/voice/call-control)
- [AI Inference docs](https://developers.telnyx.com/docs/inference)
- [Merge.dev API docs](https://docs.merge.dev)
- [Telnyx Portal](https://portal.telnyx.com)
