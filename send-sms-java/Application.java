package com.telnyx.example;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpServer;
import com.telnyx.sdk.client.TelnyxClient;
import com.telnyx.sdk.client.okhttp.TelnyxOkHttpClient;
import com.telnyx.sdk.errors.TelnyxServiceException;
import com.telnyx.sdk.models.messages.MessageSendParams;
import com.telnyx.sdk.models.messages.MessageSendResponse;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 * Minimal HTTP service that sends a single SMS through the Telnyx Messaging API.
 *
 * <p>Exposes {@code POST /sms/send} backed by the JDK built-in {@code HttpServer}.
 * One shared {@link TelnyxClient} is created from the environment. Telnyx SDK
 * objects are never returned directly; only a small, serializable JSON payload is.
 */
public final class Application {

    private static final Logger LOGGER = Logger.getLogger(Application.class.getName());
    private static final ObjectMapper MAPPER = new ObjectMapper();

    private Application() {
    }

    public static void main(String[] args) throws IOException {
        int port = parsePort(System.getenv("PORT"), 5000);

        // One shared client. TelnyxOkHttpClient.fromEnv() reads TELNYX_API_KEY
        // (and optional TELNYX_PUBLIC_KEY / TELNYX_BASE_URL) from the environment.
        TelnyxClient client = TelnyxOkHttpClient.fromEnv();

        String fromNumber = System.getenv("TELNYX_PHONE_NUMBER");
        if (fromNumber == null || fromNumber.isBlank()) {
            throw new IllegalStateException("TELNYX_PHONE_NUMBER environment variable not set");
        }

        HttpServer server = HttpServer.create(new InetSocketAddress(port), 0);
        server.createContext("/sms/send", new SendSmsHandler(client, fromNumber));
        server.setExecutor(null); // default executor
        server.start();

        LOGGER.info(() -> "Listening on http://localhost:" + port);
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

    /** Handles {@code POST /sms/send}. */
    static final class SendSmsHandler implements HttpHandler {

        private final TelnyxClient client;
        private final String fromNumber;

        SendSmsHandler(TelnyxClient client, String fromNumber) {
            this.client = client;
            this.fromNumber = fromNumber;
        }

        @Override
        public void handle(HttpExchange exchange) throws IOException {
            try {
                if (!"POST".equalsIgnoreCase(exchange.getRequestMethod())) {
                    sendError(exchange, 405, "Method not allowed");
                    return;
                }

                String to;
                String message;
                try (InputStream body = exchange.getRequestBody()) {
                    JsonNode root = MAPPER.readTree(body.readAllBytes());
                    to = textOrNull(root, "to");
                    message = textOrNull(root, "message");
                } catch (IOException parseError) {
                    sendError(exchange, 400, "Invalid JSON body");
                    return;
                }

                if (to == null || message == null) {
                    sendError(exchange, 400, "Missing required fields: 'to' and 'message'");
                    return;
                }

                // Validate E.164 before calling the API to avoid an obvious 422.
                if (!to.startsWith("+")) {
                    sendError(exchange, 400, "Phone number must be in E.164 format (e.g., +15551234567)");
                    return;
                }

                ObjectNode result = sendSms(to, message);
                sendJson(exchange, 200, result);
            } catch (TelnyxServiceException e) {
                // Log full detail server-side; never leak provider error text to the caller.
                LOGGER.log(Level.WARNING, "Telnyx API error", e);
                int status = e.statusCode();
                if (status == 401) {
                    sendError(exchange, 401, "Invalid API key");
                } else if (status == 429) {
                    sendError(exchange, 429, "Rate limit exceeded. Please slow down.");
                } else {
                    sendError(exchange, 502, "Failed to send message");
                }
            } catch (RuntimeException e) {
                LOGGER.log(Level.SEVERE, "Unexpected error sending SMS", e);
                sendError(exchange, 503, "Network error connecting to Telnyx");
            } finally {
                exchange.close();
            }
        }

        /** Sends the SMS and returns a small serializable result object. */
        private ObjectNode sendSms(String to, String message) {
            MessageSendParams params = MessageSendParams.builder()
                    .from(fromNumber)
                    .to(to)
                    .text(message)
                    .build();

            MessageSendResponse response = client.messages().send(params);

            // Getters return Optional in the Stainless SDK; chain defensively.
            String messageId = response.data()
                    .flatMap(d -> d.id())
                    .orElse(null);

            String status = response.data()
                    .flatMap(d -> d.to())
                    .flatMap(list -> list.stream().findFirst())
                    .flatMap(recipient -> recipient.status())
                    .map(Object::toString)
                    .orElse("unknown");

            ObjectNode result = MAPPER.createObjectNode();
            result.put("message_id", messageId);
            result.put("status", status);
            result.put("from", fromNumber);
            result.put("to", to);
            return result;
        }
    }

    private static String textOrNull(JsonNode root, String field) {
        JsonNode node = root.get(field);
        if (node == null || node.isNull()) {
            return null;
        }
        String value = node.asText();
        return value.isBlank() ? null : value;
    }

    private static void sendError(HttpExchange exchange, int status, String message) throws IOException {
        ObjectNode body = MAPPER.createObjectNode();
        body.put("error", message);
        sendJson(exchange, status, body);
    }

    private static void sendJson(HttpExchange exchange, int status, JsonNode body) throws IOException {
        byte[] bytes = MAPPER.writeValueAsBytes(body);
        exchange.getResponseHeaders().set("Content-Type", "application/json");
        exchange.sendResponseHeaders(status, bytes.length);
        try (OutputStream os = exchange.getResponseBody()) {
            os.write(bytes);
        }
    }
}
