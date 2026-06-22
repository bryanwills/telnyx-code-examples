# Make Outbound Phone Calls with Telnyx (Java)

A standalone walkthrough for placing an outbound Call Control call in Java using the Telnyx Java SDK and the JDK's built-in HTTP server — no Spring, Spark, or Javalin.

## How It Works

```
  POST /calls/dial  {"to": "+1..."}
          │
          ▼
  HttpServer (JDK)  ──  client.calls().dial(params)  ──▶  Telnyx Call Control
          │                                          ◀──  CallDialResponse
          ▼
  { "call_control_id": "...", "from": "...", "to": "..." }
```

## Telnyx Products Used

- **Voice** — programmatic Call Control with webhooks for every call state change.
- **Call Control** — `calls.dial` places the call; `call.answered` / `call.hangup` webhooks report progress.

## Prerequisites

- JDK 17+ (the SDK's webhook signature verification uses the JDK-native `Ed25519` provider, available on JDK 15+).
- Maven 3.6+.
- A [Telnyx account](https://portal.telnyx.com/sign-up) with a funded balance.
- An [API key](https://portal.telnyx.com/api-keys).
- A [phone number](https://portal.telnyx.com/numbers/my-numbers) with voice enabled.
- A [Call Control Application](https://portal.telnyx.com/call-control/applications) (its ID is your `connection_id`).
- [ngrok](https://ngrok.com) to expose your local server for webhooks.

## Step 1: Set Up the Project

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/make-outbound-phone-call-java
cp .env.example .env
```

The dependency lives in `pom.xml`. Note the artifact id is `telnyx`, not `telnyx-java`:

```xml
<dependency>
    <groupId>com.telnyx.sdk</groupId>
    <artifactId>telnyx</artifactId>
    <version>6.76.0</version>
</dependency>
```

## Step 2: Create the Client Once

`Application.main` builds a single `TelnyxClient` from the environment and shares it across all handlers:

```java
TelnyxClient client = TelnyxOkHttpClient.fromEnv();

String fromNumber = requireEnv("TELNYX_PHONE_NUMBER");
String connectionId = requireEnv("TELNYX_CONNECTION_ID");
String webhookUrl = System.getenv("TELNYX_WEBHOOK_URL"); // optional
```

`fromEnv()` reads `TELNYX_API_KEY` (and the optional `TELNYX_PUBLIC_KEY` used for webhook verification) from the environment.

## Step 3: Place the Call

The `DialHandler` builds `CallDialParams` and calls `client.calls().dial(...)`. `connectionId`, `from`, and `to` are required; `webhookUrl` is optional. Response getters return `Optional`:

```java
CallDialParams.Builder params = CallDialParams.builder()
        .connectionId(connectionId)
        .from(fromNumber)
        .to(toNumber);
if (webhookUrl != null && !webhookUrl.isBlank()) {
    params.webhookUrl(webhookUrl);
}

CallDialResponse response = client.calls().dial(params.build());

String callControlId = response.data().map(CallDialResponse.Data::callControlId).orElse(null);
```

The `to` field is validated for E.164 (`startsWith("+")`) before the call, and any upstream failure is logged server-side while the client receives a generic `502` — exception detail is never leaked to the HTTP response.

## Step 4: Verify Inbound Webhooks

Telnyx signs each webhook with Ed25519 over `"{timestamp}|{body}"`. The `WebhookHandler` reads the raw bytes before parsing, then verifies via `client.webhooks().unwrap(...)`:

```java
byte[] rawBody = readBody(exchange);
String signature = firstHeader(exchange, "telnyx-signature-ed25519");
String timestamp = firstHeader(exchange, "telnyx-timestamp");

Headers headers = Headers.builder()
        .put("telnyx-signature-ed25519", signature)
        .put("telnyx-timestamp", timestamp)
        .build();
UnwrapWebhookParams params = UnwrapWebhookParams.builder()
        .body(new String(rawBody, StandardCharsets.UTF_8))
        .headers(headers)
        .build();
UnwrapWebhookEvent event = client.webhooks().unwrap(params);
```

`unwrap` throws on a bad signature or stale timestamp (caught and turned into a `401`). Once verified, event fields are read from `data.payload`:

```java
event.callAnswered().ifPresent(e ->
        LOGGER.info(() -> "call.answered: " + e.data()
                .flatMap(d -> d.payload())
                .flatMap(p -> p.callControlId())
                .orElse("(unknown)")));
```

Verification requires `TELNYX_PUBLIC_KEY` to be set.

## Step 5: Run It

```bash
set -a && . ./.env && set +a   # export .env into the shell
mvn compile
mvn exec:java                  # http://localhost:8080
```

In a second terminal, expose the server and set the URL in the Portal:

```bash
ngrok http 8080
```

- **Call Control Application** → Webhook URL → `https://<id>.ngrok.io/webhooks/voice`

## Step 6: Test It

Health check:

```bash
curl http://localhost:8080/health
```

Place a call:

```bash
curl -X POST http://localhost:8080/calls/dial \
  -H "Content-Type: application/json" \
  -d '{"to": "+12125551234"}'
```

You should receive a JSON body with a `call_control_id`, and your destination number should ring.

## Going to Production

- **Authentication** — add an API key or signed-token check on `/calls/dial`.
- **Webhook verification** — keep `TELNYX_PUBLIC_KEY` configured; never skip the `unwrap` step.
- **Observability** — the example logs detail server-side via `java.util.logging`; ship those logs and add health-check alerts.
- **Rate limiting** — protect `/calls/dial` from abuse.

## Resources

- [Source code and reference](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/make-outbound-phone-call-java/README.md)
- [Call Control guide](https://developers.telnyx.com/docs/voice/call-control)
- [Dial API reference](https://developers.telnyx.com/api-reference/call-commands/dial)
- [Telnyx Java SDK](https://developers.telnyx.com/development/sdk/java)
