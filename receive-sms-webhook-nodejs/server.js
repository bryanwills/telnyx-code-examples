#!/usr/bin/env node
/**
 * Production-ready Express webhook receiver for inbound SMS via Telnyx.
 * Validates webhook payloads, processes messages, and responds within 5 seconds.
 */

require("dotenv").config();
const express = require("express");
const crypto = require("crypto");

const app = express();

// Verify the Telnyx Ed25519 webhook signature (version-proof; stdlib only — no SDK dependency).
function verifyTelnyxSignature(rawBody, headers, toleranceSec = 300) {
  const sig = headers["telnyx-signature-ed25519"];
  const ts = headers["telnyx-timestamp"];
  const pub = process.env.TELNYX_PUBLIC_KEY;
  if (!sig || !ts || !pub) return false;
  if (Math.abs(Date.now() / 1000 - Number(ts)) > toleranceSec) return false;
  try {
    const der = Buffer.concat([Buffer.from("302a300506032b6570032100", "hex"), Buffer.from(pub, "base64")]);
    const key = crypto.createPublicKey({ key: der, format: "der", type: "spki" });
    return crypto.verify(null, Buffer.from(`${ts}|${rawBody}`), key, Buffer.from(sig, "base64"));
  } catch (e) {
    return false;
  }
}

// IMPORTANT: do NOT apply a global JSON body parser ahead of the webhook
// route. A global express.json()/bodyParser.json() would consume the request
// stream first, leaving req.body a parsed object so signature verification
// would run over "[object Object]" and reject every real webhook.
//
// The webhook route mounts express.raw({ type: "*/*" }) so it receives the
// raw bytes. JSON parsing is applied only to the non-webhook routes below.

// In-memory storage for received messages (replace with database in production)
const receivedMessages = [];

/**
 * Process inbound SMS webhook event.
 * Validates webhook payload and extracts message details.
 * @param {Object} payload - Webhook event payload from Telnyx.
 * @returns {Object} Processed message data.
 */
function processInboundSMS(payload) {
  // Validate required fields in webhook payload
  if (!payload.data || !payload.data.payload) {
    throw new Error("Invalid webhook payload structure");
  }

  const messageData = payload.data.payload;

  // Extract message details — ensure fields exist before accessing
  const processedMessage = {
    message_id: messageData.id || null,
    from: messageData.from?.phone_number || null,
    to: messageData.to?.[0]?.phone_number || null,
    text: messageData.text || "",
    received_at: messageData.received_at || new Date().toISOString(),
    direction: messageData.direction || "inbound",
  };

  // Validate critical fields
  if (!processedMessage.from || !processedMessage.to) {
    throw new Error("Missing sender or recipient phone number in webhook");
  }

  return processedMessage;
}

/**
 * Webhook endpoint to receive inbound SMS messages.
 * Telnyx sends POST requests to this endpoint when SMS is received.
 *
 * The raw body is captured via express.raw so the Telnyx signature can be
 * verified before the payload is processed. Signature verification is
 * enforced on every request to this endpoint.
 */
app.post("/webhooks/sms", express.raw({ type: "*/*" }), async (req, res) => {
  // Enforce Telnyx webhook signature verification (ENFORCE-ALWAYS).
  // express.raw gives us the raw request bytes as a Buffer in req.body.
  const rawBody = Buffer.isBuffer(req.body) ? req.body : Buffer.from("");

  // Verify the Ed25519 signature over the RAW body BEFORE parsing it.
  if (!verifyTelnyxSignature(rawBody.toString(), req.headers)) {
    return res.status(401).json({ error: "invalid signature" });
  }

  try {
    // Parse the verified raw body into JSON (only after the signature passed)
    let body;
    try {
      body = JSON.parse(rawBody.toString());
    } catch (parseError) {
      return res.status(400).json({ error: "Invalid webhook payload" });
    }

    // Validate webhook payload structure
    if (!body || !body.data) {
      return res.status(400).json({ error: "Invalid webhook payload" });
    }

    // Process the inbound SMS
    const message = processInboundSMS(body);

    // Store message in memory (use database in production)
    receivedMessages.push(message);

    console.log(`[SMS Received] From: ${message.from}, To: ${message.to}`);
    console.log(`Message: ${message.text}`);

    // Respond with 200 OK to acknowledge receipt
    // Telnyx requires a 2xx response within 5 seconds
    res.status(200).json({
      success: true,
      message_id: message.message_id,
      status: "received",
    });
  } catch (error) {
    console.error("Webhook processing error:", error.message);
    // Return 400 for validation errors, but still acknowledge to Telnyx
    res.status(400).json({ error: error.message });
  }
});

// JSON body parsing for the non-webhook routes only. Mounted AFTER the
// webhook route so it never touches the raw webhook stream.
const jsonParser = express.json();

/**
 * Health check endpoint to verify server is running.
 */
app.get("/health", jsonParser, (req, res) => {
  res.status(200).json({ status: "ok", timestamp: new Date().toISOString() });
});

/**
 * Debug endpoint to view received messages (remove in production).
 */
app.get("/messages", jsonParser, (req, res) => {
  res.status(200).json({
    count: receivedMessages.length,
    messages: receivedMessages,
  });
});

/**
 * Global error handler for uncaught exceptions.
 */
app.use((err, req, res, next) => {
  console.error("Unhandled error:", err);
  res.status(500).json({
    error: "Internal server error",
    message: err.message,
  });
});

// Start the server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Express server running on port ${PORT}`);
  console.log(`Webhook endpoint: http://localhost:${PORT}/webhooks/sms`);
  console.log(`Health check: http://localhost:${PORT}/health`);
});
