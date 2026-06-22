package com.telnyx.examples;

import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpServer;
import com.telnyx.sdk.client.TelnyxClient;
import com.telnyx.sdk.client.okhttp.TelnyxOkHttpClient;
import com.telnyx.sdk.core.UnwrapWebhookParams;
import com.telnyx.sdk.core.http.Headers;
import com.telnyx.sdk.models.InboundMessagePayload;
import com.telnyx.sdk.models.webhooks.InboundMessageWebhookEvent;
import com.telnyx.sdk.models.webhooks.UnwrapWebhookEvent;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Optional;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 * Production-ready JDK HttpServer webhook receiver for inbound SMS via Telnyx.
 *
 * <p>Telnyx delivers a {@code message.received} event to {@code POST /webhooks/sms} when an SMS
 * arrives on an inbound-enabled number. This server verifies the Telnyx Ed25519 signature over the
 * exact bytes of {@code "<telnyx-timestamp>|<raw body>"} BEFORE trusting the payload, then reads the
 * message fields from {@code data.payload} and acknowledges with {@code 200 OK} within 5 seconds.
 *
 * <p>Verification and parsing are delegated to the Telnyx SDK via
 * {@code client.webhooks().unwrap(UnwrapWebhookParams)}, which performs the Ed25519 check and a
 * 300-second replay-tolerance window using the configured public key ({@code TELNYX_PUBLIC_KEY}).
 */
public final class Application {

    private static final Logger LOGGER = Logger.getLogger(Application.class.getName());

    private Application() {
    }

    public static void main(String[] args) throws IOException {
        // One shared client. fromEnv() reads TELNYX_API_KEY and TELNYX_PUBLIC_KEY from the
        // environment; the public key is required so unwrap() can verify webhook signatures.
        TelnyxClient client = TelnyxOkHttpClient.fromEnv();

        int port = resolvePort();
        HttpServer server = HttpServer.create(new InetSocketAddress(port), 0);
        server.createContext("/webhooks/sms", new SmsWebhookHandler(client));
        server.createContext("/health", new HealthHandler());
        server.setExecutor(null); // default executor
        server.start();

        LOGGER.info(() -> "HttpServer listening on port " + port);
        LOGGER.info(() -> "Webhook endpoint: http://localhost:" + port + "/webhooks/sms");
        LOGGER.info(() -> "Health check:     http://localhost:" + port + "/health");
    }

    private static int resolvePort() {
        String raw = System.getenv("PORT");
        if (raw == null || raw.isBlank()) {
            return 8080;
        }
        try {
            return Integer.parseInt(raw.trim());
        } catch (NumberFormatException e) {
            LOGGER.warning("Invalid PORT value; falling back to 8080");
            return 8080;
        }
    }

    /** Handles inbound SMS webhook deliveries: verify signature, then read data.payload. */
    static final class SmsWebhookHandler implements HttpHandler {

        private final TelnyxClient client;

        SmsWebhookHandler(TelnyxClient client) {
            this.client = client;
        }

        @Override
        public void handle(HttpExchange exchange) throws IOException {
            try {
                if (!"POST".equalsIgnoreCase(exchange.getRequestMethod())) {
                    writeJson(exchange, 405, "{\"error\":\"method not allowed\"}");
                    return;
                }

                // Read the raw request bytes BEFORE any parsing; the signature is over these bytes.
                String rawBody = readBody(exchange);

                // Headers are case-insensitive; the SDK looks them up case-insensitively.
                String signature = firstHeader(exchange, "telnyx-signature-ed25519");
                String timestamp = firstHeader(exchange, "telnyx-timestamp");
                if (signature == null || timestamp == null) {
                    writeJson(exchange, 401, "{\"error\":\"missing signature headers\"}");
                    return;
                }

                Headers headers = Headers.builder()
                        .put("telnyx-signature-ed25519", signature)
                        .put("telnyx-timestamp", timestamp)
                        .build();

                UnwrapWebhookParams params = UnwrapWebhookParams.builder()
                        .body(rawBody)
                        .headers(headers)
                        .build();

                // unwrap() verifies the Ed25519 signature (using the configured public key) and the
                // replay window, then parses the body. It throws on a bad/stale signature or on a
                // parse error — both are treated as untrusted input below.
                UnwrapWebhookEvent event;
                try {
                    event = client.webhooks().unwrap(params);
                } catch (RuntimeException verificationError) {
                    LOGGER.log(Level.WARNING, "Webhook signature verification failed", verificationError);
                    writeJson(exchange, 401, "{\"error\":\"invalid signature\"}");
                    return;
                }

                // Only inbound SMS events carry an inboundMessage; ignore everything else.
                Optional<InboundMessageWebhookEvent> inbound = event.inboundMessage();
                if (inbound.isEmpty()) {
                    writeJson(exchange, 200, "{\"status\":\"ignored\"}");
                    return;
                }

                // Project convention: read event fields from data.payload.
                Optional<InboundMessagePayload> payload =
                        inbound.flatMap(InboundMessageWebhookEvent::data).flatMap(d -> d.payload());

                if (payload.isEmpty()) {
                    writeJson(exchange, 200, "{\"status\":\"ignored\"}");
                    return;
                }

                InboundMessagePayload msg = payload.get();
                String messageId = msg.id().orElse(null);
                String from = msg.from().flatMap(f -> f.phoneNumber()).orElse(null);
                String to = msg.to().flatMap(SmsWebhookHandler::firstRecipient).orElse(null);
                String text = msg.text().orElse("");

                LOGGER.info(() -> "[SMS Received] id=" + messageId + " from=" + from + " to=" + to);
                LOGGER.fine(() -> "Message text: " + text);

                // Acknowledge fast (2xx within 5s). In production, hand off heavy work to a queue.
                writeJson(exchange, 200,
                        "{\"status\":\"received\",\"message_id\":" + jsonString(messageId) + "}");
            } catch (RuntimeException unexpected) {
                // Never leak exception detail to the HTTP response.
                LOGGER.log(Level.SEVERE, "Unhandled error processing webhook", unexpected);
                safeWriteJson(exchange, 500, "{\"error\":\"internal server error\"}");
            }
        }

        private static Optional<String> firstRecipient(List<InboundMessagePayload.To> recipients) {
            if (recipients == null || recipients.isEmpty()) {
                return Optional.empty();
            }
            return recipients.get(0).phoneNumber();
        }
    }

    /** Simple liveness probe. */
    static final class HealthHandler implements HttpHandler {
        @Override
        public void handle(HttpExchange exchange) throws IOException {
            if (!"GET".equalsIgnoreCase(exchange.getRequestMethod())) {
                writeJson(exchange, 405, "{\"error\":\"method not allowed\"}");
                return;
            }
            writeJson(exchange, 200, "{\"status\":\"ok\"}");
        }
    }

    // ----- small HTTP helpers (no third-party web framework) -----

    private static String readBody(HttpExchange exchange) throws IOException {
        try (InputStream in = exchange.getRequestBody()) {
            return new String(in.readAllBytes(), StandardCharsets.UTF_8);
        }
    }

    private static String firstHeader(HttpExchange exchange, String name) {
        List<String> values = exchange.getRequestHeaders().get(name);
        if (values == null || values.isEmpty()) {
            return null;
        }
        return values.get(0);
    }

    private static void writeJson(HttpExchange exchange, int status, String json) throws IOException {
        byte[] bytes = json.getBytes(StandardCharsets.UTF_8);
        exchange.getResponseHeaders().set("Content-Type", "application/json");
        exchange.sendResponseHeaders(status, bytes.length);
        try (OutputStream out = exchange.getResponseBody()) {
            out.write(bytes);
        }
    }

    private static void safeWriteJson(HttpExchange exchange, int status, String json) {
        try {
            writeJson(exchange, status, json);
        } catch (IOException ioError) {
            LOGGER.log(Level.WARNING, "Failed to write error response", ioError);
        }
    }

    private static String jsonString(String value) {
        if (value == null) {
            return "null";
        }
        StringBuilder sb = new StringBuilder(value.length() + 2);
        sb.append('"');
        for (int i = 0; i < value.length(); i++) {
            char c = value.charAt(i);
            switch (c) {
                case '"' -> sb.append("\\\"");
                case '\\' -> sb.append("\\\\");
                case '\n' -> sb.append("\\n");
                case '\r' -> sb.append("\\r");
                case '\t' -> sb.append("\\t");
                default -> sb.append(c);
            }
        }
        sb.append('"');
        return sb.toString();
    }
}
