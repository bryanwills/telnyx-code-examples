# Receive and Verify Inbound SMS with Telnyx and Java

Build a production-ready Java server (JDK `HttpServer`, no web framework) that receives inbound SMS via Telnyx webhooks, verifies the Ed25519 signature before trusting the payload, and reads the message from `data.payload`.

## How It Works

```
  Inbound SMS
        │
        ▼
  ┌───────────────────┐
  │ Telnyx Messaging  │
  └────────┬──────────┘
           │ POST webhook (Ed25519-signed)
           ▼
  ┌───────────────────────────┐
  │ JDK HttpServer            │
  │ /webhooks/sms             │
  └────────┬──────────────────┘
           │
           └──► verify → read data.payload → 200 OK
```

## Telnyx Products Used

- **Messaging** — send and receive messages with delivery receipts

## API Endpoints

- **Inbound Message webhook**: `POST /webhooks/sms` (your endpoint, called by Telnyx) -- [Webhook reference](https://developers.telnyx.com/docs/messaging/messages/receive-message)

## Prerequisites

- JDK 17+ (the webhook verification uses native `java.security` Ed25519, available on JDK 15+)
- Maven 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up)
- [API key](https://portal.telnyx.com/api-keys) and your Ed25519 [public key](https://portal.telnyx.com)
- [Phone number](https://portal.telnyx.com/numbers/my-numbers) enabled for inbound SMS
- [Messaging Profile](https://portal.telnyx.com/messaging/profiles) with an inbound webhook URL
- [ngrok](https://ngrok.com) to expose your local server to Telnyx

## Step 1: Set Up the Project

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/receive-sms-webhook-java
cp .env.example .env          # fill in your credentials
export $(grep -v '^#' .env | xargs)
```

The SDK reads `TELNYX_API_KEY` and `TELNYX_PUBLIC_KEY` from the process environment — Java has no `.env` auto-loading, so you must export them (or set them another way) before running.

## Step 2: Understand the Code

Everything lives in `Application.java`. One shared client is created at startup from the environment:

```java
TelnyxClient client = TelnyxOkHttpClient.fromEnv();
```

`fromEnv()` reads `TELNYX_API_KEY` and the Ed25519 `TELNYX_PUBLIC_KEY`. The public key is what `unwrap()` uses to verify webhook signatures — without it, verification (and the webhook) is rejected.

### Verify the signature, then read `data.payload`

The handler reads the raw request bytes first (the signature is computed over the exact bytes), builds the headers, and delegates verification and parsing to the SDK:

```java
String rawBody = readBody(exchange);

Headers headers = Headers.builder()
        .put("telnyx-signature-ed25519", signature)
        .put("telnyx-timestamp", timestamp)
        .build();

UnwrapWebhookParams params = UnwrapWebhookParams.builder()
        .body(rawBody)
        .headers(headers)
        .build();

UnwrapWebhookEvent event = client.webhooks().unwrap(params);
```

`unwrap()` verifies the Ed25519 signature over `"<telnyx-timestamp>|<raw body>"` (with a 300-second replay window) using the configured public key, then parses the body. It throws on a bad or stale signature, which the handler catches and answers with `401`.

Once verified, read the inbound message from `data.payload` using the SDK's typed accessors (all return `Optional`):

```java
Optional<InboundMessageWebhookEvent> inbound = event.inboundMessage();

Optional<InboundMessagePayload> payload =
        inbound.flatMap(InboundMessageWebhookEvent::data).flatMap(d -> d.payload());

InboundMessagePayload msg = payload.get();
String messageId = msg.id().orElse(null);
String from = msg.from().flatMap(f -> f.phoneNumber()).orElse(null);
String to = msg.to().flatMap(SmsWebhookHandler::firstRecipient).orElse(null);
String text = msg.text().orElse("");
```

The handler then acknowledges quickly so Telnyx stops retrying:

```java
writeJson(exchange, 200,
        "{\"status\":\"received\",\"message_id\":" + jsonString(messageId) + "}");
```

### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/webhooks/sms` | Receive + verify inbound SMS events from Telnyx |
| `GET` | `/health` | Liveness check |

Errors are logged via `java.util.logging`; the HTTP response only ever carries a generic message (e.g. `{"error":"internal server error"}`), never exception detail.

## Step 3: Run It

```bash
mvn -q compile
mvn -q exec:java
```

The server starts on `http://localhost:8080` (or `PORT` if set).

In a separate terminal, expose it for webhooks:

```bash
ngrok http 8080
```

Copy the HTTPS URL and set it in the [Telnyx Portal](https://portal.telnyx.com):

- **Messaging Profile** → Inbound Settings → Webhook URL → `https://<id>.ngrok.io/webhooks/sms`

Then assign your inbound-enabled number to that Messaging Profile.

## Step 4: Test It

**Health check:**

```bash
curl http://localhost:8080/health
```

**Real inbound SMS:** text your Telnyx number from a phone. Because every webhook must carry a valid Ed25519 signature, you cannot meaningfully forge one with `curl` — an unsigned request is correctly rejected with `401`. Watch the server logs print the verified inbound message.

## Going to Production

- **Persistence** — write verified messages to a database or queue instead of logging.
- **Fast acknowledgment** — return `200` immediately and move heavy work to a background worker so you stay under the 5-second window.
- **Clock sync** — keep the host clock NTP-synced; the 300-second replay window depends on it.
- **Monitoring** — alert on bursts of `401`s (possible misconfiguration or spoofing attempts).

## Resources

- [Source code and reference](./README.md)
- [API reference](./API.md)
- [Receive a Message guide](https://developers.telnyx.com/docs/messaging/messages/receive-message)
- [Webhook signing reference](https://developers.telnyx.com/api-reference/webhooks/verify-webhook-signatures)
- [Java SDK](https://developers.telnyx.com/development/sdk/java)
