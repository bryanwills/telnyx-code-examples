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
    ├─ call.initiated (incoming) ──► Answer Call
    │
    ├─ call.answered ──► speak() greeting ("Hello, how can I help?")
    │
    ├─ call.speak.ended (stage=greeting) ──► gather_using_ai (capture caller speech)
    │
    ├─ call.ai_gather.ended ──► Classify Intent (AI Inference API)
    │                              │
    │                              ▼
    │                         speak() announcement ("Transferring you to billing…")
    │                              │
    │                              ▼
    │                         call.speak.ended (stage=announcing) ──► transfer() to route destination
    │
    └─ call.ai_gather.failed ──► Fallback announcement + transfer to default destination
```

### How transfers work

This example uses `client.calls.actions.transfer()` — a **blind bridge**: Telnyx dials the
destination number from `ROUTE_TABLE`, and when the destination answers, the two legs are
connected. The caller hears the spoken announcement ("Transferring you to billing. Please
hold.") on the **original leg**, then the bridge connects. The **transferred leg does not
receive a greeting or TTS** — it is simply bridged to the original call. This is standard
Call Control transfer behavior.

To customize routing destinations, edit `ROUTE_TABLE` in `app.py`:

```python
ROUTE_TABLE = {
    "billing": "+1XXXXXXXXXX",   # replace with your billing queue number
    "sales": "+1XXXXXXXXXX",     # replace with your sales queue number
    "support": "+1XXXXXXXXXX",   # replace with your support queue number
}
```

**Tips for testing locally:**
- Set all destinations to your own cell phone to verify the full flow end-to-end. You'll hear
  the announcement on the original leg, then your cell rings and bridges you back to the
  original call (you'll be talking to yourself — expected for a single-phone demo).
- To hear a greeting on the **transferred leg** (e.g. "You've reached billing"), replace the
  `transfer()` call with a `dial` to a Telnyx number mapped to a separate Call Control
  application that plays its own greeting, or use `transfer()` with a `webhook_url` pointing
  to a handler that speaks before bridging.
- In production, destinations would be separate people, queues, or PBX extensions — not your
  own cell. The caller hears the other end pick up naturally after the announcement.

## Environment Variables

| Variable | Type | Example | Required | Description | Where to get it |
|----------|------|---------|----------|-------------|-----------------|
| `PORT` | `string` | `5000` | no | Port for the Flask server | — |
| `TELNYX_API_KEY` | `string` | `your_telnyx_api_key_here` | **yes** | Telnyx API key (Mission Control → API Keys) | [API Keys](https://portal.telnyx.com/#/app/api-keys) |
| `TELNYX_PUBLIC_KEY` | `string` | `your_telnyx_public_key_here` | **yes** | Telnyx Ed25519 public key for webhook signature verification (`GET /v2/public_key`) | [Webhooks](https://developers.telnyx.com/docs/api/v2/overview#webhooks) |
| `TELNYX_CONNECTION_ID` | `string` | `your_call_control_application_id_here` | **yes** | Call Control Application ID (webhook events are routed here) | [Call Control Apps](https://portal.telnyx.com/#/app/call-control-applications) |
| `AI_MODEL` | `string` | `meta-llama/Llama-3.3-70B-Instruct` | no | Telnyx-hosted AI Inference model used for intent classification (no OpenAI key needed) | [AI Inference](https://developers.telnyx.com/docs/api/ai/ai-inference) |

> **Agent / CLI access** — provision the resources above with the Telnyx CLI:
>
> ```bash
> # API key + public key
> telnyx whoami
> curl -H "Authorization: Bearer $TELNYX_API_KEY" https://api.telnyx.com/v2/public_key | jq -r .data.public
>
> # Call Control Application (webhook URL → TELNYX_CONNECTION_ID)
> telnyx connection list                                   # see existing
> curl -X POST https://api.telnyx.com/v2/call_control_applications \
>   -H "Authorization: Bearer $TELNYX_API_KEY" \
>   -d '{"application_name":"ai-powered-call-router","active":true,"webhook_event_url":"https://YOUR-TUNNEL/webhook","webhook_api_version":"2","outbound":{"outbound_voice_profile_id":"YOUR_PROFILE_ID"}}'
>
> # Phone number → Call Control Application
> telnyx number list
> telnyx number update +1XXXXXXXXXX --connection-id YOUR_CONNECTION_ID
>
> # AI Inference models (Telnyx-hosted, no OpenAI key needed)
> curl -H "Authorization: Bearer $TELNYX_API_KEY" https://api.telnyx.com/v2/ai/openai/models | jq '.data[] | select(.owned_by=="Telnyx") | .id'
> ```

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
TELNYX_CONNECTION_ID=your_call_control_application_id_here
AI_MODEL=meta-llama/Llama-3.3-70B-Instruct
PORT=5000
```

**Provisioning the Telnyx resources** (if starting from scratch):

```bash
# 1. Get your Ed25519 public key for webhook verification
curl -H "Authorization: Bearer $TELNYX_API_KEY" https://api.telnyx.com/v2/public_key | jq -r .data.public
# → set as TELNYX_PUBLIC_KEY in .env

# 2. Expose your local server publicly (cloudflared quick tunnel — no account needed)
cloudflared tunnel --url http://localhost:5000
# → note the https://*.trycloudflare.com URL

# 3. Create a Call Control Application with that webhook URL
curl -s -X POST "https://api.telnyx.com/v2/call_control_applications" \
  -H "Authorization: Bearer $TELNYX_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "application_name": "ai-powered-call-router",
    "active": true,
    "webhook_event_url": "https://YOUR-TUNNEL.trycloudflare.com/webhook",
    "webhook_api_version": "2",
    "outbound": { "outbound_voice_profile_id": "YOUR_OUTBOUND_VOICE_PROFILE_ID" }
  }' | jq -r .data.id
# → set as TELNYX_CONNECTION_ID in .env

# 4. Map a Telnyx phone number to the Call Control Application
curl -s -X PATCH "https://api.telnyx.com/v2/phone_numbers/+1XXXXXXXXXX" \
  -H "Authorization: Bearer $TELNYX_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"connection_id": "YOUR_CALL_CONTROL_APPLICATION_ID"}'
```

<details>
<summary>Programmatic / CLI setup</summary>

```bash
# List existing connections / numbers / voice profiles
telnyx connection list
telnyx number list
telnyx voice-profile list

# Get your public key (alternative to the curl call above)
telnyx whoami   # shows account info; public key via API: curl /v2/public_key

# Map a number to a Call Control Application (alternative to PATCH)
telnyx number update +1XXXXXXXXXX --connection-id YOUR_CONNECTION_ID
```

</details>

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
| Webhook returns 401 | Invalid or missing Telnyx public key | Verify `TELNYX_PUBLIC_KEY` matches your Telnyx account's public key (`GET /v2/public_key`) |
| Calls not answered | Webhook URL not reachable | Ensure your server is publicly accessible (use `cloudflared tunnel` or ngrok for local dev) |
| Gather fails with `90012 Invalid value for voice` | `gather_using_ai` uses a different voice set than `speak()` | Do not pass `voice` to `gather_using_ai` — play greetings via `speak(voice="female")` instead. See `app.py:play_greeting` vs `start_gather`. |
| Gather times out | Caller didn't speak within timeout | Adjust `user_response_timeout_ms` in `start_gather()` or check audio settings |
| Intent always returns "support" | AI Inference API error | Check `TELNYX_API_KEY` and verify AI Inference access on your account |
| Transfer fails | Invalid destination number | Ensure `ROUTE_TABLE` destinations are valid E.164 phone numbers |
| Transferred leg is silent on answer | Expected — `transfer()` is a blind bridge | The announcement plays on the original leg; the transferred leg is bridged without TTS. See "How transfers work" above. |
| App re-answers the transfer leg (loop) | Handler not filtering outbound legs | Only `call.initiated` with `direction == "incoming"` enters `CALL_STATE`; other events are gated on `call_control_id in CALL_STATE`. |
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
