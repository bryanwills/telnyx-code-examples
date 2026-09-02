# Event Microsite That Takes Calls — Developer Guide

This guide walks you through the **Event Microsite That Takes Calls** sample. You'll learn how each piece of the Flask application works, how Telnyx primitives are wired together, and how to run the sample in safe demo mode or switch to live mode.

---

## Prerequisites

Before you begin, ensure you have:

- **Python 3.9+** installed locally
- A **Telnyx account** with access to:
  - SMS & WhatsApp messaging
  - Voice & Voice AI WebSocket
  - KV (Key-Value) store
  - SQLDB
  - Inference (GPT + Whisper)
- A **publicly accessible HTTPS endpoint** (e.g., ngrok) for receiving webhooks
- A **custom domain** configured in the Telnyx Portal (for the microsite)
- `pip` package manager

---

## Environment Setup

### 1. Clone and install dependencies

```bash
cd event-microsite-that-takes-calls
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment variables

Copy the example file and fill in your Telnyx credentials:

```bash
cp .env.example .env
```

Edit `.env` and replace placeholder values with your real Telnyx resource IDs and keys. Key variables include:

| Variable | Description |
|---|---|
| `TELNYX_API_KEY` | Your Telnyx API key |
| `TELNYX_PUBLIC_KEY` | Ed25519 public key for webhook verification |
| `TELNYX_PHONE_NUMBER` | Your Telnyx phone number (E.164 format) |
| `TELNYX_SMS_FROM` | SMS-enabled sender number |
| `TELNYX_WHATSAPP_FROM` | WhatsApp sender number |
| `TELNYX_VOICE_CONNECTION_ID` | Voice connection ID for WebSocket |
| `TELNYX_KV_NAMESPACE_ID` | KV namespace ID for event data |
| `TELNYX_SQLDB_CONNECTION_STRING` | SQLDB connection string |
| `TELNYX_INFERENCE_API_KEY` | Inference API key |
| `TELNYX_AI_CONCIERGE_NAME` | Display name for the AI concierge |
| `TELNYX_AI_CONCIERGE_PROMPT` | System prompt for the concierge |
| `TELNYX_SALES_REP_PHONE` | Sales rep phone number for hot leads |
| `TELNYX_EVENT_DOMAIN` | Custom domain for the microsite |
| `TELNYX_DEMO_MODE` | Set to `true` for demo mode, `false` for live |

### 3. Start the app

```bash
python app.py
```

By default, the app runs on `http://0.0.0.0:5000`. In demo mode, no real SMS, calls, or charges are made — all actions are logged instead.

---

## How the Code Works

### Configuration & Initialization

The app loads environment variables using `python-dotenv` and validates that all required variables are present. If any are missing, it logs an error at startup. The Telnyx SDK is configured with `telnyx.api_key`.

A `DEMO_MODE` flag controls whether real API calls are made or actions are logged as dry runs. This allows developers to test the full flow without incurring charges.

### Sample Event Data (Fixtures)

The `SAMPLE_EVENT_DATA` dictionary contains realistic event fixtures: event metadata, schedule items, speaker profiles, venue details, and sponsor information. This data is used as a fallback when KV is empty or unreachable, and is also seeded into KV on first run.

### KV Helpers

Two helper functions interact with the Telnyx KV store:

- **`kv_get(key)`** — Retrieves a JSON-encoded value from the KV namespace. Returns `None` on failure.
- **`kv_put(key, value)`** — Stores a JSON-encoded value in KV. Returns `True` on success.

The **`get_event_data()`** function fetches event data from KV. If no data exists, it seeds KV with the sample fixtures and returns them. This ensures the microsite always has content to render, even on first deployment.

### SQLDB Helpers

The **`sqldb_execute(query, params)`** function connects to Telnyx SQLDB, executes a parameterized query, commits the transaction, and returns result rows for `SELECT` queries. All database errors are caught and logged.

The **`init_sqldb()`** function creates two tables on startup:

- `exhibitor_leads` — Stores lead qualification data including company size, budget, timeline, and hot-lead status.
- `post_event_feedback` — Stores phone number, audio URL, transcript, and summary for post-event feedback.

### Webhook Signature Verification

The **`verify_webhook(req)`** function validates incoming Telnyx webhook signatures using Ed25519. It extracts the `Telnyx-Signature` header and calls `telnyx.Webhook.verify_signature()`. If verification fails, the request is rejected with a 401.

### Microsite Routes

The root route (`/`) renders an HTML template (`MICROSITE_HTML`) populated with event data from KV. The template includes styled sections for:

- Event header with name, date, location, and demo mode badge
- About section with event description
- Schedule with time, title, speaker, and room
- Speaker cards with photos, titles, and bios
- Venue details with address, WiFi, parking, and map link
- Sponsor cards with logos and tier badges
- Contact box with SMS, WhatsApp, voice, and in-browser voice options

Additional API routes (`/api/event`, `/api/schedule`, `/api/speakers`, `/api/venue`, `/api/sponsors`) return JSON representations of the same KV data, enabling programmatic access.

### SMS & WhatsApp — AI Concierge

The `/webhook/sms` and `/webhook/whatsapp` endpoints handle inbound messages from attendees. Each:

1. Verifies the webhook signature
2. Constructs the Telnyx event from the payload
3. Extracts the sender's phone number and message text
4. Calls `get_ai_concierge_response()` to generate a reply using Telnyx Inference
5. Sends the response back via SMS or WhatsApp (or logs it in demo mode)

The **`get_ai_concierge_response(user_message)`** function uses `telnyx.Inference.create_completion()` with a GPT model, passing the concierge system prompt and user message. On failure, it returns a fallback message.

### Voice — AI Concierge via Voice AI WebSocket

The `/webhook/voice` endpoint handles inbound voice calls:

1. Verifies the webhook signature
2. Extracts `call_control_id` from the payload
3. Answers the call using `telnyx.Call.answer()`
4. Starts the Voice AI WebSocket using `telnyx.Call.start_voice_ai()`, passing the concierge prompt and voice settings

The `/webhook/voice-ai` endpoint receives real-time events from the Voice AI WebSocket, including:

- `call.started` — Call has begun
- `call.answered` — Call was answered
- `transcription.received` — Real-time transcription of speech
- `call.ended` — Call has terminated

All events are logged for observability.

### Broadcast Schedule Changes

The `/api/broadcast-schedule-change` endpoint accepts a POST request with a schedule change description and optional session ID. It:

1. Fetches all opted-in attendee phone numbers from SQLDB
2. Constructs a broadcast message
3. Sends the message via both SMS and WhatsApp to each attendee (or logs it in demo mode)

This ensures schedule changes reach attendees across multiple channels simultaneously.

### Exhibitor Lead Qualification & Routing

The `/api/qualify-lead` endpoint captures exhibitor lead information:

1. Validates required fields: company, company_size, budget, timeline, phone_number
2. Qualifies the lead: a "hot lead" is identified when budget is "high" or "enterprise" AND timeline is "immediate", "q2 2025", or "within 30 days"
3. Stores the lead in SQLDB
4. If hot lead, sends an SMS alert to the sales rep (or logs it in demo mode)

### Post-Event Feedback Transcription & Sponsor Report

The `/api/submit-feedback` endpoint accepts spoken feedback:

1. Validates `phone_number` and `audio_url`
2. Transcribes the audio using `telnyx.Inference.create_transcription()` with the Whisper model
3. Summarizes the transcript using `telnyx.Inference.create_completion()` with a system prompt for sponsor report analysis
4. Stores the transcript and summary in SQLDB

The `/api/sponsor-report` endpoint generates a consolidated report from all feedback entries, including timestamps and summaries.

### In-Browser Voice WebSocket Info

The `/api/voice-websocket-info` endpoint returns configuration details for initializing the in-browser Voice AI WebSocket, including the connection ID, domain, and concierge name.

### Error Handling

The app includes error handlers for 401 (unauthorized), 404 (not found), and 500 (internal server error). All exceptions are logged using `app.logger.exception()` with full stack traces, while HTTP responses return generic error messages to avoid leaking sensitive information.

---

## Demo Mode vs Live Mode

### Demo Mode (Default)

Set `TELNYX_DEMO_MODE=true` in your `.env` file. In this mode:

- No real SMS, WhatsApp, or voice calls are sent
- No real charges are incurred
- All outbound actions are logged with `[DEMO]` prefix
- The microsite displays a "DEMO MODE" badge
- SQLDB tables are still created (if connection string is valid)

This is ideal for local development, testing, and demonstrations.

### Live Mode

Set `TELNYX_DEMO_MODE=false` and ensure all Telnyx credentials and resource IDs are valid. In live mode:

- Real SMS and WhatsApp messages are sent to attendees
- Real voice calls are answered and connected to the AI concierge
- Real lead alerts are sent to the sales rep
- Real transcription and summarization occur for feedback

**Warning:** Live mode incurs real charges. Use with caution.

---

## Running the Smoke Test

A smoke test is included to verify the app loads correctly:

```bash
python smoke_test.py
```

This test:

1. Imports the Flask app
2. Verifies the app object exists
3. Checks that all required environment variables are loaded
4. Confirms the KV and SQLDB helper functions are callable
5. Makes a test request to the `/` route and verifies a 200 response

Expected output:

```
✓ App imported successfully
✓ Required environment variables loaded
✓ KV helpers callable
✓ SQLDB helpers callable
✓ Index route returned 200
✓ All smoke tests passed
```

---

## Testing Webhooks Locally

To test webhooks locally, use ngrok to expose your local server:

```bash
ngrok http 5000
```

Then configure your Telnyx phone number's webhook URL in the Telnyx Portal to point to your ngrok URL (e.g., `https://abc123.ngrok.io/webhook/sms`).

---

## Next Steps

- [Telnyx Python SDK Documentation](https://docs.telnyx.com/sdk/python)
- [KV Store Guide](https://docs.telnyx.com/kv)
- [SQLDB Guide](https://docs.telnyx.com/sqldb)
- [Voice AI WebSocket Guide](https://docs.telnyx.com/voice-ai)
- [Inference API Guide](https://docs.telnyx.com/inference)
- [Messaging API Guide](https://docs.telnyx.com/messaging)
- [Webhooks Guide](https://docs.telnyx.com/webhooks)
