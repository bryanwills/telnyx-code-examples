# Send Your First SMS with Telnyx and Java

Send an SMS message using the Telnyx Messaging API and Java SDK, exposed over a built-in JDK `HttpServer` endpoint. No web framework required.

## How It Works

```
  POST /sms/send  (JDK HttpServer)
        │
        ▼
  ┌─────────────────────────┐
  │ SendSmsHandler          │
  │ - parse JSON body       │
  │ - validate E.164        │
  │ - read from-number      │
  └────────────┬────────────┘
               │  client.messages().send(params)
               ▼
  ┌─────────────────────────┐
  │ Telnyx Messaging API    │
  └────────────┬────────────┘
               │
               └──► SMS delivered to recipient
```

## Telnyx Products Used

- **Messaging** — send and receive messages with delivery receipts

## API Endpoints

- **Send Message**: `POST /v2/messages` (via `client.messages().send(params)`) -- [API reference](https://developers.telnyx.com/api-reference/messages/send-a-message)

## Prerequisites

- JDK 17+ and Maven 3.6+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)
- [Phone number](https://portal.telnyx.com/numbers/my-numbers) with messaging enabled

## Step 1: Set Up the Project

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/send-sms-java
cp .env.example .env
```

Edit `.env` with your Telnyx credentials:

```
TELNYX_API_KEY=your_telnyx_api_key_here
TELNYX_PHONE_NUMBER=+15551234567
PORT=5000
```

The `HttpServer` reads process environment variables (not a `.env` file directly), so
load them into your shell before running:

```bash
set -a && . ./.env && set +a
```

## Step 2: Add the Dependency

`pom.xml` pins the current Telnyx Java SDK (the Stainless-generated `com.telnyx.sdk:telnyx`
artifact — note the artifact id is `telnyx`, not `telnyx-java`) and Jackson for JSON:

```xml
<dependency>
    <groupId>com.telnyx.sdk</groupId>
    <artifactId>telnyx</artifactId>
    <version>6.76.0</version>
</dependency>
<dependency>
    <groupId>com.fasterxml.jackson.core</groupId>
    <artifactId>jackson-databind</artifactId>
    <version>2.17.2</version>
</dependency>
```

## Step 3: Understand the Code

Everything lives in `Application.java`.

### Initialize the client

`main()` creates one shared client from the environment, validates the from-number, and
starts an `HttpServer` with a single handler:

```java
TelnyxClient client = TelnyxOkHttpClient.fromEnv();

String fromNumber = System.getenv("TELNYX_PHONE_NUMBER");
if (fromNumber == null || fromNumber.isBlank()) {
    throw new IllegalStateException("TELNYX_PHONE_NUMBER environment variable not set");
}

HttpServer server = HttpServer.create(new InetSocketAddress(port), 0);
server.createContext("/sms/send", new SendSmsHandler(client, fromNumber));
server.start();
```

`TelnyxOkHttpClient.fromEnv()` reads `TELNYX_API_KEY` (and optional `TELNYX_PUBLIC_KEY` /
`TELNYX_BASE_URL`) from the environment.

### Send the message

The handler builds `MessageSendParams` and calls `client.messages().send(params)`. SDK
getters return `Optional`, so the response is read with `Optional` chaining and only a
small, serializable result is returned to the caller:

```java
MessageSendParams params = MessageSendParams.builder()
        .from(fromNumber)
        .to(to)
        .text(message)
        .build();

MessageSendResponse response = client.messages().send(params);

String messageId = response.data()
        .flatMap(d -> d.id())
        .orElse(null);

String status = response.data()
        .flatMap(d -> d.to())
        .flatMap(list -> list.stream().findFirst())
        .flatMap(recipient -> recipient.status())
        .map(Object::toString)
        .orElse("unknown");
```

### Production-safe error handling

`TelnyxServiceException` is caught in the handler. Its `statusCode()` is mapped to an HTTP
status; the full exception is logged via `java.util.logging` and the caller only ever sees
a generic message — provider error text is never leaked in the response body:

```java
} catch (TelnyxServiceException e) {
    LOGGER.log(Level.WARNING, "Telnyx API error", e);
    int status = e.statusCode();
    if (status == 401) {
        sendError(exchange, 401, "Invalid API key");
    } else if (status == 429) {
        sendError(exchange, 429, "Rate limit exceeded. Please slow down.");
    } else {
        sendError(exchange, 502, "Failed to send message");
    }
}
```

### All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/sms/send` | Send a single SMS |

## Step 4: Run It

```bash
mvn -q compile
mvn -q exec:java
```

The server starts on `http://localhost:5000`.

## Step 5: Test It

```bash
curl -X POST http://localhost:5000/sms/send \
  -H "Content-Type: application/json" \
  -d '{
    "to": "+12125559999",
    "message": "Hello from Telnyx and Java"
  }'
```

A successful call returns the message ID, status, and the from/to numbers.

## Going to Production

- **Authentication** — add API key or token validation on your endpoint
- **Structured logging** — emit JSON logs with request IDs instead of the default JUL format
- **Rate limiting** — protect the endpoint from abuse
- **Retries** — retry on `429` and `503` responses with backoff
- **Monitoring** — track send success rate and add alerting

## Resources

- [Source overview](./README.md)
- [Typed endpoint reference](./API.md)
- [Messaging quickstart](https://developers.telnyx.com/docs/messaging)
- [Send a Message — API Reference](https://developers.telnyx.com/api-reference/messages/send-a-message)
- [Java SDK](https://developers.telnyx.com/development/sdk/java)
- [Telnyx Portal](https://portal.telnyx.com)
