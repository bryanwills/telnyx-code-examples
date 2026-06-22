# frozen_string_literal: true
#
# Place an outbound phone call over HTTP using the Telnyx Ruby SDK and Sinatra.
#
# Endpoints:
#   POST /calls/dial     -> initiate an outbound Call Control call
#   POST /webhooks/voice -> receive + Ed25519-verify call lifecycle webhooks
#
# NOTE: telnyx 5.x is a Stainless rewrite that uses the instance client
# `Telnyx::Client.new(...)`, and `lib/telnyx.rb` requires "standardwebhooks"
# at load time even though the gem does not declare it as a runtime dependency
# (see Gemfile). The outbound-call call is `client.calls.dial(...)`.

require "telnyx"
require "dotenv/load"
require "sinatra"
require "json"
require "base64"
require "ed25519"

# --- Configuration ---------------------------------------------------------

API_KEY = ENV["TELNYX_API_KEY"]
raise "TELNYX_API_KEY environment variable not set" if API_KEY.nil? || API_KEY.empty?

# The Call Control Application ID that owns the outbound leg (Portal > Call
# Control > Applications). Required to dial.
CONNECTION_ID = ENV["TELNYX_CONNECTION_ID"]

# Telnyx number to place the call from, in E.164 format.
FROM_NUMBER = ENV["TELNYX_PHONE_NUMBER"]

# Optional public webhook URL for call lifecycle events. When set, it is passed
# to calls.dial so Telnyx delivers events to /webhooks/voice.
VOICE_WEBHOOK_URL = ENV["TELNYX_VOICE_WEBHOOK_URL"]

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

# Place an outbound Call Control call and return a plain, JSON-serializable
# hash. SDK model objects are not directly JSON-serializable.
def dial_call(to_number)
  params = {
    connection_id: CONNECTION_ID,
    from: FROM_NUMBER,
    to: to_number
  }
  # Only forward a webhook URL when one is configured.
  params[:webhook_url] = VOICE_WEBHOOK_URL unless VOICE_WEBHOOK_URL.nil? || VOICE_WEBHOOK_URL.empty?

  response = CLIENT.calls.dial(**params)
  call = response.data
  {
    call_control_id: call.call_control_id,
    call_leg_id: call.call_leg_id,
    call_session_id: call.call_session_id,
    is_alive: call.is_alive,
    from: FROM_NUMBER,
    to: to_number
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

# Initiate an outbound call.
#
# Request body: {"to": "+15551234567"}
post "/calls/dial" do
  content_type :json

  if CONNECTION_ID.nil? || CONNECTION_ID.empty?
    halt 500, { error: "TELNYX_CONNECTION_ID environment variable not set" }.to_json
  end
  if FROM_NUMBER.nil? || FROM_NUMBER.empty?
    halt 500, { error: "TELNYX_PHONE_NUMBER environment variable not set" }.to_json
  end

  begin
    request.body.rewind
    body = JSON.parse(request.body.read)
  rescue JSON::ParserError
    halt 400, { error: "Request body must be valid JSON" }.to_json
  end

  to_number = body["to"]
  if to_number.nil? || to_number.to_s.strip.empty?
    halt 400, { error: "Missing required field: 'to'" }.to_json
  end
  unless to_number.start_with?("+")
    halt 400, { error: "Phone number must be in E.164 format (e.g., +15551234567)" }.to_json
  end

  begin
    result = dial_call(to_number)
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

# Receive and verify call lifecycle webhooks from Telnyx.
#
# Telnyx signs the request with Ed25519 over "<telnyx-timestamp>|<raw-body>".
# We verify the signature BEFORE parsing/trusting the body, then read all
# event fields from data.payload.
post "/webhooks/voice" do
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
  when "call.initiated"
    logger.info("Call #{payload['call_control_id']} initiated (#{payload['direction']})")
  when "call.answered"
    logger.info("Call #{payload['call_control_id']} answered")
    # ... issue follow-up commands here, e.g.
    # CLIENT.calls.actions.speak(payload["call_control_id"], ...)
  when "call.hangup"
    logger.info("Call #{payload['call_control_id']} ended: #{payload['hangup_cause']}")
  else
    logger.info("Received voice webhook: #{event_type}")
  end

  status 200
  { received: true }.to_json
end
