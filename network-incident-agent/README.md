---
name: network-incident-agent
title: "Network Incident Agent"
description: "An AI agent that acts as the incident itself, proactively notifying affected customers via SMS, handling inbound calls with incident context, and generating RCA documents."
language: python
framework: flask
telnyx_products: [Messaging, Voice, CloudFS, AI Agent]
---

# Network Incident Agent

An AI-powered network incident agent that acts as the incident itself — proactively notifying affected customers via SMS, answering inbound calls with real-time incident context, scheduling status checks, and generating root cause analysis (RCA) documents to CloudFS.

## Why Telnyx

This sample demonstrates how Telnyx's **AI Communications Infrastructure** enables you to build intelligent, proactive communication agents. By combining Telnyx's Messaging, Voice, and CloudFS APIs with the Telnyx Agent framework, you can create an agent that doesn't just respond to conversations — it owns the entire incident lifecycle. The agent maintains incident state, reaches out to customers before they call you, provides context-aware voice responses, and documents the full timeline for post-incident analysis.

## Telnyx API Endpoints Used

| API | Method | Endpoint | Purpose |
|-----|--------|----------|---------|
| Messaging | POST | `/v2/messages` | Send proactive SMS notifications to affected customers |
| Call Control | POST | `/v2/calls/{call_control_id}/actions/speak` | Speak incident context to callers |
| CloudFS | POST | `/v2/cloudfs/files` | Upload RCA documents to CloudFS |
| Webhooks | POST | `/webhooks/inbound-sms` | Receive inbound SMS from customers |
| Webhooks | POST | `/webhook/call` | Receive inbound call events from Telnyx |

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Network Incident Agent                      │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                    NetworkIncidentAgent                       │  │
│  │                                                               │  │
│  │  ┌─────────────┐  ┌──────────────┐  ┌──────────────────────┐  │  │
│  │  │ Incident    │  │ Customer     │  │ Status Check         │  │  │
│  │  │ State       │  │ Notification │  │ Scheduler            │  │  │
│  │  │             │  │              │  │                      │  │  │
│  │  │ • status    │  │ • SMS via    │  │ • this.schedule()    │  │  │
│  │  │ • severity  │  │   Telnyx     │  │ • recurring checks   │  │  │
│  │  │ • timeline  │  │ • affected   │  │ • logs to timeline   │  │  │
│  │  │ • root cause│  │   customers  │  │                      │  │  │
│  │  └─────────────┘  └──────────────┘  └──────────────────────┘  │  │
│  │                                                               │  │
│  │  ┌─────────────┐  ┌──────────────┐  ┌──────────────────────┐  │  │
│  │  │ Inbound     │  │ RCA          │  │ SQLite Timeline      │  │  │
│  │  │ Call        │  │ Generation   │  │                      │  │  │
│  │  │ Handler     │  │              │  │ • incident_timeline  │  │  │
│  │  │             │  │ • CloudFS    │  │ • event logging      │  │  │
│  │  │ • speak     │  │ • JSON doc   │  │ • queryable history  │  │  │
│  │  │   context   │  │ • RCA content│  │                      │  │  │
│  │  └─────────────┘  └──────────────┘  └──────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────────────┐ │
│  │ Flask App   │  │ Telnyx SDK   │  │ SQLite Database            │ │
│  │             │  │              │  │                            │ │
│  │ • /health   │  │ • Messaging  │  │ • incident_timeline.db     │ │
│  │ • /incident │  │ • Call Ctrl  │  │ • event history            │ │
│  │ • /webhooks │  │ • CloudFS    │  │ • incident state           │ │
│  └─────────────┘  └──────────────┘  └────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

## Environment Variables

| Variable | Type | Example | Required | Description | Where to get it |
|----------|------|---------|----------|-------------|-----------------|
| `AFFECTED_CUSTOMERS` | `string` | `your_affected_customers_here` | **yes** | AFFECTED_CUSTOMERS | — |
| `CLOUDFS_BUCKET` | `string` | `your_cloudfs_bucket_here` | **yes** | CLOUDFS_BUCKET | — |
| `INCIDENT_DB_PATH` | `string` | `your_incident_db_path_here` | **yes** | INCIDENT_DB_PATH | — |
| `INCIDENT_ID` | `string` | `your_incident_id_here` | **yes** | INCIDENT_ID | — |
| `PORT` | `string` | `your_port_here` | **yes** | PORT | — |
| `TELNYX_API_KEY` | `string` | `your_telnyx_api_key_here` | **yes** | TELNYX_API_KEY | — |
| `TELNYX_PUBLIC_KEY` | `string` | `your_telnyx_public_key_here` | **yes** | TELNYX_PUBLIC_KEY | — |
| `TELNYX_SMS_FROM_NUMBER` | `string` | `your_telnyx_sms_from_number_here` | **yes** | TELNYX_SMS_FROM_NUMBER | — |

## Setup

1. **Clone the repository**

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/network-incident-agent
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Configure environment variables**

```bash
cp .env.example .env
# Edit .env and fill in your Telnyx API credentials and configuration
```

4. **Run the application**

```bash
python app.py
```

The server will start on `http://localhost:8080` (or the port specified in your `.env` file).

## API Reference

### GET `/health`

Health check endpoint.

**Response:**
```json
{
  "status": "healthy"
}
```

**Status Codes:**
- `200` — Service is healthy

---

### GET `/incident/status`

Get the current incident state.

**Response:**
```json
{
  "status": "investigating",
  "severity": "SEV-1",
  "description": "",
  "affected_services": [],
  "start_time": "2024-01-15T10:30:00Z",
  "resolution_time": null,
  "root_cause": null,
  "timeline": []
}
```

**Status Codes:**
- `200` — Incident state retrieved successfully

---

### POST `/incident/update`

Update the incident status and notify affected customers.

**Request Body:**
```json
{
  "status": "monitoring",
  "description": "Issue isolated to edge router, monitoring traffic"
}
```

**Response:**
```json
{
  "status": "updated",
  "incident_state": {
    "status": "monitoring",
    "severity": "SEV-1",
    "description": "Issue isolated to edge router, monitoring",
    "affected_services": [],
    "start_time": "2024-01-15T00:30:00Z",
    "resolution_time": null,
    "root_cause": null,
    "timeline": []
  }
}
```

**Status Codes:**
- `200` — Incident updated successfully
- `400` — Missing required `status` field

---

### POST `/incident/notify`

Proactively notify all affected customers via SMS.

**Request Body:**
```json
{
  "message": "We are aware of the issue and working to resolve it."
}
```

**Response:**
```json
{
  "status": "ok",
  "notified": 3
}
```

**Status Codes:**
- `200` — Notifications sent successfully

---

### POST `/incident/rca`

Generate an RCA document and upload to CloudFS.

**Request Body:**
```json
{
  "root_cause": "Network switch failure in data center A"
}
```

**Response:**
```json
{
  "status": "ok"
}
```

**Status Codes:**
- `200` — RCA generated and uploaded successfully
- `400` — Missing required `root_cause` field

---

### POST `/webhooks/inbound-sms`

Webhook endpoint for inbound SMS messages from Telnyx.

**Request Body (Telnyx webhook payload):**
```json
{
  "data": {
    "payload": {
      "from": {"phone_number": "+1234567890"},
      "to": [{"phone_number": "+1987654321"}],
      "text": "What's the status of the incident?"
    }
  }
}
```

**Response:**
```json
{
  "status": "ok"
}
```

**Status Codes:**
- `200` — Webhook processed successfully
- `500` — Internal server error

---

### POST `/webhook/call`

Webhook endpoint for inbound call events from Telnyx.

**Request Body (Telnyx webhook payload):**
```json
{
  "data": {
    "payload": {
      "call_control_id": "call_control_id_here",
      "from": "+1234567890"
    }
  }
}
```

**Response:**
```json
{
  "status": "ok"
}
```

**Status Codes:**
- `200` — Webhook processed successfully
- `500` — Internal server error

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| `TELNYX_API_KEY` not found | Environment variable not set | Ensure `.env` file exists and contains `TELNYX_API_KEY=your_api_key` |
| SMS messages not sending | Invalid `TELNYX_SMS_FROM_NUMBER` | Verify the number is a valid Telnyx number and has SMS capabilities |
| Webhook signature verification fails | Invalid `TELNYX_PUBLIC_KEY` | Ensure the public key matches your Telnyx account's public key |
| RCA upload fails | Invalid `CLOUDFS_BUCKET` | Verify the bucket exists and you have write permissions |
| Database errors | Corrupted or missing SQLite database | Delete `incident_timeline.db` and restart the application |
| Port already in use | Another process using port 8080 | Change `PORT` in `.env` to an available port |
| Inbound calls not speaking context | Missing call control ID | Ensure the webhook payload includes `call_control_id` |

## Agent Discovery

- [Telnyx Agent Signup](https://telnyx.com/agent-signup.md)
- [Telnyx AI Agent Repository](https://github.com/team-telnyx/ai)
- [Telnyx LLM Documentation](https://llms.txt)

## Related Examples

- **sms-ai-agent** — Build an AI-powered SMS assistant
- **voice-ai-agent** — Create a voice-based AI agent
- **call-control-basics** — Learn the fundamentals of Telnyx Call Control
- **messaging-basics** — Get started with Telnyx Messaging APIs

## Resources

- [Telnyx Developer Documentation](https://developers.telnyx.com)
- [Telnyx API Reference](https://developers.telnyx.com/api)
- [Telnyx Python SDK](https://github.com/team-telnyx/telnyx-python)
- [Telnyx Product Page](https://telnyx.com)
- [Telnyx Pricing](https://telnyx.com/pricing)
