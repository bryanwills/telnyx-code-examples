package com.telnyx.examples;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpServer;
import com.telnyx.sdk.client.TelnyxClient;
import com.telnyx.sdk.client.okhttp.TelnyxOkHttpClient;
import com.telnyx.sdk.core.UnwrapWebhookParams;
import com.telnyx.sdk.core.http.Headers;
import com.telnyx.sdk.models.calls.CallDialParams;
import com.telnyx.sdk.models.calls.CallDialResponse;
import com.telnyx.sdk.models.webhooks.UnwrapWebhookEvent;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 * Place an outbound Call Control call via the Telnyx Java SDK (calls.dial).
 *
 * <p>Single-file example built on the JDK's {@code com.sun.net.httpserver.HttpServer} — no Spring,
 * Spark, or Javalin. One shared {@link TelnyxClient} is created from the environment and reused
 * across requests.
 *
 * <p>Endpoints:
 * <ul>
 *   <li>{@code GET  /health}        — liveness probe</li>
 *   <li>{@code POST /calls/dial}    — initiate an outbound call: {@code {"to": "+12125551234"}}</li>
 *   <li>{@code POST /webhooks/voice} — receive + Ed25519-verify Call Control events</li>
 * </ul>
 */
public final class Application {

    private static final Logger LOGGER = Logger.getLogger(Application.class.getName());
    private static final ObjectMapper MAPPER = new ObjectMapper();

    private Application() {
    }

    public static void main(String[] args) throws IOException {
        // One client, created once from TELNYX_API_KEY (+ optional TELNYX_PUBLIC_KEY) in the env.
        TelnyxClient client = TelnyxOkHttpClient.fromEnv();

        String fromNumber = requireEnv("TELNYX_PHONE_NUMBER");
        String connectionId = requireEnv("TELNYX_CONNECTION_ID");
        String webhookUrl = System.getenv("TELNYX_WEBHOOK_URL"); // optional

        int port = parsePort(System.getenv("PORT"), 8080);

        HttpServer server = HttpServer.create(new InetSocketAddress(port), 0);
        server.createContext("/health", new HealthHandler());
        server.createContext("/calls/dial", new DialHandler(client, fromNumber, connectionId, webhookUrl));
        server.createContext("/webhooks/voice", new WebhookHandler(client));
        server.setExecutor(null); // default executor
        server.start();

        LOGGER.info(() -> "Server listening on http://localhost:" + port);
    }

    // ── Handlers ──────────────────────────────────────────────────────────

    /** {@code GET /health} — returns {@code {"status":"ok"}}. */
    static final class HealthHandler implements HttpHandler {
        @Override
        public void handle(HttpExchange exchange) throws IOException {
            if (!"GET".equalsIgnoreCase(exchange.getRequestMethod())) {
                sendJson(exchange, 405, Map.of("error", "Method not allowed"));
                return;
            }
            sendJson(exchange, 200, Map.of("status", "ok"));
        }
    }

    /** {@code POST /calls/dial} — place an outbound call via {@code client.calls().dial(...)}. */
    static final class DialHandler implements HttpHandler {
        private final TelnyxClient client;
        private final String fromNumber;
        private final String connectionId;
        private final String webhookUrl;

        DialHandler(TelnyxClient client, String fromNumber, String connectionId, String webhookUrl) {
            this.client = client;
            this.fromNumber = fromNumber;
            this.connectionId = connectionId;
            this.webhookUrl = webhookUrl;
        }

        @Override
        public void handle(HttpExchange exchange) throws IOException {
            if (!"POST".equalsIgnoreCase(exchange.getRequestMethod())) {
                sendJson(exchange, 405, Map.of("error", "Method not allowed"));
                return;
            }

            String toNumber;
            try {
                byte[] body = readBody(exchange);
                Map<?, ?> json = MAPPER.readValue(body, Map.class);
                Object to = json.get("to");
                toNumber = to == null ? null : to.toString();
            } catch (Exception e) {
                // Malformed JSON — never echo the parse error back to the caller.
                LOGGER.log(Level.WARNING, "Failed to parse request body", e);
                sendJson(exchange, 400, Map.of("error", "Invalid JSON request body"));
                return;
            }

            if (toNumber == null || !toNumber.startsWith("+")) {
                sendJson(exchange, 400,
                        Map.of("error", "Field 'to' is required and must be E.164 (e.g. +12125551234)"));
                return;
            }

            try {
                CallDialParams.Builder params = CallDialParams.builder()
                        .connectionId(connectionId)
                        .from(fromNumber)
                        .to(toNumber);
                if (webhookUrl != null && !webhookUrl.isBlank()) {
                    params.webhookUrl(webhookUrl);
                }

                CallDialResponse response = client.calls().dial(params.build());

                String callControlId = response.data().map(CallDialResponse.Data::callControlId).orElse(null);

                Map<String, Object> result = new LinkedHashMap<>();
                result.put("call_control_id", callControlId);
                result.put("from", fromNumber);
                result.put("to", toNumber);
                sendJson(exchange, 200, result);
            } catch (Exception e) {
                // Log the detail server-side; return a generic message so we never leak it.
                LOGGER.log(Level.SEVERE, "Failed to dial call", e);
                sendJson(exchange, 502, Map.of("error", "Failed to place call"));
            }
        }
    }

    /**
     * {@code POST /webhooks/voice} — verify the Telnyx Ed25519 signature, then read event fields.
     *
     * <p>The signature is computed over the exact request bytes, so the raw body is read before any
     * JSON parsing and handed to {@code client.webhooks().unwrap(...)} together with the
     * {@code telnyx-signature-ed25519} and {@code telnyx-timestamp} headers. Verification requires a
     * configured {@code TELNYX_PUBLIC_KEY}.
     */
    static final class WebhookHandler implements HttpHandler {
        private final TelnyxClient client;

        WebhookHandler(TelnyxClient client) {
            this.client = client;
        }

        @Override
        public void handle(HttpExchange exchange) throws IOException {
            if (!"POST".equalsIgnoreCase(exchange.getRequestMethod())) {
                sendJson(exchange, 405, Map.of("error", "Method not allowed"));
                return;
            }

            byte[] rawBody = readBody(exchange);
            String signature = firstHeader(exchange, "telnyx-signature-ed25519");
            String timestamp = firstHeader(exchange, "telnyx-timestamp");

            if (signature == null || timestamp == null) {
                sendJson(exchange, 400, Map.of("error", "Missing Telnyx signature headers"));
                return;
            }

            UnwrapWebhookEvent event;
            try {
                Headers headers = Headers.builder()
                        .put("telnyx-signature-ed25519", signature)
                        .put("telnyx-timestamp", timestamp)
                        .build();
                UnwrapWebhookParams params = UnwrapWebhookParams.builder()
                        .body(new String(rawBody, StandardCharsets.UTF_8))
                        .headers(headers)
                        .build();
                // Throws on a bad signature or a stale timestamp.
                event = client.webhooks().unwrap(params);
            } catch (Exception e) {
                LOGGER.log(Level.WARNING, "Webhook signature verification failed", e);
                sendJson(exchange, 401, Map.of("error", "Invalid webhook signature"));
                return;
            }

            // Read event fields from data.payload via the typed accessors.
            event.callAnswered().ifPresent(e ->
                    LOGGER.info(() -> "call.answered: " + e.data()
                            .flatMap(d -> d.payload())
                            .flatMap(p -> p.callControlId())
                            .orElse("(unknown)")));
            event.callHangup().ifPresent(e ->
                    LOGGER.info(() -> "call.hangup: " + e.data()
                            .flatMap(d -> d.payload())
                            .flatMap(p -> p.callControlId())
                            .orElse("(unknown)")));

            // Always 200 once verified — Telnyx retries non-2xx.
            sendJson(exchange, 200, Map.of("status", "received"));
        }
    }

    // ── Helpers ───────────────────────────────────────────────────────────

    private static String requireEnv(String name) {
        String value = System.getenv(name);
        if (value == null || value.isBlank()) {
            throw new IllegalStateException("Missing required environment variable: " + name);
        }
        return value;
    }

    private static int parsePort(String raw, int fallback) {
        if (raw == null || raw.isBlank()) {
            return fallback;
        }
        try {
            return Integer.parseInt(raw.trim());
        } catch (NumberFormatException e) {
            return fallback;
        }
    }

    private static byte[] readBody(HttpExchange exchange) throws IOException {
        try (InputStream in = exchange.getRequestBody()) {
            return in.readAllBytes();
        }
    }

    private static String firstHeader(HttpExchange exchange, String name) {
        return exchange.getRequestHeaders().getFirst(name);
    }

    private static void sendJson(HttpExchange exchange, int status, Map<String, ?> body) throws IOException {
        byte[] payload = MAPPER.writeValueAsBytes(body);
        exchange.getResponseHeaders().add("Content-Type", "application/json");
        exchange.sendResponseHeaders(status, payload.length);
        try (OutputStream out = exchange.getResponseBody()) {
            out.write(payload);
        }
    }
}
