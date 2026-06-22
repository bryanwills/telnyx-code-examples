# Chat With a Telnyx AI Assistant in PHP

Build a production-ready, framework-free PHP front controller that sends a user message to a Telnyx AI Assistant and returns its reply, keeping conversation context across turns.

## How It Works

```
  POST /chat  { "message": "...", "conversation_id": "..." (optional) }
        │
        ▼
  ┌────────────────────────────────┐
  │ index.php (vanilla PHP router)  │
  └───────────────┬────────────────┘
                  │  $client->ai->conversations->create()  (first turn only)
                  │  $client->ai->assistants->chat(assistantID, content, conversationID)
                  ▼
  ┌────────────────────────────────┐
  │ Telnyx AI Assistant            │
  └───────────────┬────────────────┘
                  │
                  └──► { conversation_id, reply } (JSON)
```

## Telnyx Products Used

- **AI Assistants** — conversational AI that runs on the Telnyx network

## API Endpoints

- **Create a Conversation**: `POST /v2/ai/conversations`
- **Chat with an Assistant**: `POST /v2/ai/assistants/{assistant_id}/chat` — [API reference](https://developers.telnyx.com/api-reference/assistants/chat-with-an-assistant)

## Prerequisites

- PHP 8.1+ with the `sodium` extension (bundled in standard PHP 8 builds)
- [Composer](https://getcomposer.org/)
- [Telnyx account](https://portal.telnyx.com/sign-up) and [API key](https://portal.telnyx.com/api-keys)
- An existing [AI Assistant](https://portal.telnyx.com/ai/assistants) and its ID

## Step 1: Set Up the Project

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/chat-with-ai-assistant-php
cp .env.example .env
composer install
```

Edit `.env` with your Telnyx credentials:

```bash
TELNYX_API_KEY=your_telnyx_api_key_here
TELNYX_ASSISTANT_ID=your_assistant_id_here
TELNYX_PUBLIC_KEY=your_telnyx_public_key_here
PORT=8080
```

The dependencies are pinned in `composer.json`: `telnyx/telnyx-php ^7.84` (the Stainless-generated 7.x SDK), `guzzlehttp/guzzle ^7.8` (a PSR-18 client auto-discovered by the SDK), and `vlucas/phpdotenv ^5.6` for local `.env` loading. `ext-sodium` is declared because webhook signature verification needs it.

## Step 2: Understand the Code

Everything lives in `index.php`. It is a single front controller — no framework.

### Client Initialization

The SDK client is built from the environment. The constructor takes **named** parameters; `apiKey` falls back to `TELNYX_API_KEY` and `publicKey` to `TELNYX_PUBLIC_KEY`, but we pass them explicitly so a missing key is obvious:

```php
function make_client(): Client
{
    return new Client(
        apiKey: getenv('TELNYX_API_KEY') ?: null,
        publicKey: getenv('TELNYX_PUBLIC_KEY') ?: null,
    );
}
```

### Chatting and Keeping Context

The `/chat` handler reads `message` (and an optional `conversation_id`) from the JSON body. On the first turn it creates a conversation; on later turns the client passes the returned id back so the assistant keeps context. The reply is read from `$response->content`:

```php
if ($conversationId === '') {
    $conversation   = $client->ai->conversations->create();
    $conversationId = $conversation->data->id;
}

$response = $client->ai->assistants->chat(
    assistantID: $assistantId,
    content: $message,
    conversationID: $conversationId,
);

send_json(200, [
    'assistant_id'    => $assistantId,
    'conversation_id' => $conversationId,
    'user_message'    => $message,
    'reply'           => $response->content,
    'timestamp'       => gmdate('c'),
]);
```

The chat method takes named parameters `assistantID`, `content`, and `conversationID` — it is **not** a `messages: [{role, content}]` array, and the reply is `$response->content` (not a nested `data.result.output`).

### Production-Safe Error Handling

Telnyx SDK exceptions live under `Telnyx\Core\Exceptions\`. `classify_error()` logs the real error server-side and returns a generic, safe message plus an HTTP status — exception detail never reaches the client:

```php
function classify_error(\Throwable $e): array
{
    error_log('[chat-with-ai-assistant] ' . get_class($e) . ': ' . $e->getMessage());

    if ($e instanceof AuthenticationException) {
        return [401, 'Authentication failed. Check your TELNYX_API_KEY.'];
    }
    if ($e instanceof RateLimitException) {
        return [429, 'Rate limit exceeded. Please retry shortly.'];
    }
    if ($e instanceof APIConnectionException) {
        return [503, 'Could not reach Telnyx. Please try again.'];
    }
    if ($e instanceof APIException) {
        $status = $e->status ?? 502;
        return [$status, 'The Telnyx API returned an error.'];
    }

    return [500, 'An unexpected error occurred.'];
}
```

`APIException` exposes the HTTP status as a public `$status` property — there is no `getHttpStatus()`.

### Verifying Webhooks

Inbound webhooks must be signature-verified before any field is trusted. The SDK ships a native helper, so we do not roll our own crypto. `unwrap()` verifies the Ed25519 signature against `TELNYX_PUBLIC_KEY` and parses the event in one call:

```php
$raw     = file_get_contents('php://input') ?: '';
$headers = function_exists('getallheaders') ? getallheaders() : [];

try {
    $client = make_client();
    $event = $client->webhooks->unwrap($raw, $headers);
} catch (WebhookException $e) {
    error_log('[chat-with-ai-assistant] webhook verification failed: ' . $e->getMessage());
    send_json(401, ['error' => 'Invalid webhook signature.']);
}

// Telnyx v2 webhooks carry fields under data.payload — read from there.
$eventType = $event->data->eventType ?? 'unknown';
```

Telnyx v2 webhook fields live under `data.payload` (e.g. `$event->data->payload->...`), not `data.attributes`.

## Step 3: Run It

```bash
php -S localhost:8080 index.php
```

## Step 4: Test It

**Health check:**

```bash
curl http://localhost:8080/health
```

**Start a conversation:**

```bash
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What are your business hours?"}'
```

Expected response:

```json
{
  "assistant_id": "assistant-1234abcd",
  "conversation_id": "conv-abcd1234",
  "user_message": "What are your business hours?",
  "reply": "We are open Monday to Friday, 9am to 5pm.",
  "timestamp": "2026-06-19T14:32:00+00:00"
}
```

**Continue the conversation** — pass the returned `conversation_id` back:

```bash
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "And on weekends?", "conversation_id": "conv-abcd1234"}'
```

## Going to Production

- **Persist conversation ids** — store the `conversation_id` per user/session so context survives across requests.
- **Authentication** — add API key or token validation on `/chat`.
- **Rate limiting** — protect the endpoint and add exponential backoff for upstream 429s.
- **Monitoring** — add structured logging and alert on the `/health` endpoint.

## Resources

- [Source code and reference](./README.md)
- [Typed API reference](./API.md)
- [AI Assistants Guide](https://developers.telnyx.com/docs/inference/ai-assistants/no-code-voice-assistant)
- [PHP SDK](https://developers.telnyx.com/development/sdk/php)
- [Telnyx Portal](https://portal.telnyx.com)
