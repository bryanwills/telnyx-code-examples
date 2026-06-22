# Build a MCP Server on Edge Compute

Deploy an MCP server to Telnyx Edge Compute exposing Telnyx APIs as tools for AI agents. Send SMS, search numbers, run inference.

## How It Works

```
  API Request
        │
        ▼
  ┌──────────────────┐
  │ Parse message     │
  └────────┬─────────┘
           │
           ▼
  ┌──────────────────┐
  │ AI Inference      │
  │ • Business logic   │
  └────────┬─────────┘
           │ ◄──── conversation loop
           │
           └──► SMS notification
```

## Telnyx Products Used

- **Edge Compute** — serverless functions at the network edge
- **Messaging** — send and receive messages with delivery receipts
- **Numbers** — phone number search, purchase, and configuration
- **AI Inference** — LLM inference with OpenAI-compatible API, runs on Telnyx infrastructure

## API Endpoints

- **Messages**: `POST /v2/messages` — [API reference](https://developers.telnyx.com/api/messaging/send-message)
- **Available Phone Numbers**: `GET /v2/available_phone_numbers` — [API reference](https://developers.telnyx.com/api/numbers/list-available-phone-numbers)
- **AI Inference**: `POST /v2/ai/chat/completions` — [API reference](https://developers.telnyx.com/api/inference/chat-completions)
- **Phone Numbers**: `GET /v2/phone_numbers` — [API reference](https://developers.telnyx.com/api/numbers/list-phone-numbers)

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)
- [Phone number](https://portal.telnyx.com/numbers/my-numbers) with messaging enabled
- [Messaging Profile](https://portal.telnyx.com/messaging/profiles) with webhook URL
- [ngrok](https://ngrok.com) for exposing your local server to Telnyx webhooks

## Step 1: Set Up the Project

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/edge-mcp-server-deploy-python
cp .env.example .env
pip install -r requirements.txt
```

Edit `.env` with your Telnyx credentials. Each variable links to where you find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Understand the Code

Everything lives in `app.py` (164 lines). Here's what each piece does.

### Business Logic

- **`new()`** — Processes new request and returns result.

## Step 3: Run It

```bash
python app.py
```

Server starts on `http://localhost:5000`.

In a separate terminal, expose your server for webhooks:

```bash
ngrok http 5000
```

Copy the HTTPS URL and set it in the [Telnyx Portal](https://portal.telnyx.com):

- **Messaging Profile** → Inbound Webhook → `https://<id>.ngrok.io/webhooks/sms`

## Step 4: Test It

**Health check:**

```bash
curl http://localhost:5000/health
```

Or text your Telnyx number to trigger the SMS workflow.

## Key Code

The MCP server function runs at the edge:

```python
"""MCP Server on Telnyx Edge Compute — expose Telnyx APIs (send SMS, make calls, search numbers, run inference) as MCP tools for AI agents."""
import json
import os
import logging
from urllib.request import Request, urlopen
from urllib.error import URLError

HTTP_SCOPE_TYPE = "http"
logger = logging.getLogger("mcp-server")
TELNYX_API = "https://api.telnyx.com/v2"

TOOLS = [
    {
        "name": "send_sms",
```

## Going to Production

This example uses in-memory storage for simplicity. For production:

- **Database** — replace the in-memory dict/list with PostgreSQL or Redis
- **Authentication** — add API key validation on your endpoints
- **Webhook verification** — validate Telnyx webhook signatures ([docs](https://developers.telnyx.com/docs/api/v2/overview#webhook-signing))
- **Prompt engineering** — tune the AI prompts for your specific domain and tone
- **Monitoring** — add structured logging and health check alerts
- **Rate limiting** — protect your endpoints from abuse

## Deploy

```bash

```

## Resources

- [Source code and reference](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/edge-mcp-server-deploy-python/README.md)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Messaging quickstart](https://developers.telnyx.com/docs/messaging)
- [AI Inference docs](https://developers.telnyx.com/docs/inference)
- [Telnyx Portal](https://portal.telnyx.com)
