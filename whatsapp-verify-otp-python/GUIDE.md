# WhatsApp OTP Verification with Telnyx

Send and verify one-time passwords via WhatsApp using the Telnyx Verify API.

## How It Works

```
  User requests OTP
        │
        ▼
  ┌────────────────────┐
  │  Python Server     │  receives request
  └─────────┬──────────┘
        │  Telnyx Verify API
        │  type: "whatsapp"
        ▼
  ┌────────────────────┐
  │  Telnyx Verify     │  sends OTP via WhatsApp
  └─────────┬──────────┘
        │
        ▼
  ┌────────────────────┐
  │  User enters code  │  submits OTP
  └─────────┬──────────┘
        │
        ▼
  ┌────────────────────┐
  │  Code verified     │  ✓ or ✗
  └────────────────────┘
```

## Telnyx Products Used

- **Verify** — phone verification with OTP delivery via WhatsApp ([Documentation](https://developers.telnyx.com/docs/identity/verify/quickstart))

## Prerequisites

- Python 3.8+
- A [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- An [API key](https://portal.telnyx.com/api-keys)
- A [Verify Profile](https://portal.telnyx.com/verify/profiles) configured with the WhatsApp channel
- A WhatsApp Business Account (WABA) linked to your Telnyx account
- [ngrok](https://ngrok.com) for webhook testing

## Step 1: Set Up the Project

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/whatsapp-verify-otp-python
cp .env.example .env
pip install -r requirements.txt
```

Edit `.env` with your Telnyx credentials:

| Variable | Description |
|----------|-------------|
| `TELNYX_API_KEY` | Your Telnyx API v2 key from [Portal](https://portal.telnyx.com/api-keys) |
| `VERIFY_PROFILE_ID` | Your Verify Profile ID with WhatsApp enabled from [Portal](https://portal.telnyx.com/verify/profiles) |
| `PORT` | HTTP server port (default: 5000) |

## Step 2: Configure WhatsApp for Verify

1. **Link your WABA** — In the [Telnyx Portal](https://portal.telnyx.com), connect your WhatsApp Business Account under the WhatsApp section.
2. **Create a Verify Profile** — Go to [Verify Profiles](https://portal.telnyx.com/verify/profiles) and create a new profile.
3. **Enable WhatsApp channel** — In your Verify Profile settings, enable WhatsApp as a delivery channel.
4. **Set the webhook URL** — Configure the webhook URL to point to your `/webhooks/verify` endpoint.

## Step 3: Understand the Code

The main application logic lives in `app.py`.

### Starting a Verification

**`start_verification()`** — Sends a WhatsApp OTP to the given phone number via the Telnyx Verify API with `type: "whatsapp"`.

```python
resp = requests.post("https://api.telnyx.com/v2/verifications",
    headers={"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"},
    json={"phone_number": phone, "verify_profile_id": VERIFY_PROFILE_ID, "type": "whatsapp"}, timeout=10)
```

### Checking the Code

**`check_verification()`** — Submits the user-entered OTP code for validation against the Telnyx Verify API.

### Receiving Webhooks

**`verify_webhook()`** — Handles delivery status webhooks (`verify.sent`, `verify.delivered`, `verify.completed`, `verify.failed`) for real-time tracking.

### All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/verify/start` | Send WhatsApp OTP |
| `POST` | `/verify/check` | Verify submitted code |
| `POST` | `/webhooks/verify` | Receive delivery webhooks |
| `GET` | `/health` | Health check |

## Step 4: Run It

```bash
python app.py
```

The server starts on `http://localhost:5000`.

For webhook-based features, expose your local server:

```bash
ngrok http 5000
```

Copy the HTTPS URL and set it as the webhook URL in your [Verify Profile](https://portal.telnyx.com/verify/profiles).

## Step 5: Test It

**Health check:**

```bash
curl http://localhost:5000/health
```

**Send an OTP:**

```bash
curl -X POST http://localhost:5000/verify/start \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+12125551234"}'
```

**Verify the code:**

```bash
curl -X POST http://localhost:5000/verify/check \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+12125551234", "code": "12345"}'
```

## Going to Production

- **Database** — replace the in-memory dict with PostgreSQL or Redis for verification state.
- **Authentication** — add API key validation on your endpoints.
- **Webhook verification** — validate Telnyx webhook signatures ([docs](https://developers.telnyx.com/docs/api/v2/overview#webhook-signing)).
- **Monitoring** — add structured logging and health check alerts.
- **Rate limiting** — protect your endpoints from abuse.
- **Fallback channels** — consider adding SMS or voice fallback if WhatsApp delivery fails.

## Resources

- [Source code](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/whatsapp-verify-otp-python/README.md)
- [API reference](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/whatsapp-verify-otp-python/API.md)
- [Verify API Documentation](https://developers.telnyx.com/docs/identity/verify/quickstart)
- [Telnyx Portal](https://portal.telnyx.com)
