package com.telnyx.examples;

import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpServer;
import com.telnyx.sdk.client.TelnyxClient;
import com.telnyx.sdk.client.okhttp.TelnyxOkHttpClient;
import com.telnyx.sdk.models.simcards.actions.ActionEnableResponse;

import java.io.IOException;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.logging.Level;
import java.util.logging.Logger;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Activate (enable) a Telnyx IoT SIM card over HTTP.
 *
 * <p>Single-file example built on the JDK's {@link com.sun.net.httpserver.HttpServer}
 * (no web framework) and the Telnyx Java SDK ({@code com.telnyx.sdk:telnyx}). It exposes
 * one route, {@code POST /sim/activate}, which reads a JSON body with a {@code sim_card_id}
 * field and calls {@code client.simCards().actions().enable(simCardId)}.
 */
public final class Application {

    private static final Logger LOG = Logger.getLogger(Application.class.getName());

    /** Extracts the value of the JSON "sim_card_id" field without pulling in a JSON parser. */
    private static final Pattern SIM_CARD_ID =
            Pattern.compile("\"sim_card_id\"\\s*:\\s*\"([^\"]+)\"");

    /** Pulls an HTTP status code out of an SDK error message (e.g. "status code 401"). */
    private static final Pattern HTTP_STATUS =
            Pattern.compile("\\b(4\\d{2}|5\\d{2})\\b");

    private final TelnyxClient client;

    private Application(TelnyxClient client) {
        this.client = client;
    }

    public static void main(String[] args) throws IOException {
        // Fail fast if the API key is not configured. TelnyxOkHttpClient.fromEnv()
        // reads TELNYX_API_KEY (and optional TELNYX_PUBLIC_KEY / TELNYX_BASE_URL).
        if (isBlank(System.getenv("TELNYX_API_KEY"))) {
            LOG.severe("TELNYX_API_KEY environment variable is not set. "
                    + "Copy .env.example to .env and export it before running.");
            System.exit(1);
        }

        TelnyxClient client = TelnyxOkHttpClient.fromEnv();
        Application app = new Application(client);

        int port = parsePort(System.getenv("PORT"), 8080);
        HttpServer server = HttpServer.create(new InetSocketAddress(port), 0);
        server.createContext("/sim/activate", app.new ActivateHandler());
        server.setExecutor(null); // default executor
        server.start();

        LOG.info(() -> "Listening on http://localhost:" + port + " (POST /sim/activate)");
    }

    /** Handles {@code POST /sim/activate}. */
    private final class ActivateHandler implements HttpHandler {

        @Override
        public void handle(HttpExchange exchange) throws IOException {
            try {
                if (!"POST".equalsIgnoreCase(exchange.getRequestMethod())) {
                    respond(exchange, 405, "{\"error\":\"Method not allowed. Use POST.\"}");
                    return;
                }

                String body = new String(
                        exchange.getRequestBody().readAllBytes(), StandardCharsets.UTF_8);

                String simCardId = extractSimCardId(body);
                if (isBlank(simCardId)) {
                    respond(exchange, 400,
                            "{\"error\":\"Missing required field: 'sim_card_id'\"}");
                    return;
                }

                // Enable (activate) the SIM. The convenience overload takes the id directly.
                ActionEnableResponse response = client.simCards().actions().enable(simCardId);

                String id = response.data()
                        .flatMap(action -> action.id())
                        .orElse(simCardId);
                String status = response.data()
                        .flatMap(action -> action.status())
                        .map(Object::toString)
                        .orElse("requested");

                String json = "{"
                        + "\"id\":\"" + escape(id) + "\","
                        + "\"sim_card_id\":\"" + escape(simCardId) + "\","
                        + "\"status\":\"" + escape(status) + "\","
                        + "\"message\":\"SIM card enable requested\""
                        + "}";
                respond(exchange, 200, json);

            } catch (RuntimeException e) {
                // SDK errors surface as runtime exceptions. Log the real cause
                // server-side; never leak exception details to the client. Map the
                // upstream HTTP status (parsed from the message) to a generic reply.
                LOG.log(Level.WARNING, "Telnyx API error handling /sim/activate", e);
                int status = upstreamStatus(e);
                if (status == 401) {
                    respond(exchange, 401, "{\"error\":\"Invalid API key\"}");
                } else if (status == 404) {
                    respond(exchange, 404, "{\"error\":\"SIM card not found\"}");
                } else if (status == 422) {
                    respond(exchange, 422,
                            "{\"error\":\"SIM card cannot be activated from its current status\"}");
                } else if (status == 429) {
                    respond(exchange, 429,
                            "{\"error\":\"Rate limit exceeded. Please slow down.\"}");
                } else {
                    respond(exchange, 502, "{\"error\":\"Upstream Telnyx API error\"}");
                }
            } catch (Exception e) {
                // Catch-all: log the real cause, return a generic message.
                LOG.log(Level.SEVERE, "Unexpected error handling /sim/activate", e);
                respond(exchange, 500, "{\"error\":\"Internal server error\"}");
            }
        }
    }

    private static String extractSimCardId(String body) {
        if (body == null) {
            return null;
        }
        Matcher m = SIM_CARD_ID.matcher(body);
        return m.find() ? m.group(1).trim() : null;
    }

    private static void respond(HttpExchange exchange, int statusCode, String json)
            throws IOException {
        byte[] bytes = json.getBytes(StandardCharsets.UTF_8);
        exchange.getResponseHeaders().set("Content-Type", "application/json");
        exchange.sendResponseHeaders(statusCode, bytes.length);
        try (OutputStream os = exchange.getResponseBody()) {
            os.write(bytes);
        }
    }

    /**
     * Best-effort extraction of the upstream HTTP status from an SDK error. Returns 0 when
     * no status can be determined, in which case the caller responds with a generic 502.
     */
    private static int upstreamStatus(Throwable e) {
        for (Throwable t = e; t != null; t = t.getCause()) {
            String msg = t.getMessage();
            if (msg != null) {
                Matcher m = HTTP_STATUS.matcher(msg);
                if (m.find()) {
                    try {
                        return Integer.parseInt(m.group(1));
                    } catch (NumberFormatException ignored) {
                        // fall through
                    }
                }
            }
        }
        return 0;
    }

    private static boolean isBlank(String s) {
        return s == null || s.trim().isEmpty();
    }

    /** Minimal JSON string escaping for the small set of values we emit. */
    private static String escape(String s) {
        return s.replace("\\", "\\\\").replace("\"", "\\\"");
    }

    private static int parsePort(String value, int fallback) {
        if (isBlank(value)) {
            return fallback;
        }
        try {
            return Integer.parseInt(value.trim());
        } catch (NumberFormatException e) {
            return fallback;
        }
    }
}
