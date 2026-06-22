# Guide: Set Up a SIP Trunk in Java

This walkthrough builds a small REST API that creates, lists, and retrieves
Telnyx credential (SIP) connections. It uses the Telnyx Java SDK
(`com.telnyx.sdk:telnyx`) for the API calls and the JDK's built-in
`com.sun.net.httpserver.HttpServer` for the HTTP layer — no web framework.

A credential connection is a SIP trunk authenticated with a username and
password. It is the simplest way to connect a PBX or SBC to Telnyx.

## Prerequisites

- JDK 17 or newer (the SDK's webhook signature verification needs JDK-native Ed25519, available on JDK 15+).
- Maven 3.8+.
- A Telnyx account and an API v2 key from the [Telnyx Portal](https://portal.telnyx.com/app/api-keys).

## 1. Add the SDK dependency

The Stainless-generated Telnyx Java SDK is published as
`com.telnyx.sdk:telnyx` (the artifactId is `telnyx`, **not** `telnyx-java` —
that coordinate is the old, deprecated SDK with a completely different API).

```xml
<dependency>
    <groupId>com.telnyx.sdk</groupId>
    <artifactId>telnyx</artifactId>
    <version>6.76.0</version>
</dependency>
```

See [`pom.xml`](./pom.xml) for the full build configuration, including the
`exec-maven-plugin` used to run the app.

## 2. Configure credentials

Copy `.env.example` to `.env` and set your API key:

```bash
cp .env.example .env
# edit .env, then load it into the shell:
set -a && . ./.env && set +a
```

The SDK reads `TELNYX_API_KEY` (and the optional `TELNYX_PUBLIC_KEY` /
`TELNYX_BASE_URL`) straight from the environment. Never hardcode keys.

## 3. Create one shared client

Create a single `TelnyxClient` at startup and share it across requests — it is
thread-safe.

```java
import com.telnyx.sdk.client.TelnyxClient;
import com.telnyx.sdk.client.okhttp.TelnyxOkHttpClient;

// Reads TELNYX_API_KEY from the environment.
TelnyxClient client = TelnyxOkHttpClient.fromEnv();
```

## 4. Create a credential connection

Use the builder, then call `client.credentialConnections().create(...)`. Note
that `client.connections()` (the generic connection service) only exposes
`retrieve`/`list` — to *create* a SIP trunk you must use
`credentialConnections()` (or `fqdnConnections()` / `ipConnections()`).

```java
import com.telnyx.sdk.models.credentialconnections.CredentialConnectionCreateParams;
import com.telnyx.sdk.models.credentialconnections.CredentialConnectionCreateResponse;

CredentialConnectionCreateParams params = CredentialConnectionCreateParams.builder()
        .connectionName(connectionName) // required
        .userName(userName)             // required
        .password(password)             // required
        .build();

CredentialConnectionCreateResponse response = client.credentialConnections().create(params);
String id = response.data().flatMap(c -> c.id()).orElse(null);
```

`response.data()` returns `Optional<CredentialConnection>`. The model's
accessors (`id()`, `connectionName()`, `userName()`) each return `Optional`, so
chain with `flatMap` / `ifPresent`. Never echo the SIP `password` back to the
caller.

## 5. List credential connections

`list()` returns a page object whose `autoPager()` transparently fetches
subsequent pages as you iterate.

```java
import com.telnyx.sdk.models.credentialconnections.CredentialConnection;
import com.telnyx.sdk.models.credentialconnections.CredentialConnectionListPage;

CredentialConnectionListPage page = client.credentialConnections().list();
for (CredentialConnection c : page.autoPager()) {
    String name = c.connectionName().orElse("(unnamed)");
    // ...
}
```

## 6. Retrieve a single connection

```java
import com.telnyx.sdk.models.credentialconnections.CredentialConnectionRetrieveResponse;

CredentialConnectionRetrieveResponse response = client.credentialConnections().retrieve(id);
response.data().flatMap(c -> c.connectionName()).ifPresent(System.out::println);
```

## 7. Serve it over HTTP

The example wires these calls to routes on `com.sun.net.httpserver.HttpServer`.
The collection handler dispatches by method and path:

```java
HttpServer server = HttpServer.create(new InetSocketAddress(port), 0);
server.createContext("/sip-connections", app::handleSipConnections);
server.createContext("/health", Application::handleHealth);
server.start();
```

Errors are mapped carefully so internal detail never leaks to the client:

```java
} catch (IllegalArgumentException e) {
    sendJson(exchange, 400, Map.of("error", e.getMessage())); // safe: validation message
} catch (TelnyxException e) {
    LOGGER.log(Level.WARNING, "Telnyx API error", e);         // log detail server-side
    sendJson(exchange, 502, Map.of("error", "Upstream Telnyx API error"));
} catch (RuntimeException e) {
    LOGGER.log(Level.SEVERE, "Unexpected error", e);
    sendJson(exchange, 500, Map.of("error", "Internal server error"));
}
```

See [`Application.java`](./Application.java) for the full implementation,
including the dependency-free JSON request/response helpers.

## 8. Run it

```bash
mvn -q compile
mvn -q exec:java
```

Then exercise the API:

```bash
curl -X POST http://localhost:8080/sip-connections \
  -H "Content-Type: application/json" \
  -d '{"connection_name":"My PBX Trunk","user_name":"sipuser12345","password":"SuperSecretPass123"}'

curl http://localhost:8080/sip-connections
curl http://localhost:8080/sip-connections/<id>
```

## A note on webhooks

This example does not receive webhooks, but if you extend it to handle inbound
Telnyx events, you **must** verify the Ed25519 signature before trusting the
payload. The SDK provides `client.webhooks().unwrap(UnwrapWebhookParams)`, which
verifies the `telnyx-signature-ed25519` / `telnyx-timestamp` headers against the
exact raw request bytes (the signed string is `"{timestamp}|{rawBody}"`), then
returns a typed event. Read business fields from `data.payload` on the returned
event. This requires `TELNYX_PUBLIC_KEY` to be configured.

```java
import com.telnyx.sdk.core.UnwrapWebhookParams;
import com.telnyx.sdk.core.http.Headers;
import com.telnyx.sdk.models.webhooks.UnwrapWebhookEvent;

Headers headers = Headers.builder()
        .put("telnyx-signature-ed25519", signatureHeader)
        .put("telnyx-timestamp", timestampHeader)
        .build();
UnwrapWebhookParams params = UnwrapWebhookParams.builder()
        .body(rawBody)      // exact bytes of the POST body — do NOT re-serialize
        .headers(headers)
        .build();
UnwrapWebhookEvent event = client.webhooks().unwrap(params); // throws on bad/stale signature
// e.g. event.inboundMessage().flatMap(m -> m.data()).flatMap(d -> d.payload())...
```

## Next steps

- Add an outbound voice profile and SIP endpoints to route real calls.
- See [setup-sip-trunk-go](../setup-sip-trunk-go/), [setup-sip-trunk-nodejs](../setup-sip-trunk-nodejs/), and [setup-sip-trunk-python](../setup-sip-trunk-python/) for the same flow in other languages.
