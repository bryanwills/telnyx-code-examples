# frozen_string_literal: true
#
# Activate (enable) a Telnyx IoT SIM card over HTTP using the Telnyx Ruby SDK
# and Sinatra.
#
# Endpoints:
#   POST /sim/activate    -> enable a SIM card by its Telnyx SIM card ID
#   POST /webhooks/sim    -> receive + Ed25519-verify SIM status webhooks
#
# NOTE: telnyx 5.x is a Stainless rewrite that uses the instance client
# `Telnyx::Client.new(...)`, and `lib/telnyx.rb` requires "standardwebhooks"
# at load time even though the gem does not declare it as a runtime dependency
# (see Gemfile). The activation call is `client.sim_cards.actions.enable(id)`.

require "telnyx"
require "dotenv/load"
require "sinatra"
require "json"
require "base64"
require "ed25519"

# --- Configuration ---------------------------------------------------------

API_KEY = ENV["TELNYX_API_KEY"]
raise "TELNYX_API_KEY environment variable not set" if API_KEY.nil? || API_KEY.empty?

# Base64-encoded Ed25519 public key from Telnyx Portal > Account >
# Keys & Credentials > Public Key. Only required to verify inbound webhooks.
TELNYX_PUBLIC_KEY = ENV["TELNYX_PUBLIC_KEY"]

# Reject webhooks whose timestamp is older than this many seconds (replay
# protection).
MAX_WEBHOOK_SKEW = 300

# Instantiate the client ONCE per process (thread-safe; owns a connection pool).
CLIENT = Telnyx::Client.new(api_key: API_KEY)

set :port, (ENV["PORT"] || 4567).to_i
set :bind, "0.0.0.0"

# --- Helpers ---------------------------------------------------------------

# Activate (enable) a SIM card and return a plain, JSON-serializable hash.
# SDK model objects are not directly JSON-serializable.
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

# Verify a Telnyx Ed25519 webhook signature over "<timestamp>|<raw_body>".
# Returns true on success, false on any failure. Never raises.
def verify_telnyx_signature(raw_body, signature_b64, timestamp)
  return false if TELNYX_PUBLIC_KEY.nil? || TELNYX_PUBLIC_KEY.empty?
  return false if signature_b64.nil? || timestamp.nil?
  return false if (Time.now.to_i - timestamp.to_i).abs > MAX_WEBHOOK_SKEW

  verify_key = Ed25519::VerifyKey.new(Base64.decode64(TELNYX_PUBLIC_KEY))
  verify_key.verify(Base64.decode64(signature_b64), "#{timestamp}|#{raw_body}")
rescue Ed25519::VerifyError, ArgumentError
  false
end

# --- Routes -----------------------------------------------------------------

# Activate a SIM card by ID.
#
# Request body: {"sim_card_id": "<uuid>"}
post "/sim/activate" do
  content_type :json

  begin
    request.body.rewind
    body = JSON.parse(request.body.read)
  rescue JSON::ParserError
    halt 400, { error: "Request body must be valid JSON" }.to_json
  end

  sim_card_id = body["sim_card_id"]
  if sim_card_id.nil? || sim_card_id.to_s.strip.empty?
    halt 400, { error: "Missing required field: 'sim_card_id'" }.to_json
  end

  begin
    result = activate_sim(sim_card_id)
    status 200
    result.to_json
  rescue Telnyx::Errors::AuthenticationError
    halt 401, { error: "Invalid API key" }.to_json
  rescue Telnyx::Errors::RateLimitError
    halt 429, { error: "Rate limit exceeded. Please slow down." }.to_json
  rescue Telnyx::Errors::APIStatusError => e
    # Echo the upstream HTTP status; do not leak the raw exception message.
    logger.error("Telnyx API error: #{e.class} status=#{e.status}")
    upstream = e.status.to_i
    upstream = 502 unless (400..599).cover?(upstream)
    halt upstream, { error: "Telnyx API returned an error", status_code: e.status }.to_json
  rescue Telnyx::Errors::APIConnectionError
    halt 503, { error: "Network error connecting to Telnyx" }.to_json
  rescue StandardError => e
    # Never leak internal details to the client.
    logger.error("Unexpected error: #{e.class}: #{e.message}")
    halt 500, { error: "Internal server error" }.to_json
  end
end

# Receive and verify SIM status-change webhooks from Telnyx.
#
# Telnyx signs the request with Ed25519 over "<telnyx-timestamp>|<raw-body>".
# We verify the signature BEFORE parsing/trusting the body, then read all
# event fields from data.payload.
post "/webhooks/sim" do
  content_type :json

  raw_body  = request.body.read
  signature = request.env["HTTP_TELNYX_SIGNATURE_ED25519"]
  timestamp = request.env["HTTP_TELNYX_TIMESTAMP"]

  unless verify_telnyx_signature(raw_body, signature, timestamp)
    halt 401, { error: "Invalid webhook signature" }.to_json
  end

  begin
    event = JSON.parse(raw_body)
  rescue JSON::ParserError
    halt 400, { error: "Request body must be valid JSON" }.to_json
  end

  event_type = event.dig("data", "event_type")
  payload    = event.dig("data", "payload") || {}

  case event_type
  when "sim_card.status_changed", "sim_card_status_changed"
    logger.info(
      "SIM #{payload['sim_card_id'] || payload['id']} status -> #{payload['status']}"
    )
    # ... handle the SIM status transition here ...
  else
    logger.info("Received SIM webhook: #{event_type}")
  end

  status 200
  { received: true }.to_json
end
