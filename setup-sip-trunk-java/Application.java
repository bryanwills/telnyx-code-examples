package com.telnyx.examples.sip;

import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpServer;
import com.telnyx.sdk.client.TelnyxClient;
import com.telnyx.sdk.client.okhttp.TelnyxOkHttpClient;
import com.telnyx.sdk.errors.TelnyxException;
import com.telnyx.sdk.models.credentialconnections.CredentialConnection;
import com.telnyx.sdk.models.credentialconnections.CredentialConnectionCreateParams;
import com.telnyx.sdk.models.credentialconnections.CredentialConnectionCreateResponse;
import com.telnyx.sdk.models.credentialconnections.CredentialConnectionListPage;
import com.telnyx.sdk.models.credentialconnections.CredentialConnectionRetrieveResponse;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 * Minimal REST API that creates, lists, and retrieves Telnyx credential (SIP)
 * connections using the Telnyx Java SDK (com.telnyx.sdk:telnyx) and the JDK's
 * built-in {@link com.sun.net.httpserver.HttpServer} (no web framework).
 *
 * <p>Routes:
 * <ul>
 *   <li>{@code POST /sip-connections} — create a credential connection</li>
 *   <li>{@code GET  /sip-connections} — list credential connections</li>
 *   <li>{@code GET  /sip-connections/{id}} — retrieve one credential connection</li>
 *   <li>{@code GET  /health} — liveness probe</li>
 * </ul>
 */
public final class Application {

    private static final Logger LOGGER = Logger.getLogger(Application.class.getName());

    /** Shared, thread-safe Telnyx client. Created once from environment variables. */
    private final TelnyxClient client;

    private Application(TelnyxClient client) {
        this.client = client;
    }

    public static void main(String[] args) throws IOException {
        if (System.getenv("TELNYX_API_KEY") == null || System.getenv("TELNYX_API_KEY").isBlank()) {
            LOGGER.severe("TELNYX_API_KEY environment variable is not set.");
            System.exit(1);
        }

        // TelnyxOkHttpClient.fromEnv() reads TELNYX_API_KEY (and optional
        // TELNYX_PUBLIC_KEY / TELNYX_BASE_URL) from the environment.
        TelnyxClient client = TelnyxOkHttpClient.fromEnv();
        Application app = new Application(client);

        int port = port();
        HttpServer server = HttpServer.create(new InetSocketAddress(port), 0);
        server.createContext("/sip-connections", app::handleSipConnections);
        server.createContext("/health", Application::handleHealth);
        server.setExecutor(null); // default executor
        server.start();

        LOGGER.info(() -> "SIP Trunking API listening on http://localhost:" + port);
    }

    private static int port() {
        String raw = System.getenv("PORT");
        if (raw == null || raw.isBlank()) {
            return 8080;
        }
        try {
            return Integer.parseInt(raw.trim());
        } catch (NumberFormatException e) {
            return 8080;
        }
    }

    // ------------------------------------------------------------------
    // Routing
    // ------------------------------------------------------------------

    private void handleSipConnections(HttpExchange exchange) throws IOException {
        try {
            String method = exchange.getRequestMethod();
            String path = exchange.getRequestURI().getPath();
            // Path segment after "/sip-connections" — empty for the collection route.
            String remainder = path.substring("/sip-connections".length());
            if (remainder.startsWith("/")) {
                remainder = remainder.substring(1);
            }

            if ("POST".equalsIgnoreCase(method) && remainder.isEmpty()) {
                createConnection(exchange);
            } else if ("GET".equalsIgnoreCase(method) && remainder.isEmpty()) {
                listConnections(exchange);
            } else if ("GET".equalsIgnoreCase(method)) {
                retrieveConnection(exchange, remainder);
            } else {
                sendJson(exchange, 405, Map.of("error", "Method not allowed"));
            }
        } catch (IllegalArgumentException e) {
            // Client input error — safe to surface the validation message.
            sendJson(exchange, 400, Map.of("error", e.getMessage()));
        } catch (TelnyxException e) {
            // Log the detail internally; return a generic message to the caller.
            LOGGER.log(Level.WARNING, "Telnyx API error", e);
            sendJson(exchange, 502, Map.of("error", "Upstream Telnyx API error"));
        } catch (RuntimeException e) {
            LOGGER.log(Level.SEVERE, "Unexpected error", e);
            sendJson(exchange, 500, Map.of("error", "Internal server error"));
        }
    }

    private static void handleHealth(HttpExchange exchange) throws IOException {
        if (!"GET".equalsIgnoreCase(exchange.getRequestMethod())) {
            sendJson(exchange, 405, Map.of("error", "Method not allowed"));
            return;
        }
        sendJson(exchange, 200, Map.of("status", "ok"));
    }

    // ------------------------------------------------------------------
    // Operations
    // ------------------------------------------------------------------

    /** {@code POST /sip-connections} — create a credential connection. */
    private void createConnection(HttpExchange exchange) throws IOException {
        String body = readBody(exchange);
        Map<String, String> fields = parseFlatJsonObject(body);

        String connectionName = required(fields, "connection_name");
        String userName = required(fields, "user_name");
        String password = required(fields, "password");

        CredentialConnectionCreateParams params = CredentialConnectionCreateParams.builder()
                .connectionName(connectionName)
                .userName(userName)
                .password(password)
                .build();

        CredentialConnectionCreateResponse response = client.credentialConnections().create(params);
        Map<String, Object> result = response.data()
                .map(Application::toMap)
                .orElseGet(LinkedHashMap::new);
        sendJson(exchange, 201, result);
    }

    /** {@code GET /sip-connections} — list credential connections. */
    private void listConnections(HttpExchange exchange) throws IOException {
        CredentialConnectionListPage page = client.credentialConnections().list();

        List<Map<String, Object>> connections = new ArrayList<>();
        for (CredentialConnection connection : page.autoPager()) {
            connections.add(toMap(connection));
        }

        Map<String, Object> result = new LinkedHashMap<>();
        result.put("data", connections);
        sendJson(exchange, 200, result);
    }

    /** {@code GET /sip-connections/{id}} — retrieve one credential connection. */
    private void retrieveConnection(HttpExchange exchange, String id) throws IOException {
        if (id == null || id.isBlank()) {
            throw new IllegalArgumentException("Connection id is required");
        }

        CredentialConnectionRetrieveResponse response = client.credentialConnections().retrieve(id);
        Map<String, Object> result = response.data()
                .map(Application::toMap)
                .orElseGet(LinkedHashMap::new);
        sendJson(exchange, 200, result);
    }

    // ------------------------------------------------------------------
    // Serialization helpers
    // ------------------------------------------------------------------

    /**
     * Extract the JSON-safe fields from a {@link CredentialConnection}. The SDK
     * model is not directly serialized; only non-sensitive fields are exposed
     * (the password is never returned).
     */
    private static Map<String, Object> toMap(CredentialConnection connection) {
        Map<String, Object> map = new LinkedHashMap<>();
        connection.id().ifPresent(v -> map.put("id", v));
        connection.connectionName().ifPresent(v -> map.put("connection_name", v));
        connection.userName().ifPresent(v -> map.put("user_name", v));
        return map;
    }

    private static String required(Map<String, String> fields, String key) {
        String value = fields.get(key);
        if (value == null || value.isBlank()) {
            throw new IllegalArgumentException("Missing required field: " + key);
        }
        return value;
    }

    private static String readBody(HttpExchange exchange) throws IOException {
        try (InputStream in = exchange.getRequestBody()) {
            return new String(in.readAllBytes(), StandardCharsets.UTF_8);
        }
    }

    private static void sendJson(HttpExchange exchange, int status, Map<String, ?> payload)
            throws IOException {
        byte[] bytes = toJson(payload).getBytes(StandardCharsets.UTF_8);
        exchange.getResponseHeaders().set("Content-Type", "application/json");
        exchange.sendResponseHeaders(status, bytes.length);
        try (OutputStream out = exchange.getResponseBody()) {
            out.write(bytes);
        }
    }

    // ------------------------------------------------------------------
    // Tiny dependency-free JSON helpers (request body + response rendering).
    // For a flat object of string values only; sufficient for this example.
    // ------------------------------------------------------------------

    /**
     * Parse a flat JSON object ({@code {"a":"b","c":"d"}}) into a map of strings.
     * Only string values are supported; nested objects/arrays are not parsed.
     */
    static Map<String, String> parseFlatJsonObject(String json) {
        Map<String, String> out = new LinkedHashMap<>();
        if (json == null) {
            return out;
        }
        String trimmed = json.trim();
        if (trimmed.isEmpty()) {
            return out;
        }
        if (!trimmed.startsWith("{") || !trimmed.endsWith("}")) {
            throw new IllegalArgumentException("Request body must be a JSON object");
        }
        String inner = trimmed.substring(1, trimmed.length() - 1);
        int i = 0;
        int n = inner.length();
        while (i < n) {
            while (i < n && (Character.isWhitespace(inner.charAt(i)) || inner.charAt(i) == ',')) {
                i++;
            }
            if (i >= n) {
                break;
            }
            if (inner.charAt(i) != '"') {
                throw new IllegalArgumentException("Malformed JSON: expected string key");
            }
            StringBuilder key = new StringBuilder();
            i = readString(inner, i, key);
            while (i < n && Character.isWhitespace(inner.charAt(i))) {
                i++;
            }
            if (i >= n || inner.charAt(i) != ':') {
                throw new IllegalArgumentException("Malformed JSON: expected ':'");
            }
            i++; // skip ':'
            while (i < n && Character.isWhitespace(inner.charAt(i))) {
                i++;
            }
            if (i >= n || inner.charAt(i) != '"') {
                throw new IllegalArgumentException("Malformed JSON: only string values are supported");
            }
            StringBuilder value = new StringBuilder();
            i = readString(inner, i, value);
            out.put(key.toString(), value.toString());
        }
        return out;
    }

    /** Read a JSON string starting at the opening quote; returns index past the closing quote. */
    private static int readString(String s, int start, StringBuilder sink) {
        int i = start + 1; // skip opening quote
        int n = s.length();
        while (i < n) {
            char c = s.charAt(i);
            if (c == '\\' && i + 1 < n) {
                char next = s.charAt(i + 1);
                switch (next) {
                    case '"': sink.append('"'); break;
                    case '\\': sink.append('\\'); break;
                    case '/': sink.append('/'); break;
                    case 'n': sink.append('\n'); break;
                    case 't': sink.append('\t'); break;
                    case 'r': sink.append('\r'); break;
                    default: sink.append(next); break;
                }
                i += 2;
            } else if (c == '"') {
                return i + 1; // past closing quote
            } else {
                sink.append(c);
                i++;
            }
        }
        throw new IllegalArgumentException("Malformed JSON: unterminated string");
    }

    /** Render a flat map (string/number/boolean/list-of-maps values) as JSON. */
    @SuppressWarnings("unchecked")
    static String toJson(Object value) {
        StringBuilder sb = new StringBuilder();
        if (value == null) {
            sb.append("null");
        } else if (value instanceof Map<?, ?> map) {
            sb.append('{');
            boolean first = true;
            for (Map.Entry<?, ?> entry : map.entrySet()) {
                if (!first) {
                    sb.append(',');
                }
                first = false;
                appendString(sb, String.valueOf(entry.getKey()));
                sb.append(':');
                sb.append(toJson(entry.getValue()));
            }
            sb.append('}');
        } else if (value instanceof List<?> list) {
            sb.append('[');
            boolean first = true;
            for (Object item : list) {
                if (!first) {
                    sb.append(',');
                }
                first = false;
                sb.append(toJson(item));
            }
            sb.append(']');
        } else if (value instanceof Number || value instanceof Boolean) {
            sb.append(value);
        } else {
            appendString(sb, String.valueOf(value));
        }
        return sb.toString();
    }

    private static void appendString(StringBuilder sb, String s) {
        sb.append('"');
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            switch (c) {
                case '"': sb.append("\\\""); break;
                case '\\': sb.append("\\\\"); break;
                case '\n': sb.append("\\n"); break;
                case '\r': sb.append("\\r"); break;
                case '\t': sb.append("\\t"); break;
                default: sb.append(c); break;
            }
        }
        sb.append('"');
    }
}
