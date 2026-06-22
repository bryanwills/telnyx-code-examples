# Receive Inbound SMS with Telnyx and Sinatra (Ruby)

Build a production-ready Sinatra server that receives inbound SMS via Telnyx webhooks
and verifies the Telnyx Ed25519 signature before trusting any payload.

## How It Works

```
  Inbound SMS
        │
        ▼
  ┌──────────────────┐
  │ Telnyx Messaging  │
  └────────┬─────────┘
           │ POST webhook (Ed25519-signed)
           ▼
  ┌─────────────────────────────┐
  │ Sinatra server              │
  │ POST /webhooks/sms          │
  │  read raw → verify sig →    │
  │  parse → read data.payload  │
  │  → store → 200 OK           │
  └─────────────────────────────┘
```

## Telnyx Products Used

- **Messaging** — send and receive messages with delivery receipts

## API Endpoints

- **Inbound Message webhook**: `POST /webhooks/sms` (your endpoint, called by Telnyx) -- [Webhook reference](https://developers.telnyx.com/docs/messaging/messages/receive-message)

## Prerequisites

- Ruby 3.2+ (the Telnyx 5.x SDK is a Stainless rewrite and Ed25519 key parsing needs OpenSSL 3.x)
- Bundler
- [Telnyx account](https://portal.telnyx.com/sign-up)
- [API key](https://portal.telnyx.com/api-keys) and the account **Ed25519 public key** (Portal → Account Settings → Keys & Credentials → Public Key)
- [Phone number](https://portal.telnyx.com/numbers/my-numbers) enabled for inbound SMS
- [Messaging Profile](https://portal.telnyx.com/messaging/profiles) with an inbound webhook URL
- [ngrok](https://ngrok.com) for exposing your local server to Telnyx webhooks

## Step 1: Set Up the Project

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/receive-sms-webhook-ruby
cp .env.example .env
bundle install
```

Edit `.env` with your Telnyx credentials. `TELNYX_API_KEY` initializes the SDK client;
`TELNYX_PUBLIC_KEY` is the base64 Ed25519 public key used to verify webhook signatures;
`PORT` controls the listen port (defaults to `5000`).

The `Gemfile` pins these gems:

```ruby
gem "telnyx", "~> 5.131"
gem "standardwebhooks", "~> 1.1"  # transitive require of the telnyx gem
gem "sinatra", "~> 4.1"
gem "ed25519", "~> 1.3"
gem "dotenv", "~> 3.1"
```

> `require "telnyx"` loads `standardwebhooks` at startup even though the SDK does not
> declare it as a runtime dependency, so it must be in the `Gemfile`.

## Step 2: Verify the Telnyx Signature

Telnyx signs every webhook with Ed25519 over the string `"<telnyx-timestamp>|<raw-body>"`.
The request carries the headers `telnyx-signature-ed25519` (base64 signature) and
`telnyx-timestamp` (unix seconds). We verify against the account's base64 Ed25519
**public** key using the native `ed25519` gem.

> Do **not** use the SDK helper `client.webhooks.unwrap` here. In the 5.x SDK it
> delegates to the Standard Webhooks spec (HMAC-SHA256 over `"<id>.<ts>.<body>"` using
> a symmetric `whsec_` secret and `webhook-*` headers), which is a different scheme and
> rejects genuine Telnyx webhooks.

```ruby
require "ed25519"
require "base64"

MAX_SKEW_SECONDS = 300

def verify_telnyx_signature(raw_body, signature, timestamp)
  public_key = ENV["TELNYX_PUBLIC_KEY"]
  return false if signature.nil? || timestamp.nil? || public_key.nil? || public_key.empty?

  # Replay protection: reject stale or future-dated timestamps.
  return false if (Time.now.to_i - timestamp.to_i).abs > MAX_SKEW_SECONDS

  verify_key = Ed25519::VerifyKey.new(Base64.decode64(public_key))
  verify_key.verify(Base64.decode64(signature), "#{timestamp}|#{raw_body}")
rescue Ed25519::VerifyError, ArgumentError
  false
end
```

`Ed25519::VerifyKey#verify` returns `true` on success and raises `Ed25519::VerifyError`
on a bad signature (or `ArgumentError` on a wrong-length signature/key), which we treat
as a failed verification.

## Step 3: Handle the Webhook

Sinatra exposes the unmodified request body via `request.body.read`, which is exactly
what Ed25519 verification needs — a body parser must not consume the stream first.
Read the message fields from `data.payload` only **after** the signature passes.

```ruby
post "/webhooks/sms" do
  raw_body  = request.body.read
  signature = request.env["HTTP_TELNYX_SIGNATURE_ED25519"]
  timestamp = request.env["HTTP_TELNYX_TIMESTAMP"]

  # ENFORCE-ALWAYS: verify before parsing/trusting.
  unless verify_telnyx_signature(raw_body, signature, timestamp)
    halt 401, json_response(error: "invalid signature")
  end

  begin
    event = JSON.parse(raw_body)
  rescue JSON::ParserError
    halt 400, json_response(error: "Invalid webhook payload")
  end

  if event.dig("data", "event_type") == "message.received"
    message = process_inbound_sms(event)
    RECEIVED_MESSAGES << message
    status 200
    json_response(success: true, message_id: message[:message_id], status: "received")
  else
    status 200
    json_response(success: true, status: "ignored")
  end
end
```

Header names arrive in Rack's `request.env` as `HTTP_TELNYX_SIGNATURE_ED25519` and
`HTTP_TELNYX_TIMESTAMP`.

The fields are pulled out of `data.payload`:

```ruby
def process_inbound_sms(event)
  payload = event.dig("data", "payload")
  raise ArgumentError, "Invalid webhook payload structure" if payload.nil?

  message = {
    message_id: payload["id"],
    from: payload.dig("from", "phone_number"),
    to: payload.dig("to", 0, "phone_number"),
    text: payload["text"] || "",
    received_at: payload["received_at"] || Time.now.utc.iso8601,
    direction: payload["direction"] || "inbound"
  }

  if message[:from].nil? || message[:to].nil?
    raise ArgumentError, "Missing sender or recipient phone number in webhook"
  end

  message
end
```

See [`app.rb`](./app.rb) for the complete implementation, including the `/messages`
debug endpoint, `/health` check, and the generic 500 error handler that logs internally
without leaking exception details.

## Step 4: Run It

```bash
bundle exec ruby app.rb
```

The server starts on `http://localhost:5000` (or `PORT` if set).

In a separate terminal, expose your server for webhooks:

```bash
ngrok http 5000
```

Copy the HTTPS URL and set it in the [Telnyx Portal](https://portal.telnyx.com):

- **Messaging Profile** → Inbound Settings → Webhook URL → `https://<id>.ngrok.io/webhooks/sms`

Then assign your inbound-enabled number to that Messaging Profile.

## Step 5: Test It

**Health check:**

```bash
curl http://localhost:5000/health
```

**Real inbound test:** text your Telnyx number from a phone and watch the server log the
inbound message. Because the endpoint enforces signature verification, a plain `curl`
POST (with no Telnyx signature) is correctly rejected with `401` — that is the security
working, not a bug. To exercise the handler end-to-end, send a real message through your
Telnyx number, or temporarily generate a valid Ed25519 signature in a test harness.

**View what was received:**

```bash
curl http://localhost:5000/messages
```

## Going to Production

This example uses in-memory storage for simplicity. For production:

- **Database** — replace the in-memory `RECEIVED_MESSAGES` array with PostgreSQL or Redis
- **Authentication** — restrict the `/messages` debug endpoint or remove it
- **Fast acknowledgment** — respond `200` immediately and move heavy work (DB writes, downstream calls) to a background queue so you stay under the 5-second window
- **Monitoring** — add structured logging and health check alerts

## Resources

- [Source code and reference](./README.md)
- [Receive a Message guide](https://developers.telnyx.com/docs/messaging/messages/receive-message)
- [Ruby SDK](https://developers.telnyx.com/development/sdk/ruby)
- [Telnyx Portal](https://portal.telnyx.com)
