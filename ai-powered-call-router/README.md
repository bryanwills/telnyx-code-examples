---
name: ai-powered-call-router
title: "AI-Powered Call Router"
description: "Route inbound calls by analyzing caller intent with LLM classification and transferring to the correct queue."
language: python
framework: flask
telnyx_products: [Call Control, AI Inference API, Agent SDK]
---

# AI-Powered Call Router

Route inbound calls dynamically by analyzing caller intent with the Telnyx AI Inference API — "I need to pay my bill" → billing queue, "I want to upgrade" → sales queue.

## Why Telnyx

Telnyx provides a comprehensive AI Communications Infrastructure platform that bridges voice, messaging, and artificial intelligence. By combining Call Control for programmatic voice routing with the AI Inference API for intent classification, developers can build intelligent telephony applications that adapt to caller needs in real-time without managing separate telephony and AI providers.

## Telnyx API Endpoints Used

- **Call Control** — `telnyx.Call.answer()`, `telnyx.Call.gather_using_speech()`, `telnyx.Call.playback_start()`, `telnyx.Call.transfer()`
- **AI Inference API** — `telnyx.ai.openai.chat.create_completion()` for intent classification
- **Webhook Verification** — `telnyx.Webhook.unwrap()` for Ed25519 signature verification

## Architecture

```
Inbound Call
    │
    ▼
Telnyx Call Control (Webhook)
    │
    ▼
Flask Webhook Handler (/webhook)
    │
    ├─ call.initiated ──► Answer Call
    │
    ├─ call.answered ──► Play Greeting + Gather Speech
    │
    ├─ call.gather.ended ──► Classify Intent (AI Inference)
    │                            │
    │                            ▼
    │                       KV Route Table Lookup
    │                            │
    │                            ▼
    │                       Transfer Call to Destination
    │
    └─ call.gather.failed ──► Fallback Transfer (Default Queue)
```

## Environment Variables

| Variable | Type | Example | Required | Description | Where to get it |
|----------|------|---------|----------|-------------|-----------------|
| `PORT` | `string` | `your_port_here` | **yes** | PORT | — |
| `TELNYX_API_KEY` | `string` | `your_telnyx_api_key_here` | **yes** | TELNYX_API_KEY | — |
| `TELNYX_CONNECTION_ID` | `string` | `your_telnyx_connection_id_here` | **yes** | TELNYX_CONNECTION_ID | — |
| `TELNYX_PUBLIC_KEY` | `string` | `your_telnyx_public_key_here` | **yes** | TELNYX_PUBLIC_KEY | — |

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/ai-powered-call-router
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and add your Telnyx credentials:

```
TELNYX_API_KEY=your_telnyx_api_key_here
TELNYX_PUBLIC_KEY=your_telnyx_public_key_here
TELNYX_CONNECTION_ID=your_telnyx_connection_id_here
PORT=5000
```

### 5. Run the application

```bash
python app.py
```

### 6. Configure the webhook

Point your Telnyx Call Control application's webhook URL to your public endpoint:

```
https://your-domain.com/webhook
```

Use a tool like ngrok for local development:

```bash
ngrok http 5000
```

## API Reference

See [API.md](./API.md) for the full endpoint reference including request/response shapes and status codes.

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Webhook returns 401 | Invalid or missing Telnyx public key | Verify `TELNYX_PUBLIC_KEY` matches your Telnyx account's public key |
| Calls not answered | Webhook URL not reachable | Ensure your server is publicly accessible (use ngrok for local dev) |
| Gather times out | Caller didn't speak within timeout | Adjust `timeout_millis` in `gather_speech()` or check audio settings |
| Intent always returns "support" | AI Inference API error | Check `TELNYX_API_KEY` and verify AI Inference access on your account |
| Transfer fails | Invalid destination number | Ensure `ROUTE_TABLE` destinations are valid E.164 phone numbers |
| Signature verification fails | Timestamp skew or replay | Ensure server time is synced (NTP) and requests arrive within the timestamp window |

## Agent Discovery

- [Agent Signup](https://telnyx.com/agent-signup.md)
- [Team Telnyx AI on GitHub](https://github.com/team-telnyx/ai)
- [llms.txt](https://telnyx.com/llms.txt)

## Related Examples

- [Call Control Quickstart](https://github.com/team-telnyx/telnyx-code-examples) — Basic inbound call handling
- [IVR Menu System](https://github.com/team-telnyx/telnyx-code-examples) — DTMF-based call routing
- [AI Voice Assistant](https://github.com/team-telnyx/telnyx-code-examples) — Two-way AI conversation with Call Control

## Resources

- [Telnyx Developer Docs](https://developers.telnyx.com/docs)
- [Call Control API Reference](https://developers.telnyx.com/docs/api/v2/call-control)
- [AI Inference API Reference](https://developers.telnyx.com/docs/api/ai/ai-inference)
- [Telnyx Python SDK](https://github.com/team-telnyx/telnyx-python)
- [Call Control Product Page](https://telnyx.com/products/call-control)
- [Telnyx Pricing](https://telnyx.com/pricing)
