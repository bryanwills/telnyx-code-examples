---
name: ai-call-campaign-orchestrator
title: "AI Call Campaign Orchestrator"
description: "Durable outbound call campaign with rate limiting, SQL tracking, and SMS summary using Telnyx Agent SDK, Call Control, and SMS."
language: python
framework: flask
telnyx_products: [Call Control, SMS, Agent SDK]
---

# AI Call Campaign Orchestrator

Durable outbound call campaign with rate limiting, SQL tracking, and SMS summary.

## Why Telnyx

This sample demonstrates how to build a durable, production-grade outbound call campaign using Telnyx's **AI Communications Infrastructure**. Telnyx provides the primitives you need to orchestrate complex communication workflows — queueing outbound calls, rate-limiting them with the Agent SDK, controlling each call with Call Control, and delivering results via SMS — all in one platform. Instead of stitching together multiple vendors, Telnyx gives you a single API surface for voice, messaging, and stateful workflow orchestration.

## Telnyx API Endpoints Used

| API | Method | Purpose |
|-----|--------|---------|
| `telnyx.Call.create()` | POST | Create an outbound Call Control call |
| `telnyx.Message.create()` | POST | Send SMS campaign summary |
| `telnyx.webhooks.unwrap()` | — | Verify inbound webhook signature (Ed25519) |
| `POST /webhooks/call` | Webhook | Receive Call Control events (answer, hangup, etc.) |

## Architecture

```
POST /campaign { phone_numbers: [...] }
  → CampaignAgent.onTask()
  → this.queue() all calls
  → this.schedule() rate limiter: 10 calls/min
  → Each call: Call Control answer + LLM + gather + hangup
  → Result saved to SQL: ctx.storage.sql.exec('INSERT INTO results ...')
  → On completion: SMS summary via this.env.TELNYX.messages.send()
```

```
┌─────────────────┐     ┌──────────────────────────────────────────────┐
│  Client         │     │  Flask App (app.py)                          │
│  POST /campaign │ ──▶ │                                              │
└─────────────────┘     │  ┌────────────────────────────────────────┐  │
                        │  │  CampaignAgent                         │  │
                        │  │  ┌─────────────┐                       │  │
                        │  │  │ queue()     │  Enqueue all calls    │  │
                        │  │  └─────────────┘                       │  │
                        │  │  ┌─────────────┐                       │  │
                        │  │  │ schedule()   │  Rate limit 10/min   │  │
                        │  │  └─────────────┘                       │  │
                        │  │  ┌─────────────┐                       │  │
                        │  │  │ make_call()  │  Call Control API    │  │
                        │  │  └─────────────┘                       │  │
                        │  │  ┌─────────────┐                       │  │
                        │  │  │ SQLite       │  Track results       │  │
                        │  │  └─────────────┘                       │  │
                        │  │  ┌─────────────┐                       │  │
                        │  │  │ SMS summary  │  Send completion     │  │
                        │  │  └─────────────┘                       │  │
                        │  └────────────────────────────────────────┘  │
                        └──────────────────────────────────────────────┘
```

## Environment Variables

| Variable | Type | Example | Required | Description | Where to get it |
|----------|------|---------|----------|-------------|-----------------|
| `CALL_RATE_LIMIT_PER_MINUTE` | `string` | `your_call_rate_limit_per_minute_here` | **yes** | CALL_RATE_LIMIT_PER_MINUTE | — |
| `PORT` | `string` | `your_port_here` | **yes** | PORT | — |
| `TELNYX_API_KEY` | `string` | `your_telnyx_api_key_here` | **yes** | TELNYX_API_KEY | — |
| `TELNYX_CONNECTION_ID` | `string` | `your_telnyx_connection_id_here` | **yes** | TELNYX_CONNECTION_ID | — |
| `TELNYX_PHONE_NUMBER` | `string` | `your_telnyx_phone_number_here` | **yes** | TELNYX_PHONE_NUMBER | — |
| `TELNYX_PUBLIC_KEY` | `string` | `your_telnyx_public_key_here` | **yes** | TELNYX_PUBLIC_KEY | — |
| `TELNYX_SMS_FROM` | `string` | `your_telnyx_sms_from_here` | **yes** | TELNYX_SMS_FROM | — |
| `TELNYX_SMS_TO` | `string` | `your_telnyx_sms_to_here` | **yes** | TELNYX_SMS_TO | — |
| `TELNYX_WEBHOOK_URL` | `string` | `your_telnyx_webhook_url_here` | **yes** | TELNYX_WEBHOOK_URL | — |

## Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/team-telnyx/telnyx-code-examples.git
   cd telnyx-code-examples/ai-call-campaign-orchestrator
   ```

2. **Create a virtual environment**

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**

   Copy the `.env.example` file to `.env` and fill in your Telnyx credentials:

   ```bash
   cp .env.example .env
   ```

   Edit `.env` with your actual values. Never commit real credentials.

5. **Run the application**

   ```bash
   python app.py
   ```

   The server will start on `http://localhost:5000` (or the port specified in `PORT`).

## API Reference

### `POST /campaign`

Create a new outbound call campaign.

**Request Body:**

```json
{
  "phone_numbers": ["+15551234567", "+15559876543"]
}
```

**Response:**

```json
{
  "campaign_id": "3f2b8c1e-9a4d-4f6b-8e7a-2c5d9f1a3b4c",
  "status": "started"
}
```

**Status Codes:**

- `202 Accepted` — Campaign started successfully
- `400 Bad Request` — Missing or invalid `phone_numbers`

### `GET /campaign/<campaign_id>`

Get the status of a campaign.

**Response:**

```json
{
  "campaign_id": "3f2b8c1e-9a4d-4f6b-8e7a-2c5d9f1a3b4c",
  "total": 2,
  "completed": false,
  "results": [
    {
      "to": "+15551234567",
      "status": "queued",
      "call_control_id": "call_control_id_here"
    }
  ]
}
```

**Status Codes:**

- `200 OK` — Campaign found
- `404 Not Found` — Campaign does not exist

### `POST /webhooks/call`

Receive Call Control webhook events. The request must include a valid Telnyx Ed25519 signature.

**Response:**

```json
{
  "status": "ok"
}
```

### `GET /health`

Health check endpoint.

**Response:**

```json
{
  "status": "ok"
}
```

## Troubleshooting

| Issue | Likely Cause | Solution |
|-------|--------------|----------|
| `telnyx.exceptions.AuthenticationError` | Invalid `TELNYX_API_KEY` | Verify your API key in the [Telnyx Portal](https://portal.telnyx.com) |
| `telnyx.exceptions.InvalidRequestError` | Invalid `TELNYX_CONNECTION_ID` or phone number | Check your connection ID and phone number format (E.164) |
| Webhook verification fails | Incorrect `TELNYX_PUBLIC_KEY` | Ensure the public key matches your API key's public key |
| SMS summary not sent | `TELNYX_SMS_TO` not set | Set `TELNYX_SMS_TO` to the destination phone number |
| Calls not being placed | `TELNYX_WEBHOOK_URL` not reachable | Ensure the webhook URL is publicly accessible and HTTPS |
| Rate limiting not working | `CALL_RATE_LIMIT_PER_MINUTE` set too high | Adjust the value to control call volume |

## Agent Discovery

- [Telnyx Agent Signup](https://telnyx.com/agent-signup.md)
- [Telnyx AI GitHub Repository](https://github.com/team-telnyx/ai)
- [Telnyx llms.txt](https://telnyx.com/llms.txt)

## Related Examples

- [agent-desk](https://github.com/team-telnyx/telnyx-code-examples/tree/main/edge-compute-statefulactor/examples/agent-desk) — Stateful actor pattern for agent-based workflows
- [Call Control Examples](https://github.com/team-telnyx/telnyx-code-examples/tree/main/call-control) — Outbound call control patterns
- [SMS Examples](https://github.com/team-telnyx/telnyx-code-examples/tree/main/sms) — Messaging patterns

## Resources

- [Telnyx Developer Documentation](https://developers.telnyx.com)
- [Telnyx API Reference](https://developers.telnyx.com/api)
- [Telnyx Python SDK](https://github.com/team-telnyx/telnyx-python)
- [Telnyx Product Page](https://telnyx.com)
- [Telnyx Pricing](https://telnyx.com/pricing)
