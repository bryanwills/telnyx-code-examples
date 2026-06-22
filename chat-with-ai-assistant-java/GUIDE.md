# Chat With a Telnyx AI Assistant in Java

Build a small HTTP service that chats with a Telnyx AI Assistant using the Telnyx Java SDK
and the JDK's built-in `HttpServer` — no web framework required. Each request can carry a
`conversation_id` so you can thread a multi-turn conversation.

## How It Works

```
  HTTP Request (POST /chat)
        │
        ▼
  ┌──────────────────────┐
  │  JDK HttpServer       │
  │  (Application.java)    │
  └──────────┬───────────┘
             │  Telnyx Java SDK
             ▼
  ┌──────────────────────┐
  │  Telnyx AI Assistant  │
  │  Chat API             │
  └──────────┬───────────┘
             │
             └──► assistant reply + conversation_id
```

## Telnyx Products Used

- **AI Assistants** — conversational agents you reach over the Telnyx API

## API Endpoints

- **Chat with an AI Assistant**: `POST /v2/ai/assistants/{assistant_id}/chat` — [API reference](https://developers.telnyx.com/api-reference/assistants/chat)

## Prerequisites

- JDK 17+ and Maven 3.6+
- [Telnyx account](https://portal.telnyx.com/sign-up)
- [API key](https://portal.telnyx.com/api-keys)
- An AI Assistant created under AI → Assistants in the [Telnyx Portal](https://portal.telnyx.com); note its id

## Step 1: Set Up the Project

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/chat-with-ai-assistant-java
cp .env.example .env
```

Edit `.env` and set `TELNYX_API_KEY` and `TELNYX_ASSISTANT_ID`. The Telnyx Java SDK reads
`TELNYX_API_KEY` from the process environment, so export the values before running:

```bash
set -a && . ./.env && set +a
```

The dependency is pinned in `pom.xml`:

```xml
<dependency>
  <groupId>com.telnyx.sdk</groupId>
  <artifactId>telnyx</artifactId>
  <version>6.76.0</version>
</dependency>
```

Note: the artifactId is `telnyx`, not `telnyx-java`.

## Step 2: Understand the Code

Everything lives in `Application.java`. Here's what each piece does.

### Client initialization

The SDK builds one client from the environment and shares it across requests:

```java
private static final TelnyxClient CLIENT = TelnyxOkHttpClient.fromEnv();
```

`fromEnv()` reads `TELNYX_API_KEY` (and optional `TELNYX_BASE_URL`) from the process
environment. Never hardcode the key.

### Chatting with the assistant

The `chat(...)` helper builds an `AssistantChatParams` and calls the SDK. The
`conversationId` threads multi-turn conversations — pass the same value back on each turn:

```java
private static String chat(String userMessage, String conversationId) {
    AssistantChatParams params = AssistantChatParams.builder()
            .content(userMessage)
            .conversationId(conversationId)
            .build();

    AssistantChatResponse response = CLIENT.ai().assistants().chat(ASSISTANT_ID, params);
    return response.content();
}
```

`AssistantChatResponse.content()` returns the assistant's reply as a `String`.

### Routes

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/chat` | Send a message to the assistant |
| `GET` | `/health` | Liveness probe |

The `/chat` handler reads the body, extracts `message` and optional `conversation_id`,
generates a conversation id when none is supplied, calls the assistant, and returns JSON:

```java
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
```

### Error handling

Telnyx SDK errors are unchecked, so they are caught as `RuntimeException`, logged
server-side, and returned as a generic `502` — no exception details leak into the HTTP
response:

```java
} catch (RuntimeException e) {
    LOGGER.log(Level.WARNING, "Telnyx API error", e);
    respond(exchange, 502, "{\"error\":\"Upstream AI request failed\"}");
} catch (Exception e) {
    LOGGER.log(Level.SEVERE, "Unexpected error handling /chat", e);
    respond(exchange, 500, "{\"error\":\"Internal server error\"}");
}
```

## Step 3: Run It

```bash
mvn compile exec:java
```

The server logs the routes it serves and listens on `PORT` (or `8080` if unset).

## Step 4: Test It

**Health check:**

```bash
curl http://localhost:8080/health
```

**Start a conversation:**

```bash
curl -X POST http://localhost:8080/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "What are your support hours?"}'
```

A successful response returns the reply and a `conversation_id`:

```json
{
  "assistant_id": "assistant-abc123",
  "conversation_id": "0b6f2d4e-9a1c-4f3b-8e2a-1c2d3e4f5a6b",
  "reply": "Our support team is available 24/7."
}
```

**Continue the conversation** by passing that `conversation_id` back:

```bash
curl -X POST http://localhost:8080/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "And on weekends?", "conversation_id": "0b6f2d4e-9a1c-4f3b-8e2a-1c2d3e4f5a6b"}'
```

## Going to Production

- **Authentication** — add API key or token validation on your endpoints.
- **Conversation storage** — persist `conversation_id` per user/session so follow-up turns thread correctly.
- **Retries** — add exponential backoff for transient upstream errors.
- **Monitoring** — add structured logging and alerts on the `/health` endpoint.

## Resources

- [Source code and reference](./README.md)
- [Typed API reference](./API.md)
- [AI Assistants Guide](https://developers.telnyx.com/docs/inference/ai-assistants/no-code-voice-assistant)
- [Java SDK](https://developers.telnyx.com/development/sdk/java)
- [Telnyx Portal](https://portal.telnyx.com)
