# frozen_string_literal: true

# Production-ready Sinatra webhook receiver for inbound SMS via Telnyx.
#
# Telnyx signs every webhook with Ed25519 over the string "<telnyx-timestamp>|<raw-body>".
# This server verifies that signature over the RAW request body BEFORE parsing or
# trusting any field, then reads message data from data.payload.
#
# Why native Ed25519 (the `ed25519` gem) and not the SDK helper:
# `Telnyx::Client#webhooks.unwrap` delegates to the Standard Webhooks spec
# (HMAC-SHA256 over "<msg_id>.<timestamp>.<payload>" using a symmetric whsec_ secret
# and webhook-* headers). That is NOT Telnyx's scheme, so it rejects genuine Telnyx
# webhooks. We verify the real Telnyx Ed25519 signature directly here.

require "sinatra"
require "dotenv/load"
require "ed25519"
require "base64"
require "json"

# Reject webhooks whose timestamp is more than this many seconds away from now
# (replay-attack protection).
MAX_SKEW_SECONDS = 300

# In-memory storage for received messages (replace with a database in production).
RECEIVED_MESSAGES = []

set :port, (ENV["PORT"] || 5000).to_i
set :bind, "0.0.0.0"
# Surface unexpected errors as generic 500s instead of leaking stack traces.
set :show_exceptions, false
set :raise_errors, false

helpers do
  # Serialize a Hash to a JSON response body and set the content type.
  def json_response(hash)
    content_type :json
    hash.to_json
  end
end

# Verify the Telnyx Ed25519 webhook signature over "<timestamp>|<raw_body>".
# Returns true only when the signature, headers, and timestamp skew all check out.
def verify_telnyx_signature(raw_body, signature, timestamp)
  public_key = ENV["TELNYX_PUBLIC_KEY"]
  return false if signature.nil? || timestamp.nil? || public_key.nil? || public_key.empty?

  # Replay protection: reject stale or future-dated timestamps.
  return false if (Time.now.to_i - timestamp.to_i).abs > MAX_SKEW_SECONDS

  verify_key = Ed25519::VerifyKey.new(Base64.decode64(public_key))
  verify_key.verify(Base64.decode64(signature), "#{timestamp}|#{raw_body}")
rescue Ed25519::VerifyError, ArgumentError
  # VerifyError: signature does not match. ArgumentError: malformed key/signature length.
  false
end

# Extract and validate the inbound SMS fields from a parsed webhook event.
# Reads everything from data.payload. Raises ArgumentError when the structure is
# wrong or a required field (sender/recipient) is missing.
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

# Webhook endpoint. Telnyx POSTs here when an SMS is received.
# The raw body is read directly (Sinatra does not parse it first), so the Ed25519
# signature can be verified before the JSON is trusted.
post "/webhooks/sms" do
  raw_body  = request.body.read
  signature = request.env["HTTP_TELNYX_SIGNATURE_ED25519"]
  timestamp = request.env["HTTP_TELNYX_TIMESTAMP"]

  # ENFORCE-ALWAYS: verify the Telnyx Ed25519 signature before parsing/trusting.
  unless verify_telnyx_signature(raw_body, signature, timestamp)
    halt 401, json_response(error: "invalid signature")
  end

  begin
    event = JSON.parse(raw_body)
  rescue JSON::ParserError
    halt 400, json_response(error: "Invalid webhook payload")
  end

  halt 400, json_response(error: "Invalid webhook payload") unless event.is_a?(Hash) && event["data"]

  # Only act on inbound message events; acknowledge everything else with 200.
  if event.dig("data", "event_type") == "message.received"
    begin
      message = process_inbound_sms(event)
    rescue ArgumentError => e
      halt 400, json_response(error: e.message)
    end

    RECEIVED_MESSAGES << message
    logger.info("[SMS Received] from=#{message[:from]} to=#{message[:to]}")

    status 200
    json_response(success: true, message_id: message[:message_id], status: "received")
  else
    status 200
    json_response(success: true, status: "ignored")
  end
end

# Debug endpoint: list every message received since startup (in-memory; remove in production).
get "/messages" do
  status 200
  json_response(count: RECEIVED_MESSAGES.length, messages: RECEIVED_MESSAGES)
end

# Liveness check.
get "/health" do
  status 200
  json_response(status: "ok", timestamp: Time.now.utc.iso8601)
end

# Catch-all error handler: log internally, return a generic message (no leakage).
error do
  logger.error("Unhandled error: #{env['sinatra.error']&.message}")
  status 500
  json_response(error: "Internal server error")
end
