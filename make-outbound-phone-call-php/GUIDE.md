# Make Your First Outbound Call with Telnyx and PHP

Place an outbound phone call using the Telnyx Call Control API in vanilla PHP.
This guide walks through a single `index.php` front controller that exposes one
endpoint to dial a number through Telnyx and returns the call control ID, plus a
signature-verified webhook receiver for call lifecycle events.

## How It Works

```
  POST /calls/dial
        │
        ▼
  ┌──────────────────────┐
  │  index.php (router)   │
  │  initiateCall()       │
  └──────────┬───────────┘
             │  $client->calls->dial(connectionID, from, to)
             ▼
  ┌──────────────────────┐
  │  Telnyx Voice         │
  │  (Call Control)       │
  └──────────┬───────────┘
             │  outbound call placed → call_control_id returned
             ▼
  POST /webhooks/calls  ──►  $client->webhooks->unwrap()  (Ed25519 verify)
```

## Telnyx Products Used

- **Voice (Call Control)** — programmatically dial outbound calls and control them via a Call Control Application

## API Endpoints

- **Dial**: `POST /v2/calls` — [API reference](https://developers.telnyx.com/api-reference/call-commands/dial)

## Prerequisites

- PHP 8.1+ with the `sodium` extension (bundled in standard PHP 8 builds)
- [Composer](https://getcomposer.org/)
- A [Telnyx account](https://portal.telnyx.com/sign-up) with a funded balance
- An [API key](https://portal.telnyx.com/api-keys)
- A [Telnyx phone number](https://portal.telnyx.com/numbers/my-numbers) enabled for voice
- A [Call Control Application](https://portal.telnyx.com/call-control/applications) (its ID is your connection ID)

## Step 1: Set Up the Project

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/make-outbound-phone-call-php
cp .env.example .env
composer install
```

Edit `.env` with your Telnyx credentials:

| Variable | Description |
|----------|-------------|
| `TELNYX_API_KEY` | Your Telnyx API v2 key |
| `TELNYX_PHONE_NUMBER` | The Telnyx number you dial from (E.164) |
| `TELNYX_CONNECTION_ID` | Your Call Control Application ID |
| `TELNYX_PUBLIC_KEY` | Base64 Ed25519 public key for webhook verification |

## Step 2: Understand the Code

Everything lives in `index.php`. The Telnyx client is created from environment
credentials using named constructor parameters:

```php
$client = new Client(
    apiKey: getenv('TELNYX_API_KEY') ?: null,
    publicKey: getenv('TELNYX_PUBLIC_KEY') ?: null,
);
```

### `initiateCall($client, $toNumber)`

A helper that validates inputs and places the call. It reads `TELNYX_PHONE_NUMBER`
and `TELNYX_CONNECTION_ID` from the environment, enforces E.164 formatting on the
destination, then calls `$client->calls->dial()` with camelCase named parameters:

```php
$response = $client->calls->dial(
    connectionID: $connectionId,
    from: $fromNumber,
    to: $toNumber,
);
```

The `connectionID` is required — it links the call to your Call Control
Application. The `call_control_id` is returned in the response (you never pass it
in). Because SDK objects are not directly JSON-serializable, the helper returns a
plain array:

```php
return [
    'call_control_id' => $response->data->callControlID,
    'call_leg_id'     => $response->data->callLegID,
    'call_session_id' => $response->data->callSessionID,
    'is_alive'        => $response->data->isAlive,
    'from'            => $fromNumber,
    'to'              => $toNumber,
];
```

### `POST /calls/dial`

The route reads `to` from the JSON body, returns `400` if it is missing, otherwise
calls `initiateCall()`. Telnyx SDK exceptions are mapped to clean HTTP statuses so
internal details never leak (they are written to the log via `error_log()`):

| SDK exception | HTTP status | Body |
|---------------|-------------|------|
| `InvalidArgumentException` (validation) | `400` | the validation message |
| `AuthenticationException` | `401` | `Invalid API key` |
| `RateLimitException` | `429` | `Rate limit exceeded...` |
| `APIConnectionException` | `503` | `Network error connecting to Telnyx` |
| `APIStatusException` | upstream `status` | generic message + `status_code` |
| any other `Throwable` | `500` | `Internal server error` |

### `POST /webhooks/calls`

The webhook route passes the raw request body and headers to the SDK helper, which
verifies the Ed25519 signature against `TELNYX_PUBLIC_KEY` and parses the event in
one call. A bad signature throws `WebhookException` and the handler returns `401`:

```php
$payload = file_get_contents('php://input') ?: '';
$headers = getallheaders() ?: [];

try {
    $event = $client->webhooks->unwrap($payload, $headers);
} catch (WebhookException $e) {
    error_log('Webhook signature verification failed: ' . $e->getMessage());
    jsonResponse(401, ['error' => 'Invalid signature']);
}

// Telnyx v2 webhooks carry event data under data.payload.
$eventType = $event->data->eventType ?? 'unknown';
```

Always read event fields from `data.payload` and acknowledge with `200` quickly.

## Step 3: Run It

```bash
php -S localhost:8080 index.php
```

The server starts on `http://localhost:8080`.

## Step 4: Test It

Place a call:

```bash
curl -X POST http://localhost:8080/calls/dial \
  -H "Content-Type: application/json" \
  -d '{"to": "+12125551234"}'
```

Successful response:

```json
{
  "call_control_id": "v3:abc123def456...",
  "call_leg_id": "0ccc7b54-...",
  "call_session_id": "0ccc7b54-...",
  "is_alive": true,
  "from": "+15551234567",
  "to": "+12125551234"
}
```

## Going to Production

- **Webhook handling** — register the `/webhooks/calls` URL on your Call Control Application to receive `call.answered`, `call.hangup`, and other lifecycle events, and drive the rest of the flow off `data.payload`.
- **Webhook verification** — keep `TELNYX_PUBLIC_KEY` set so every event is Ed25519-verified before you act on it.
- **Authentication** — add API key or token validation on your `/calls/dial` endpoint.
- **Monitoring** — add structured logging and alerting around dial failures.
- **Rate limiting** — protect the endpoint from abuse.

## Resources

- [Source code and reference](./README.md)
- [Typed API reference](./API.md)
- [Voice / Call Control Guide](https://developers.telnyx.com/docs/voice/programmable-voice/voice-api-commands-and-resources)
- [Dial API Reference](https://developers.telnyx.com/api-reference/call-commands/dial)
- [PHP SDK](https://developers.telnyx.com/development/sdk/php)
- [Telnyx Portal](https://portal.telnyx.com)
