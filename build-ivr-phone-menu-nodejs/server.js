#!/usr/bin/env node
/**
 * Production-ready IVR system using Telnyx Voice API and Express.js
 * Handles inbound calls, DTMF collection, and menu-based call routing.
 */

const express = require("express");
const crypto = require("crypto");
require("dotenv").config();

// Initialize Telnyx client. The installed Node SDK is a factory function,
// so it is initialized by calling it with the API key. It is still used for
// outbound Call Control API calls (answer/speak/gather/transfer).
const telnyx = require("telnyx")(process.env.TELNYX_API_KEY);

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

const app = express();

// IMPORTANT: Telnyx webhook signature verification must run over the RAW
// request body. A global JSON body parser would consume the request stream
// first, leaving req.body as a parsed object — verification would then run
// over "[object Object]" and reject every legitimate webhook.
//
// To avoid that, mount express.raw() on the webhook path so handlers receive
// the raw bytes (Buffer), and apply express.json() to every OTHER route.
app.use("/webhooks", express.raw({ type: "*/*" }));
app.use((req, res, next) => {
  if (req.path.startsWith("/webhooks")) return next();
  return express.json()(req, res, next);
});

// In-memory store for call state (use Redis in production)
const callState = new Map();

/**
 * Helper: Answer an inbound call and start the IVR menu.
 * Stores call state for subsequent DTMF handling.
 */
async function answerAndGreet(callControlId) {
  try {
    // Answer the call
    await telnyx.calls.actions.answer(callControlId);

    // Store call state
    callState.set(callControlId, {
      status: "greeting",
      menuLevel: "main",
      createdAt: Date.now(),
    });

    // Play initial greeting prompt
    await telnyx.calls.actions.speak(callControlId, {
      payload: "Welcome to our IVR system. Press 1 for sales, 2 for support, or 3 to repeat this menu.",
      voice: "male",
      language: "en-US",
    });

    // Start collecting DTMF input (up to 1 digit, 5 second timeout)
    await telnyx.calls.actions.gather_dtmf(callControlId, {
      max_digits: 1,
      timeout_millis: 5000,
    });
  } catch (error) {
    console.error(`Error answering call ${callControlId}:`, error.message);
    throw error;
  }
}

/**
 * Helper: Route call based on DTMF selection.
 * Handles menu navigation and call transfers.
 */
async function routeMenuSelection(callControlId, digit) {
  const state = callState.get(callControlId) || {};

  try {
    switch (digit) {
      case "1":
        // Route to sales
        await telnyx.calls.actions.speak(callControlId, {
          payload: "Transferring you to our sales team. Please hold.",
          voice: "male",
          language: "en-US",
        });
        // Transfer to sales number (replace with your actual number)
        await telnyx.calls.actions.transfer(callControlId, {
          to: "+15559876543",
        });
        state.menuLevel = "transferred_sales";
        break;

      case "2":
        // Route to support
        await telnyx.calls.actions.speak(callControlId, {
          payload: "Transferring you to our support team. Please hold.",
          voice: "male",
          language: "en-US",
        });
        // Transfer to support number (replace with your actual number)
        await telnyx.calls.actions.transfer(callControlId, {
          to: "+15559876544",
        });
        state.menuLevel = "transferred_support";
        break;

      case "3":
        // Repeat menu
        await telnyx.calls.actions.speak(callControlId, {
          payload: "Press 1 for sales, 2 for support, or 3 to repeat this menu.",
          voice: "male",
          language: "en-US",
        });
        await telnyx.calls.actions.gather_dtmf(callControlId, {
          max_digits: 1,
          timeout_millis: 5000,
        });
        state.menuLevel = "main";
        break;

      default:
        // Invalid selection
        await telnyx.calls.actions.speak(callControlId, {
          payload: "Invalid selection. Please try again.",
          voice: "male",
          language: "en-US",
        });
        await telnyx.calls.actions.gather_dtmf(callControlId, {
          max_digits: 1,
          timeout_millis: 5000,
        });
        break;
    }

    // Update call state
    state.status = "menu_processed";
    state.lastDigit = digit;
    state.updatedAt = Date.now();
    callState.set(callControlId, state);
  } catch (error) {
    console.error(`Error routing menu selection for ${callControlId}:`, error.message);
    throw error;
  }
}

/**
 * Helper: Clean up call state when call ends.
 */
function cleanupCallState(callControlId) {
  if (callState.has(callControlId)) {
    callState.delete(callControlId);
    console.log(`Cleaned up state for call ${callControlId}`);
  }
}

/**
 * Webhook endpoint: Handle inbound call initiated event.
 * This is triggered when a call arrives at your Telnyx number.
 */
app.post("/webhooks/call-initiated", async (req, res) => {
  // req.body is the raw request body (a Buffer) thanks to express.raw().
  const rawBody = req.body;
  // Verify the Ed25519 signature over the RAW body before parsing.
  if (!verifyTelnyxSignature(rawBody.toString(), req.headers)) {
    return res.status(401).json({ error: "invalid signature" });
  }
  // Parse the body only AFTER the signature has been verified.
  const event = JSON.parse(rawBody.toString()).data;

  const callControlId = event.payload.call_control_id;

  console.log(`Inbound call initiated: ${callControlId}`);

  try {
    // Answer the call and start IVR greeting
    await answerAndGreet(callControlId);
    res.json({ status: "ok" });
  } catch (error) {
    console.error("Error handling call.initiated webhook:", error.message);
    res.status(500).json({ error: error.message });
  }
});

/**
 * Webhook endpoint: Handle DTMF received event.
 * This is triggered when the caller presses a digit.
 */
app.post("/webhooks/dtmf-received", async (req, res) => {
  // req.body is the raw request body (a Buffer) thanks to express.raw().
  const rawBody = req.body;
  // Verify the Ed25519 signature over the RAW body before parsing.
  if (!verifyTelnyxSignature(rawBody.toString(), req.headers)) {
    return res.status(401).json({ error: "invalid signature" });
  }
  // Parse the body only AFTER the signature has been verified.
  const event = JSON.parse(rawBody.toString()).data;

  const callControlId = event.payload.call_control_id;
  const digit = event.payload.dtmf.digits;

  console.log(`DTMF received on call ${callControlId}: ${digit}`);

  try {
    // Route based on the digit pressed
    await routeMenuSelection(callControlId, digit);
    res.json({ status: "ok" });
  } catch (error) {
    console.error("Error handling call.dtmf.received webhook:", error.message);
    res.status(500).json({ error: error.message });
  }
});

/**
 * Webhook endpoint: Handle call hangup event.
 * This is triggered when the call ends.
 */
app.post("/webhooks/call-hangup", async (req, res) => {
  // req.body is the raw request body (a Buffer) thanks to express.raw().
  const rawBody = req.body;
  // Verify the Ed25519 signature over the RAW body before parsing.
  if (!verifyTelnyxSignature(rawBody.toString(), req.headers)) {
    return res.status(401).json({ error: "invalid signature" });
  }
  // Parse the body only AFTER the signature has been verified.
  const event = JSON.parse(rawBody.toString()).data;

  const callControlId = event.payload.call_control_id;

  console.log(`Call ended: ${callControlId}`);

  // Clean up call state
  cleanupCallState(callControlId);

  res.json({ status: "ok" });
});

/**
 * Health check endpoint for monitoring.
 */
app.get("/health", (req, res) => {
  res.json({ status: "healthy", timestamp: new Date().toISOString() });
});

/**
 * Error handler middleware for Telnyx API errors.
 * Catches exceptions from route handlers and returns appropriate HTTP status codes.
 */
app.use((err, req, res, next) => {
  console.error("Unhandled error:", err.message);

  // The Telnyx SDK tags errors with a `type` and an HTTP `statusCode`.
  // Map the well-known error types to appropriate HTTP responses without
  // depending on importing the error constructors directly.
  const status = err.statusCode || err.status_code;

  switch (err.type) {
    case "TelnyxAuthenticationError":
      return res.status(401).json({ error: "Invalid API key" });
    case "TelnyxRateLimitError":
      return res.status(429).json({ error: "Rate limit exceeded. Please slow down." });
    case "TelnyxConnectionError":
      return res.status(503).json({ error: "Network error connecting to Telnyx" });
    default:
      if (status) {
        return res.status(status).json({ error: err.message, status_code: status });
      }
  }

  // Generic error — do not leak internal exception details.
  res.status(500).json({ error: "Internal server error" });
});

// Start the server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`IVR system listening on port ${PORT}`);
  console.log(`Webhook URL: ${process.env.WEBHOOK_URL}`);
});
