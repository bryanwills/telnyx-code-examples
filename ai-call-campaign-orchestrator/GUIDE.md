# AI Call Campaign Orchestrator — Developer Guide

This guide walks through the `ai-call-campaign-orchestrator` example, a durable outbound call campaign system built on Telnyx. You'll learn how the code orchestrates 100+ outbound calls, rate-limits them to 10 per minute, tracks results in SQL, and sends an SMS summary when the campaign finishes.

## What You'll Build

A Flask app that exposes a REST API to launch outbound call campaigns. Each campaign:

1. Queues all phone numbers for outbound calls.
2. Processes them in batches, rate-limited to 10 calls per minute.
3. Places each call using Telnyx Call Control.
4. Records every call result (queued, failed, etc.) in a SQL database.
5. Sends an SMS summary to a configured number when the campaign completes.

This is the **durable workflow with live progress** pattern — a long-running, multi-step process that survives individual call failures and gives you a live view of progress.

---

## Prerequisites

Before you run this example, make sure you have:

- **Python 3.9+** installed.
- **A Telnyx account** with:
  - An API key (`TELNYX_API_KEY`).
  - A phone number (`TELNYX_PHONE_NUMBER`) with outbound calling and SMS enabled.
  - A connection ID (`TELNYX_CONNECTION_ID`) for Call Control.
  - A webhook URL (`TELNYX_WEBHOOK_URL`) that Telnyx can reach (e.g., via `ngrok` for local testing).
- **A destination phone number** (`TELNYX_SMS_TO`) to receive the SMS summary.

---

## Environment Setup

1. **Clone the repo** and navigate to the example folder:

   ```bash
   cd ai-call-campaign-orchestrator
   ```

2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Create your `.env` file** from the template:

   ```bash
   cp .env.example .env
   ```

4. **Fill in your credentials** in `.env`:

   ```bash
   TELNYX_API_KEY=your_telnyx_api_key_here
   TELNYX_PUBLIC_KEY=your_telnyx_public_key_here
   TELNYX_PHONE_NUMBER=+1234567890
   TELNYX_CONNECTION_ID=your_connection_id_here
   TELNYX_WEBHOOK_URL=https://your-ngrok-url.ngrok.io/webhooks/call
   TELNYX_SMS_FROM=+1234567890
   TELNYX_SMS_TO=+1987654321
   CALL_RATE_LIMIT_PER_MINUTE=10
   ```

   > **Never commit your `.env` file.** It contains secrets.

4. **Start the Flask server**:

   ```bash
   python app.py
   ```

   The server will run on `http://localhost:5000` (or the port in `PORT`).

5. **Expose your webhook URL** (if testing locally):

   ```bash
   ngrok http 5000
   ```

   Copy the `https://` URL from ngrok and set it as `TELNYX_WEBHOOK_URL` in `.env`.

---

## How It Works — Step by Step

### 1. Creating a Campaign

**File reference:** `create_campaign()` route, near the bottom of `app.py`.

When you `POST /campaign` with a JSON body containing a list of phone numbers, the app:

1. Generates a unique `campaign_id` (UUID).
2. Stores a `CampaignAgent` instance in an in-memory dictionary.
3. Calls `agent.on_task()` to kick off the workflow.
4. Returns `202 Accepted` with the campaign ID.

```bash
curl -X POST http://localhost:5000/campaign \
  -H "Content-Type: application/json" \
  -d '{"phone_numbers": ["+15551234567", "+15559876543", "..."]}'
```

### 2. The CampaignAgent — Your Durable Workflow

**File reference:** `CampaignAgent` class, near the top of `app.py`.

The `CampaignAgent` is the heart of the example. It models the entire campaign lifecycle:

- **`on_task()`** — the entry point. It initializes the SQL table, queues every phone number, and schedules the first batch.
- **`queue()`** — mimics the Agent SDK's `queue()` primitive. In a production Agent SDK, this enqueues a task onto a durable queue. Here, it appends to an in-memory list.
- **`schedule()`** — mimics the Agent SDK's `schedule()` primitive. It runs a task after a delay using a background thread. In a real Agent SDK, this would be a durable timer.

> **Why this matters:** The queue and schedule primitives are what make the workflow *durable*. If the process restarts, a real Agent SDK would resume from the queue. This example uses in-memory state for simplicity, but the pattern is identical.

### 3. Rate-Limited Batch Processing

**File reference:** `process_next_batch()` method.

This is the core of the rate-limiting logic:

1. It checks if the queue is empty or the campaign is complete.
2. It pops up to `CALL_RATE_LIMIT_PER_MINUTE` items (default 10) from the queue.
3. For each, it calls `make_call()`.
4. If the queue still has items, it schedules the next batch after `CALL_RATE_LIMIT_SECONDS` (60 / rate limit).
5. If the queue is empty, it marks the campaign complete and sends the SMS summary.

This ensures you never exceed 10 calls per minute, respecting Telnyx rate limits and avoiding carrier throttling.

### 4. Placing Outbound Calls with Call Control

**File reference:** `make_call()` method.

For each phone number, the app uses the Telnyx Python SDK to create an outbound call:

```python
call = telnyx.Call.create(
    to=to,
    from_=TELNYX_PHONE_NUMBER,
    connection_id=os.getenv("TELNYX_CONNECTION_ID"),
    webhook_url=os.getenv("TELNYX_WEBHOOK_URL"),
    webhook_url_method="POST",
)
```

This is the **Call Control** primitive. Telnyx will:

- Place the call to the destination.
- Send webhooks to your `TELNYX_WEBHOOK_URL` for call events (e.g., `call.answered`, `call.hangup`).

In a production implementation, you'd handle those webhooks to drive an IVR flow (e.g., answer, play a message, gather DTMF, hang up). This example keeps it simple — it just records the call as "queued" and stores the `call_control_id`.

### 5. Tracking Results in SQL

**File reference:** `_init_storage()` and `_save_result()` methods.

The example uses `ctx.storage.sql` (the Agent SDK's SQL storage) to persist results. In this standalone Flask version, we use an in-memory SQLite-like interface via `self.storage`.

- `_init_storage()` creates the `campaign_results` table if it doesn't exist.
- `_save_result()` inserts a row for each call attempt with:
  - `campaign_id`
  - `phone_number`
  - `status` (`queued`, `failed`, etc.)
  - `call_control_id`
  - `created_at` timestamp

This gives you a durable, queryable record of every call in the campaign.

### 6. Sending the SMS Summary

**File reference:** `_send_summary()` method.

When the queue is empty and all calls have been placed, the agent sends an SMS summary:

1. It queries the SQL table to count results by status.
2. It builds a summary string like `queued: 10, failed: 2`.
3. It sends the SMS using the Telnyx Messages API:

```python
telnyx.Message.create(
    from_=TELNYX_SMS_FROM,
    to=TELNYX_SMS_TO,
    text=text,
)
```

This is the **SMS** primitive — a simple, reliable way to notify an admin that the campaign is done.

### 7. Webhooks — Handling Call Events

**File reference:** `call_webhook()` route.

The `/webhooks/call` endpoint receives Telnyx Call Control events. It:

1. Verifies the request signature using `telnyx.webhooks.unwrap()` with your public key.
2. Logs the event payload.
3. Returns `200 OK` to acknowledge.

In a full implementation, you'd use the `call_control_id` to send Call Control commands (e.g., `answer`, `gather`, `hangup`) to drive the call flow.

---

## Telnyx Primitives Used

| Primitive | Where | What it does |
|-----------|-------|--------------|
| **Agent SDK `queue()`** | `CampaignAgent.on_task()` | Enqueues all outbound call tasks for the campaign. |
| **Agent SDK `schedule()`** | `CampaignAgent.process_next_batch()` | Schedules the next batch after the rate-limit delay. |
| **Call Control** | `make_call()` | Places outbound calls and receives webhook events. |
| **SMS** | `_send_summary()` | Sends the campaign summary via `telnyx.Message.create()`. |
| **SQL DB** | `_init_storage()` / `_save_result()` | Persists call results for tracking and reporting. |

---

## Running the Example

1. **Start the server** (as described above).
2. **Create a campaign**:

   ```bash
   curl -X POST http://localhost:5000/campaign \
     -H "Content-Type: application/json" \
     -d '{"phone_numbers": ["+15551234567", "+15559876543"]}'
   ```

   You'll get a `campaign_id` back.

3. **Check campaign status**:

   ```bash
   curl http://localhost:5000/campaign/<campaign_id>
   ```

   This returns the total number of numbers, whether the campaign is complete, and the results so far.

4. **Watch the logs** — you'll see calls being placed, results saved, and the SMS summary sent.

---

## Troubleshooting

| Issue | Likely Cause | Fix |
|-------|--------------|-----|
| `TELNYX_API_KEY` not set | Missing `.env` or env var | Ensure `.env` exists and is populated. |
| Calls fail with `401` | Invalid API key | Verify your key in the Telnyx portal. |
| Webhook returns `403` | Invalid signature | Ensure `TELNYX_PUBLIC_KEY` matches your account. |
| No SMS summary | `TELNYX_SMS_TO` not set | Set it to a valid destination number. |
| Rate limit exceeded | `CALL_RATE_LIMIT_PER_MINUTE` too high | Lower it (e.g., to 5) or check Telnyx limits. |

---

## Next Steps

- **Deepen the Call Control flow** — implement `answer`, `gather`, and `hangup` in the webhook handler to build an interactive IVR.
- **Add LLM integration** — use Telnyx's AI features to generate dynamic responses during calls.
- **Persist state** — replace the in-memory `campaigns` dict with a real database (e.g., PostgreSQL) for durability.
- **Scale up** — use a real queue (e.g., Redis, SQS) instead of the in-memory list for production workloads.

---

## Resources

- [Telnyx Call Control API docs](https://developers.telnyx.com/docs/api/v2/call-control)
- [Telnyx Messaging API docs](https://developers.telnyx.com/docs/api/v2/messaging)
- [Telnyx Agent SDK docs](https://developers.telnyx.com/docs/agents)
- [Telnyx Python SDK on GitHub](https://github.com/team-telnyx/telnyx-python)

---

This example is part of the **Telnyx AI Communications Infrastructure** — a platform for building durable, intelligent communication workflows.
