---
name: sms-two-factor-agent
title: "SMS Two-Factor Authentication Agent"
description: "Agent-managed SMS two-factor authentication with code generation, KV storage, and scheduled expiry."
language: typescript
framework: edge
telnyx_products: [SMS, Verify, Agent SDK]
---

# SMS Two-Factor Authentication Agent

An Edge-based agent that manages the full lifecycle of SMS two-factor authentication codes — generation, delivery via Telnyx SMS, verification, and automatic expiry using scheduled tasks.

## Why Telnyx

Telnyx provides the AI Communications Infrastructure that powers programmable SMS, voice, and verification workflows with low-latency global delivery. By combining the Telnyx Edge Agent SDK with the native `[telnyx]` binding, this sample demonstrates zero-credential API access to Telnyx messaging services directly from the edge runtime, enabling secure, scalable authentication flows without managing API keys in application code.

## Telnyx API Endpoints Used

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/v2/messages` | POST | Send SMS verification codes via `this.env.TELNYX.messages.send()` |
| Telnyx Edge `[telnyx]` binding | — | Zero-credential access to Telnyx messaging from Edge runtime |

## Architecture

```
┌──────────────┐     POST /verify      ┌─────────────────────┐
│   Client     │ ──────────────────── │   TwoFactorAgent    │
│  (Web/App)   │                       │  (extends Agent)    │
└──────────────┘                       └──────────┬──────────┘
                                                  │
                                    ┌─────────────┼─────────────┐
                                    ▼             ▼               ▼
                              ┌─────────┐  ┌───────────┐  ┌──────────────┐
                              │   KV    │  │ StateStore│  │  Telnyx SMS  │
                              │ (TTL    │  │ (Attempts)│  │  (via env    │
                              │  300s)  │  │           │  │  binding)   │
                              └────┬────┘  └───────────┘  └──────┬──────┘
                                   │                           │
                                   │    ┌──────────────────────┘
                                   │    │
                                   ▼    ▼
                              ┌─────────────┐
                              │  User Phone │
                              │   receives  │
                              │  SMS code   │
                              └──────┬──────┘
                                     │
                                     ▼
                              POST /verify/code
                                     │
                                     ▼
                              ┌─────────────────────┐
                              │   TwoFactorAgent    │
                              │  verify against KV  │
                              │  schedule cleanup   │
                              └─────────────────────┘
```

**Flow:**
1. Client requests verification for a phone number
2. Agent generates a 6-digit code and stores it in KV with a 5-minute TTL
3. Agent sends the code via Telnyx SMS using the zero-credential `[telnyx]` binding
4. User receives SMS and submits the code
5. Agent verifies the code against KV, tracks attempts in StateStore
6. Agent schedules cleanup of expired codes via `this.schedule()`

## Environment Variables

| Variable | Type | Example | Required | Description | Where to get it |
|----------|------|---------|----------|-------------|-----------------|
| `TELNYX_API_KEY` | `string` | `your_telnyx_api_key_here` | **yes** | TELNYX_API_KEY | — |

## Setup

### Prerequisites

- Node.js 18+ and npm
- A Telnyx account with an SMS-enabled number
- Telnyx Edge runtime (or local Edge simulator)

### Local Development

```bash
# Clone the repository
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/sms-two-factor-agent

# Copy environment template
cp .env.example .env

# Edit .env and add your Telnyx API key
# TELNYX_API_KEY=your_telnyx_api_key_here

# Install dependencies
npm install

# Run in demo mode (no real SMS sent — codes logged to console)
npm run dev

# Run in live mode (sends real SMS via Telnyx)
TELNYX_LIVE_MODE=true npm run dev
```

### Project Structure

```
sms-two-factor-agent/
├── src/
│   └── index.ts          # Main entry — TwoFactorAgent + routes
├── package.json
├── tsconfig.json
├── .env.example
├── .gitignore
├── smoke_test.ts
├── README.md
├── API.md
└── GUIDE.md
```

## API Reference

### POST `/verify`

Initiate SMS two-factor authentication for a phone number.

**Request:**
```json
{
  "phone": "+15551234567"
}
```

**Response (200):**
```json
{
  "status": "code_sent",
  "phone": "+15551234567",
  "expires_in": 300
}
```

**Response (429):**
```json
{
  "error": "rate_limited",
  "message": "Too many attempts. Please wait before retrying."
}
```

---

### POST `/verify/code`

Verify the SMS code submitted by the user.

**Request:**
```json
{
  "phone": "+15551234567",
  "code": "123456"
}
```

**Response (200):**
```json
{
  "status": "verified",
  "phone": "+15551234567"
}
```

**Response (401):**
```json
{
  "error": "invalid_code",
  "attempts_remaining": 2
}
```

**Response (410):**
```json
{
  "error": "code_expired",
  "message": "Verification code has expired. Please request a new code."
}
```

---

### GET `/health`

Health check endpoint.

**Response (200):**
```json
{
  "status": "ok",
  "agent": "TwoFactorAgent"
}
```

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| SMS not received in demo mode | Demo mode logs codes instead of sending | Check console output for the generated code |
| `TELNYX_API_KEY` not found | `.env` file missing or not loaded | Copy `.env.example` to `.env` and add your key |
| `KV put failed` | KV namespace not bound | Ensure KV is configured in your Edge deployment |
| Rate limit triggered | More than 3 attempts in 60 seconds | Wait 60 seconds or increase `MAX_ATTEMPTS` in config |
| Code expired | TTL of 300 seconds elapsed | Request a new code via `POST /verify` |
| `schedule()` not firing | Agent SDK not properly initialized | Verify `TwoFactorAgent extends Agent` and runtime supports scheduling |

## Agent Discovery

- **Agent Signup:** [telnyx.com/agent-signup.md](https://telnyx.com/agent-signup.md)
- **Telnyx AI GitHub:** [github.com/team-telnyx/ai](https://github.com/team-telnyx/ai)
- **LLMs.txt:** [llms.txt](https://telnyx.com/llms.txt)

## Related Examples

- [sms-verification](../sms-verification) — Basic SMS verification without agent lifecycle
- [call-control-agent](../call-control-agent) — Agent-managed call control flows
- [webhook-inbound-sms](../webhook-inbound-sms) — Handling inbound SMS webhooks

## Resources

- [Telnyx Developer Docs](https://developers.telnyx.com/docs)
- [Telnyx Messaging API Reference](https://developers.telnyx.com/api/messaging)
- [Telnyx Edge SDK](https://github.com/team-telnyx/edge-sdk)
- [Telnyx Verify Product Page](https://telnyx.com/products/verify)
- [Telnyx Pricing](https://telnyx.com/pricing)
- [Telnyx Agent SDK Documentation](https://developers.telnyx.com/docs/agent-sdk)
