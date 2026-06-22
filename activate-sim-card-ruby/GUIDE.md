# Activate a Telnyx SIM Card with Ruby

Activate (enable) a Telnyx IoT SIM card over HTTP using the Telnyx Ruby SDK and Sinatra, and optionally confirm the transition with a signature-verified webhook.

## How It Works

```
  POST /sim/activate
        │
        ▼
  ┌────────────────────────┐
  │   Sinatra handler       │
  │  (validate JSON body)   │
  └───────────┬────────────┘
              │ client.sim_cards.actions.enable(id)
              ▼
  ┌────────────────────────┐
  │   Telnyx IoT SIM API    │
  └───────────┬────────────┘
              │  enable is asynchronous
              └──► SIM transitions toward "enabled"
```

## Telnyx Products Used

- **IoT SIM** — provision and activate cellular SIM cards over the API.

## API Endpoints

- **Enable SIM Card**: `POST /v2/sim_cards/{id}/actions/enable` — [API reference](https://developers.telnyx.com/api-reference/sim-cards/enable-sim-card)

## Prerequisites

- Ruby 3.2+ (the Telnyx 5.x SDK does not support older versions).
- [Telnyx account](https://portal.telnyx.com/sign-up).
- [API key](https://portal.telnyx.com/api-keys).
- At least one SIM card in your account that belongs to a SIM card group (IoT → SIM Cards).
- The SIM card ID (UUID), found in the [Telnyx Portal](https://portal.telnyx.com) under IoT → SIM Cards.

## Step 1: Set Up the Project

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/activate-sim-card-ruby
cp .env.example .env
bundle install
```

Edit `.env` and set `TELNYX_API_KEY` to the key shown in the [Telnyx Portal](https://portal.telnyx.com/api-keys). Set `TELNYX_PUBLIC_KEY` only if you plan to receive webhooks on `/webhooks/sim`.

> The `Gemfile` explicitly pins `standardwebhooks` because `require "telnyx"` loads it at startup even though the gem does not declare it as a runtime dependency. Without it, the SDK fails to load.

## Step 2: Understand the Code

Everything lives in `app.rb`.

### Client Initialization

The app reads `TELNYX_API_KEY`, raises if it is missing, and creates the SDK client once per process:

```ruby
API_KEY = ENV["TELNYX_API_KEY"]
raise "TELNYX_API_KEY environment variable not set" if API_KEY.nil? || API_KEY.empty?

CLIENT = Telnyx::Client.new(api_key: API_KEY)
```

### Activation Helper

`activate_sim` calls the SDK and unpacks the typed response into a plain hash (SDK model objects are not directly JSON-serializable):

```ruby
def activate_sim(sim_card_id)
  response = CLIENT.sim_cards.actions.enable(sim_card_id)
  action = response.data
  {
    id: action.id,
    status: action.status,
    action_type: action.action_type,
    sim_card_id: action.sim_card_id
  }
end
```

`client.sim_cards.actions.enable(id)` POSTs to `/v2/sim_cards/{id}/actions/enable`. Note the nested `.actions` resource — there is no `client.sim_cards.activate`.

### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/sim/activate` | Enable a SIM card by ID |
| `POST` | `/webhooks/sim` | Receive + verify SIM status webhooks |

The activate handler validates the JSON body, calls the helper, and maps SDK errors (namespaced under `Telnyx::Errors::`) to HTTP statuses without leaking exception details:

```ruby
rescue Telnyx::Errors::AuthenticationError
  halt 401, { error: "Invalid API key" }.to_json
rescue Telnyx::Errors::RateLimitError
  halt 429, { error: "Rate limit exceeded. Please slow down." }.to_json
rescue Telnyx::Errors::APIStatusError => e
  logger.error("Telnyx API error: #{e.class} status=#{e.status}")
  upstream = e.status.to_i
  upstream = 502 unless (400..599).cover?(upstream)
  halt upstream, { error: "Telnyx API returned an error", status_code: e.status }.to_json
rescue Telnyx::Errors::APIConnectionError
  halt 503, { error: "Network error connecting to Telnyx" }.to_json
```

The HTTP status accessor on `APIStatusError` is `e.status` (an Integer), not `status_code`.

### Webhook Signature Verification

Telnyx signs webhooks with Ed25519 over `"<telnyx-timestamp>|<raw-body>"`. We verify natively with the `ed25519` gem **before** parsing the body, and read event fields from `data.payload`:

```ruby
def verify_telnyx_signature(raw_body, signature_b64, timestamp)
  return false if TELNYX_PUBLIC_KEY.nil? || TELNYX_PUBLIC_KEY.empty?
  return false if signature_b64.nil? || timestamp.nil?
  return false if (Time.now.to_i - timestamp.to_i).abs > MAX_WEBHOOK_SKEW

  verify_key = Ed25519::VerifyKey.new(Base64.decode64(TELNYX_PUBLIC_KEY))
  verify_key.verify(Base64.decode64(signature_b64), "#{timestamp}|#{raw_body}")
rescue Ed25519::VerifyError, ArgumentError
  false
end
```

Do **not** use the SDK's `client.webhooks.unwrap` for Telnyx webhooks — in the 5.x SDK it delegates to the Standard Webhooks HMAC scheme (`webhook-*` headers, symmetric secret), which is incompatible with Telnyx's asymmetric Ed25519 signatures (`telnyx-*` headers). The native `ed25519` verification above is the correct approach.

The webhook handler captures the raw body, verifies, then reads `data.payload`:

```ruby
raw_body  = request.body.read
signature = request.env["HTTP_TELNYX_SIGNATURE_ED25519"]
timestamp = request.env["HTTP_TELNYX_TIMESTAMP"]

unless verify_telnyx_signature(raw_body, signature, timestamp)
  halt 401, { error: "Invalid webhook signature" }.to_json
end

event   = JSON.parse(raw_body)
payload = event.dig("data", "payload") || {}
```

## Step 3: Run It

```bash
bundle exec ruby app.rb
```

The server starts on `http://localhost:4567`.

## Step 4: Test It

Activate a SIM card (replace the ID with one from your account):

```bash
curl -X POST http://localhost:4567/sim/activate \
  -H "Content-Type: application/json" \
  -d '{
    "sim_card_id": "6b14e151-8493-4fa1-8664-1cc4e6d14158"
  }'
```

You should get back the enable action's `id`, `status`, `action_type`, and the `sim_card_id`. Because enabling is asynchronous, confirm the SIM reaches `enabled` by polling its status or by handling the `sim_card.status_changed` webhook.

## Going to Production

- **Authentication** — add API key or token validation on `/sim/activate` before exposing it publicly.
- **Confirm completion** — enable is async; watch `sim_card.status_changed` webhooks (already signature-verified here) instead of assuming success on the `200`.
- **Retries** — add bounded retries with backoff for `503`/`429` responses from Telnyx.
- **Structured logging** — log request IDs and SIM status transitions; never log secrets.

## Resources

- [Source code and reference](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/activate-sim-card-ruby/README.md)
- [Typed API reference](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/activate-sim-card-ruby/API.md)
- [IoT SIM Get Started](https://developers.telnyx.com/docs/iot-sim/get-started)
- [Ruby SDK](https://developers.telnyx.com/development/sdk/ruby)
- [Telnyx Portal](https://portal.telnyx.com)
