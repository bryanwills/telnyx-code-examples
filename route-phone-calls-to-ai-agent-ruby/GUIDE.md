# Guide: Route inbound phone calls to a Telnyx AI assistant with Ruby

This walkthrough builds a Sinatra webhook receiver that handles Telnyx Call
Control events, verifies their Ed25519 signatures, and routes answered calls
into a Telnyx AI assistant. Every snippet matches `app.rb`.

## What you'll build

```
Inbound call → Telnyx Call Control → POST /webhooks/voice (your Sinatra app)
   → verify signature → answer the call → start the AI assistant
```

## Prerequisites

- Ruby **3.2+** (the Telnyx SDK does not support macOS system Ruby 2.6). Install via `rbenv`/`asdf`.
- A Telnyx account with an API key, your account's base64 Ed25519 **Public Key**, and an **AI assistant**.
- A way to expose `localhost` publicly (e.g. ngrok).

## Step 1 — Project dependencies

The Telnyx Ruby SDK is v5.x — a Stainless rewrite with an instance-client API.
It requires `standardwebhooks` at load time even though the gem does not declare
it, so we pin it explicitly. We verify webhook signatures with the native
`ed25519` gem (the SDK's `webhooks.unwrap` is the Standard Webhooks scheme, not
Telnyx's Ed25519 scheme, so it cannot verify real Telnyx webhooks).

```ruby
# Gemfile
source "https://rubygems.org"

ruby ">= 3.2"

gem "telnyx", "~> 5.131"
gem "sinatra", "~> 4.1"
gem "puma", "~> 6.4"
gem "dotenv", "~> 3.1"
gem "ed25519", "~> 1.3"
gem "standardwebhooks", "~> 1.1"
```

```bash
bundle install
```

## Step 2 — Configuration and the Telnyx client

Load environment variables and create the client once per process (it is
thread-safe and owns its own connection pool).

```ruby
require "sinatra"
require "telnyx"
require "ed25519"
require "base64"
require "json"
require "logger"
require "dotenv/load"

MAX_SKEW_SECONDS = 300
LOGGER = Logger.new($stdout)

TELNYX = Telnyx::Client.new(api_key: ENV["TELNYX_API_KEY"])
ASSISTANT_ID = ENV["TELNYX_ASSISTANT_ID"]
```

Decode the base64 Ed25519 public key once into a verify key:

```ruby
def telnyx_verify_key
  encoded = ENV["TELNYX_PUBLIC_KEY"]
  return nil if encoded.nil? || encoded.empty?

  Ed25519::VerifyKey.new(Base64.decode64(encoded))
rescue StandardError => e
  LOGGER.error("Failed to load TELNYX_PUBLIC_KEY: #{e.class}")
  nil
end

VERIFY_KEY = telnyx_verify_key
```

## Step 3 — Verify the webhook signature

Telnyx signs `"<telnyx-timestamp>|<raw body>"` with Ed25519. Verify the **raw**
body (never a re-serialized parse) and reject stale timestamps to block replays.

```ruby
def verified_telnyx_webhook?(raw_body, signature_b64, timestamp)
  return false if VERIFY_KEY.nil?
  return false if signature_b64.nil? || signature_b64.empty?
  return false if timestamp.nil? || timestamp.empty?
  return false if (Time.now.to_i - timestamp.to_i).abs > MAX_SKEW_SECONDS

  signed_payload = "#{timestamp}|#{raw_body}"
  VERIFY_KEY.verify(Base64.decode64(signature_b64), signed_payload)
  true
rescue Ed25519::VerifyError, ArgumentError
  false
end
```

`VerifyKey#verify` returns `true` on success and raises `Ed25519::VerifyError`
(or `ArgumentError` for a wrong-length signature) otherwise — both are treated
as a failed verification.

## Step 4 — Route the call

Two small helpers wrap the Call Control commands. In v5.x these live under
`client.calls.actions` and take the `call_control_id` as the first positional
argument.

```ruby
def answer_call(call_control_id)
  TELNYX.calls.actions.answer(call_control_id)
end

def start_ai_assistant(call_control_id)
  return if ASSISTANT_ID.nil? || ASSISTANT_ID.empty?

  TELNYX.calls.actions.start_ai_assistant(
    call_control_id,
    assistant: { id: ASSISTANT_ID }
  )
end
```

## Step 5 — The webhook route

Read the raw body and the `telnyx-*` headers (Rack exposes them as
`HTTP_TELNYX_SIGNATURE_ED25519` / `HTTP_TELNYX_TIMESTAMP`). Verify first, then
parse, then dispatch on `data.event_type` reading fields from `data.payload`.

```ruby
post "/webhooks/voice" do
  raw_body  = request.body.read
  signature = request.env["HTTP_TELNYX_SIGNATURE_ED25519"]
  timestamp = request.env["HTTP_TELNYX_TIMESTAMP"]

  unless verified_telnyx_webhook?(raw_body, signature, timestamp)
    halt 401, json_response(error: "invalid signature")
  end

  begin
    event = JSON.parse(raw_body)
  rescue JSON::ParserError
    halt 400, json_response(error: "invalid JSON")
  end

  data            = event["data"] || {}
  event_type      = data["event_type"]
  payload         = data["payload"] || {}
  call_control_id = payload["call_control_id"]

  begin
    case event_type
    when "call.initiated"
      answer_call(call_control_id) if payload["direction"] == "incoming"
    when "call.answered"
      start_ai_assistant(call_control_id)
    when "call.hangup"
      LOGGER.info("Call #{call_control_id} ended (#{payload['hangup_cause']})")
    end
  rescue Telnyx::Errors::AuthenticationError
    LOGGER.error("Telnyx authentication failed (check TELNYX_API_KEY)")
  rescue Telnyx::Errors::APIStatusError => e
    LOGGER.error("Telnyx API error (HTTP #{e.status})")
  rescue Telnyx::Errors::APIError
    LOGGER.error("Unexpected Telnyx API error")
  end

  status 200
  json_response(status: "ok")
end
```

Note the flow: a fresh inbound call fires `call.initiated`, which we answer;
answering fires `call.answered`, where we start the assistant. Always return
`200` after processing so Telnyx does not retry an event you handled.

## Step 6 — Run it

```bash
cp .env.example .env   # fill in TELNYX_API_KEY, TELNYX_PUBLIC_KEY, TELNYX_ASSISTANT_ID
bundle install
ruby app.rb            # http://localhost:4567
```

Expose it and point your Call Control Application's webhook URL at
`https://<subdomain>.ngrok.io/webhooks/voice`, assign your inbound number to
that application, then place a call to the number.

## Production notes

- **Never** disable signature verification. Reject anything that fails it with `401`.
- Read event fields from `data.payload` only after verification succeeds.
- Catch `Telnyx::Errors::*` and log generic messages — do not leak exception
  details into HTTP responses.
- Keep returning `200` quickly; do heavy work asynchronously if needed so Telnyx
  does not time out and retry.
