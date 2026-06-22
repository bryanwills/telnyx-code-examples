package com.telnyx.examples;

import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;
import com.telnyx.sdk.client.TelnyxClient;
import com.telnyx.sdk.client.okhttp.TelnyxOkHttpClient;
import com.telnyx.sdk.models.ai.assistants.AssistantChatParams;
import com.telnyx.sdk.models.ai.assistants.AssistantChatResponse;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.Executors;
import java.util.logging.Level;
import java.util.logging.Logger;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Production-ready JDK HttpServer that chats with a Telnyx AI Assistant.
 *
 * <p>POST /chat with a JSON body {"message": "...", "conversation_id": "..."} sends the
 * message to the assistant configured by TELNYX_ASSISTANT_ID and returns the reply plus a
 * stable conversation id so the caller can thread follow-up turns.</p>
 *
 * <p>The Telnyx client is created once from environment variables and shared across requests.
 * Errors are logged server-side; HTTP responses carry generic messages only.</p>
 */
public final class Application {

    private static final Logger LOGGER = Logger.getLogger(Application.class.getName());

    /** Single shared client, initialized from TELNYX_API_KEY (and optional TELNYX_BASE_URL). */
    private static final TelnyxClient CLIENT = TelnyxOkHttpClient.fromEnv();

    /** Assistant to chat with; required for the /chat route. */
    private static final String ASSISTANT_ID = System.getenv("TELNYX_ASSISTANT_ID");

    // Minimal JSON string extractors for the two fields we accept. Keeps the example
    // dependency-free (no Jackson/Gson) while still parsing simple request bodies.
    private static final Pattern MESSAGE_FIELD =
            Pattern.compile("\"message\"\\s*:\\s*\"((?:\\\\.|[^\"\\\\])*)\"");
    private static final Pattern CONVERSATION_ID_FIELD =
            Pattern.compile("\"conversation_id\"\\s*:\\s*\"((?:\\\\.|[^\"\\\\])*)\"");

    private Application() {
    }

    public static void main(String[] args) throws IOException {
        int port = parsePort(System.getenv("PORT"), 8080);

        HttpServer server = HttpServer.create(new InetSocketAddress(port), 0);
        server.createContext("/chat", Application::handleChat);
        server.createContext("/health", Application::handleHealth);
        server.setExecutor(Executors.newFixedThreadPool(8));
        server.start();

        LOGGER.info("Listening on http://localhost:" + port);
        LOGGER.info("Routes: POST /chat, GET /health");
    }

    /** POST /chat — send a user message to the AI assistant and return its reply. */
    private static void handleChat(HttpExchange exchange) throws IOException {
        try {
            if (!"POST".equalsIgnoreCase(exchange.getRequestMethod())) {
                respond(exchange, 405, "{\"error\":\"Method not allowed\"}");
                return;
            }

            if (ASSISTANT_ID == null || ASSISTANT_ID.isBlank()) {
                LOGGER.warning("TELNYX_ASSISTANT_ID is not set");
                respond(exchange, 500, "{\"error\":\"Server is not configured\"}");
                return;
            }

            String body = readBody(exchange);
            String userMessage = extract(MESSAGE_FIELD, body);
            if (userMessage == null || userMessage.isBlank()) {
                respond(exchange, 400, "{\"error\":\"Missing required field: 'message'\"}");
                return;
            }

            // Reuse the caller's conversation id to thread the conversation, or mint a new one.
            String conversationId = extract(CONVERSATION_ID_FIELD, body);
            if (conversationId == null || conversationId.isBlank()) {
                conversationId = UUID.randomUUID().toString();
            }

            String reply = chat(userMessage, conversationId);

            Map<String, String> payload = new HashMap<>();
            payload.put("assistant_id", ASSISTANT_ID);
            payload.put("conversation_id", conversationId);
            payload.put("reply", reply);
            respond(exchange, 200, toJson(payload));

        } catch (RuntimeException e) {
            // Telnyx SDK errors are unchecked (auth, rate limit, upstream status). Log the
            // details server-side and return a generic message so nothing leaks to the client.
            LOGGER.log(Level.WARNING, "Telnyx API error", e);
            respond(exchange, 502, "{\"error\":\"Upstream AI request failed\"}");
        } catch (Exception e) {
            LOGGER.log(Level.SEVERE, "Unexpected error handling /chat", e);
            respond(exchange, 500, "{\"error\":\"Internal server error\"}");
        }
    }

    /**
     * Send one user turn to the assistant. {@code conversationId} threads multi-turn
     * conversations; pass the same value back on each follow-up message.
     */
    private static String chat(String userMessage, String conversationId) {
        AssistantChatParams params = AssistantChatParams.builder()
                .content(userMessage)
                .conversationId(conversationId)
                .build();

        AssistantChatResponse response = CLIENT.ai().assistants().chat(ASSISTANT_ID, params);
        return response.content();
    }

    /** GET /health — liveness probe. */
    private static void handleHealth(HttpExchange exchange) throws IOException {
        if (!"GET".equalsIgnoreCase(exchange.getRequestMethod())) {
            respond(exchange, 405, "{\"error\":\"Method not allowed\"}");
            return;
        }
        respond(exchange, 200, "{\"status\":\"ok\"}");
    }

    // ---- helpers ----

    private static int parsePort(String value, int fallback) {
        if (value == null || value.isBlank()) {
            return fallback;
        }
        try {
            return Integer.parseInt(value.trim());
        } catch (NumberFormatException e) {
            LOGGER.warning("Invalid PORT '" + value + "', using " + fallback);
            return fallback;
        }
    }

    private static String readBody(HttpExchange exchange) throws IOException {
        try (InputStream in = exchange.getRequestBody()) {
            return new String(in.readAllBytes(), StandardCharsets.UTF_8);
        }
    }

    private static String extract(Pattern pattern, String body) {
        if (body == null) {
            return null;
        }
        Matcher matcher = pattern.matcher(body);
        if (!matcher.find()) {
            return null;
        }
        return unescapeJson(matcher.group(1));
    }

    private static String unescapeJson(String raw) {
        return raw
                .replace("\\\"", "\"")
                .replace("\\n", "\n")
                .replace("\\t", "\t")
                .replace("\\/", "/")
                .replace("\\\\", "\\");
    }

    private static String toJson(Map<String, String> map) {
        StringBuilder sb = new StringBuilder("{");
        boolean first = true;
        for (Map.Entry<String, String> entry : map.entrySet()) {
            if (!first) {
                sb.append(',');
            }
            first = false;
            sb.append('"').append(escapeJson(entry.getKey())).append('"')
              .append(':')
              .append('"').append(escapeJson(entry.getValue())).append('"');
        }
        return sb.append('}').toString();
    }

    private static String escapeJson(String value) {
        if (value == null) {
            return "";
        }
        return value
                .replace("\\", "\\\\")
                .replace("\"", "\\\"")
                .replace("\n", "\\n")
                .replace("\r", "\\r")
                .replace("\t", "\\t");
    }

    private static void respond(HttpExchange exchange, int status, String json) throws IOException {
        byte[] bytes = json.getBytes(StandardCharsets.UTF_8);
        exchange.getResponseHeaders().set("Content-Type", "application/json");
        exchange.sendResponseHeaders(status, bytes.length);
        try (OutputStream out = exchange.getResponseBody()) {
            out.write(bytes);
        }
    }
}
