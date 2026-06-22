#!/usr/bin/env ruby
# frozen_string_literal: true

# Chat with a Telnyx AI Assistant over a production-ready Sinatra endpoint.
#
# NOTE: This file targets the Telnyx Ruby SDK 5.x line (Stainless-generated).
# `require "telnyx"` (lib/telnyx.rb) requires "standardwebhooks" at load time even
# though the gem does not declare it as a runtime dependency, so the Gemfile pins it
# explicitly. The SDK requires Ruby 3.2.0+.

require "telnyx"
require "sinatra"
require "json"
require "base64"
require "ed25519"
require "securerandom"
require "dotenv/load"

# --- Configuration ----------------------------------------------------------

# Maximum allowed clock skew (seconds) for inbound webhook replay protection.
MAX_WEBHOOK_SKEW = 300

# Instantiate the client ONCE per process. It is thread-safe and owns its own
# connection pool. api_key defaults to ENV["TELNYX_API_KEY"].
CLIENT = Telnyx::Client.new(api_key: ENV["TELNYX_API_KEY"])

# Lazily-built Ed25519 verify key for webhook signature checks. Built from the
# base64 Ed25519 public key in the Telnyx Portal (Account > Keys & Credentials).
def webhook_verify_key
  public_key = ENV["TELNYX_PUBLIC_KEY"]
  return nil if public_key.nil? || public_key.empty?

  @webhook_verify_key ||= Ed25519::VerifyKey.new(Base64.decode64(public_key))
end

# --- Core logic --------------------------------------------------------------

# Send a single message to an AI Assistant and return its reply, preserving the
# conversation id so multi-turn context is maintained across requests.
#
# @param assistant_id [String] the configured AI Assistant id
# @param content [String] the user's message
# @param conversation_id [String] reused across turns to maintain context
# @param name [String, nil] optional display name of the speaker
# @return [Hash] JSON-serializable response data
def chat_with_assistant(assistant_id:, content:, conversation_id:, name: nil)
  raise ArgumentError, "AI_ASSISTANT_ID environment variable not set" if assistant_id.nil? || assistant_id.empty?
  raise ArgumentError, "Message cannot be empty" if content.nil? || content.strip.empty?

  # client.ai.assistants.chat returns Telnyx::Models::AI::AssistantChatResponse,
  # whose only field is `.content` (the assistant's reply text).
  response = CLIENT.ai.assistants.chat(
    assistant_id,
    content: content,
    conversation_id: conversation_id,
    name: name
  )

  {
    assistant_id: assistant_id,
    conversation_id: conversation_id,
    user_message: content,
    assistant_response: response.content
  }
end

# --- Sinatra app -------------------------------------------------------------

set :port, (ENV["PORT"] || 3000).to_i
set :bind, "0.0.0.0"
# Do NOT show exception details to clients; log them instead (see error handler).
set :show_exceptions, false
set :raise_errors, false

# POST /chat
# Send a message to the configured AI Assistant and receive its reply.
#
# Body: { "message": "<text>", "conversation_id": "<optional>", "name": "<optional>" }
# The assistant is selected by the AI_ASSISTANT_ID env var, not the request body.
post "/chat" do
  content_type :json

  begin
    body = JSON.parse(request.body.read)
  rescue JSON::ParserError
    halt 400, { error: "Request body must be valid JSON" }.to_json
  end

  message = body["message"]
  if message.nil? || (message.is_a?(String) && message.strip.empty?)
    halt 400, { error: "Missing required field: 'message'" }.to_json
  end

  # Reuse an existing conversation id to maintain context across turns, or mint a
  # new one for the first turn. The client echoes it back on subsequent requests.
  conversation_id = body["conversation_id"]
  conversation_id = "conv-#{SecureRandom.uuid}" if conversation_id.nil? || conversation_id.to_s.strip.empty?

  begin
    result = chat_with_assistant(
      assistant_id: ENV["AI_ASSISTANT_ID"],
      content: message,
      conversation_id: conversation_id,
      name: body["name"]
    )
    status 200
    result.to_json
  rescue ArgumentError => e
    # Configuration / validation errors — message is safe to surface.
    code = e.message.include?("environment variable") ? 500 : 400
    halt code, { error: e.message }.to_json
  rescue Telnyx::Errors::AuthenticationError
    halt 401, { error: "Invalid API key" }.to_json
  rescue Telnyx::Errors::RateLimitError
    halt 429, { error: "Rate limit exceeded. Please slow down." }.to_json
  rescue Telnyx::Errors::APIConnectionError
    halt 503, { error: "Network error connecting to Telnyx" }.to_json
  rescue Telnyx::Errors::APIStatusError => e
    # e.status is the HTTP status from Telnyx (Integer). Surface a generic
    # message; do not leak the underlying exception details.
    code = e.status.is_a?(Integer) && e.status >= 400 ? e.status : 502
    halt code, { error: "Telnyx API error" }.to_json
  end
end

# POST /webhooks/ai
# Receive and verify an inbound Telnyx webhook (e.g. conversation events).
# Telnyx signs with Ed25519 over "<telnyx-timestamp>|<raw-body>". We verify the
# RAW body BEFORE parsing or trusting any field, and read event data from
# data.payload. We never use client.webhooks.unwrap (it implements the Standard
# Webhooks HMAC scheme, not Telnyx's Ed25519 scheme).
post "/webhooks/ai" do
  content_type :json

  raw = request.body.read
  signature = request.env["HTTP_TELNYX_SIGNATURE_ED25519"]
  timestamp = request.env["HTTP_TELNYX_TIMESTAMP"]

  halt 400, { error: "Missing signature headers" }.to_json unless signature && timestamp
  halt 408, { error: "Stale webhook" }.to_json if (Time.now.to_i - timestamp.to_i).abs > MAX_WEBHOOK_SKEW

  verify_key = webhook_verify_key
  halt 500, { error: "Webhook verification not configured" }.to_json if verify_key.nil?

  begin
    verify_key.verify(Base64.decode64(signature), "#{timestamp}|#{raw}")
  rescue Ed25519::VerifyError, ArgumentError
    halt 401, { error: "Invalid signature" }.to_json
  end

  # Signature is valid — now it is safe to parse and read data.payload.
  event = JSON.parse(raw)
  event_type = event.dig("data", "event_type")
  payload = event.dig("data", "payload") || {}

  logger.info("Verified Telnyx webhook: #{event_type} conversation=#{payload['conversation_id']}")

  status 200
  { received: true }.to_json
end

# GET /health
# Liveness check.
get "/health" do
  content_type :json
  { status: "ok" }.to_json
end

# Catch-all error handler — log full details server-side, return a generic
# message to the client so exception internals never leak over HTTP.
error do
  logger.error(env["sinatra.error"]&.message)
  content_type :json
  status 500
  { error: "Internal server error" }.to_json
end
