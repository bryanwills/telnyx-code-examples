# Activate a Telnyx SIM Card with Java

Activate a Telnyx IoT SIM card over HTTP using the Telnyx Java SDK and the JDK's built-in `HttpServer` — no web framework required.

## How It Works

```
  POST /sim/activate
        │
        ▼
  ┌──────────────────────┐
  │  JDK HttpServer       │
  │  ActivateHandler      │
  │  (parse + validate)   │
  └──────────┬───────────┘
             │ client.simCards().actions().enable(simCardId)
             ▼
  ┌──────────────────────┐
  │   Telnyx IoT SIM      │
  └──────────┬───────────┘
             │
             └──► SIM card transitions toward "enabled"
```

## Telnyx Products Used

- **IoT SIM** — provision and activate cellular SIM cards over the API.

## API Endpoints

- **Enable (activate) SIM Card**: `POST /v2/sim_cards/{id}/actions/enable` — [API reference](https://developers.telnyx.com/api-reference/sim-cards/enable-sim-card)

## Prerequisites

- JDK 17+ and Maven 3.8+.
- A [Telnyx account](https://portal.telnyx.com/sign-up) and an [API key](https://portal.telnyx.com/app/api-keys).
- At least one SIM card in your account that can be enabled (IoT → SIM Cards).
- The SIM card ID (UUID), found in the [Telnyx Portal](https://portal.telnyx.com) under IoT → SIM Cards.

## Step 1: Set Up the Project

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/activate-sim-card-java
cp .env.example .env
```

Edit `.env` and set `TELNYX_API_KEY` to the key from the [Telnyx Portal](https://portal.telnyx.com/app/api-keys), then export it into your shell (the SDK reads it from the environment):

```bash
set -a && . ./.env && set +a
```

The dependency is pinned in `pom.xml` — note the artifactId is `telnyx` (not `telnyx-java`):

```xml
<dependency>
    <groupId>com.telnyx.sdk</groupId>
    <artifactId>telnyx</artifactId>
    <version>6.76.0</version>
</dependency>
```

## Step 2: Understand the Code

Everything lives in `Application.java`.

### Client Initialization

`main()` fails fast if `TELNYX_API_KEY` is missing, then creates one shared client via `fromEnv()` (which reads `TELNYX_API_KEY` and optional `TELNYX_PUBLIC_KEY` / `TELNYX_BASE_URL`):

```java
TelnyxClient client = TelnyxOkHttpClient.fromEnv();
```

The server is the JDK's `HttpServer`, with one handler bound to `/sim/activate`:

```java
HttpServer server = HttpServer.create(new InetSocketAddress(port), 0);
server.createContext("/sim/activate", app.new ActivateHandler());
server.start();
```

### Activating the SIM

The handler reads the raw request body, extracts `sim_card_id`, and calls the SDK. `enable(...)` has a convenience overload that takes the SIM card ID String directly:

```java
ActionEnableResponse response = client.simCards().actions().enable(simCardId);

String id = response.data()
        .flatMap(action -> action.id())
        .orElse(simCardId);
String status = response.data()
        .flatMap(action -> action.status())
        .map(Object::toString)
        .orElse("requested");
```

`response.data()` returns `Optional<SimCardAction>`; activation is an asynchronous action sub-resource (it is **not** a `SimCard` update), so the response describes the enable *action*.

### Error Handling

SDK errors surface as runtime exceptions. The handler logs the real cause server-side, derives the upstream HTTP status, and returns a generic message — exception details are never leaked to the client:

```java
} catch (RuntimeException e) {
    LOG.log(Level.WARNING, "Telnyx API error handling /sim/activate", e);
    int status = upstreamStatus(e);
    if (status == 401) {
        respond(exchange, 401, "{\"error\":\"Invalid API key\"}");
    } else if (status == 404) {
        respond(exchange, 404, "{\"error\":\"SIM card not found\"}");
    }
    // ... 422 / 429 / default 502 ...
}
```

### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/sim/activate` | Enable (activate) a SIM card by ID |

## Step 3: Run It

```bash
mvn -q exec:java
```

The server starts on `http://localhost:8080`. To build a self-contained jar instead:

```bash
mvn -q package
java -jar target/activate-sim-card-java.jar
```

## Step 4: Test It

Activate a SIM card (replace the ID with one from your account):

```bash
curl -X POST http://localhost:8080/sim/activate \
  -H "Content-Type: application/json" \
  -d '{
    "sim_card_id": "6b14e151-8493-4fa1-8664-1cc4e6d14158"
  }'
```

You should get back the enable action `id`, the submitted `sim_card_id`, and the action `status`.

## Going to Production

- **Authentication** — add API key or token validation on your endpoints before exposing them.
- **Structured logging** — replace `java.util.logging` with structured logs and request IDs.
- **Retries** — add bounded retries with backoff for `429` / `5xx` responses from Telnyx.
- **Monitoring** — alert on activation failures and track SIM status transitions via webhooks. When you receive webhooks, verify the Telnyx Ed25519 signature with `client.webhooks().unwrap(...)` and read event fields from `data.payload`.

## Resources

- [Source code and reference](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/activate-sim-card-java/README.md)
- [Typed API reference](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/activate-sim-card-java/API.md)
- [IoT SIM Get Started](https://developers.telnyx.com/docs/iot-sim/get-started)
- [Java SDK](https://developers.telnyx.com/development/sdk/java)
- [Telnyx Portal](https://portal.telnyx.com)
