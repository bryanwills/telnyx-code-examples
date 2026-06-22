# Receive Inbound SMS Webhooks with PHP

Build a small vanilla-PHP endpoint that receives inbound SMS from Telnyx, verifies the Ed25519 webhook signature with the Telnyx PHP SDK, and reads the message from `data.payload` — no framework required.

## How It Works

```
   Inbound SMS to your Telnyx number
                 │
                 ▼
   ┌──────────────────────────────┐
   │  Telnyx Messaging platform    │  signs the event (Ed25519)
   └──────────────┬───────────────┘
                  │  POST message.received
                  ▼
   ┌──────────────────────────────┐
   │  Vanilla PHP router           │
   │  (index.php)                  │
   │   POST /webhooks/sms          │
   └──────────────────────────────┘
```

## Telnyx Products Used

- **SMS / Messaging** — inbound message delivery via signed webhooks

## API Endpoints

- **Inbound SMS webhook**: Telnyx POSTs a `message.received` event to your webhook URL — [Receive an SMS](https://developers.telnyx.com/docs/messaging/messages/receive-message)

## Prerequisites

- PHP 8.1+ with `ext-sodium` (bundled in standard PHP 8 builds; used for signature verification)
- [Composer](https://getcomposer.org/)
- [Telnyx account](https://portal.telnyx.com/sign-up) and [API key](https://portal.telnyx.com/api-keys)
- A Telnyx phone number enabled for inbound SMS, attached to a Messaging Profile
- A public HTTPS URL to receive webhooks (for local dev, a tunnel such as `ngrok http 8080`)

## Step 1: Set Up the Project

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/receive-sms-webhook-php
cp .env.example .env
composer install
```

Edit `.env` and set both `TELNYX_API_KEY` and `TELNYX_PUBLIC_KEY` (the base64 Ed25519 public key from the Telnyx Portal under Account → Public Key). The public key is what verifies inbound webhook signatures.

## Step 2: Build the Telnyx Client

The SDK constructor takes named parameters. We read both keys from the environment and fail fast when either is missing — the public key is required to verify webhooks.

```php
use Telnyx\Client;

function makeClient(): Client
{
    $apiKey = getenv('TELNYX_API_KEY') ?: ($_ENV['TELNYX_API_KEY'] ?? null);
    if (!$apiKey) {
        throw new RuntimeException('TELNYX_API_KEY is not set');
    }

    $publicKey = getenv('TELNYX_PUBLIC_KEY') ?: ($_ENV['TELNYX_PUBLIC_KEY'] ?? null);
    if (!$publicKey) {
        throw new RuntimeException('TELNYX_PUBLIC_KEY is not set');
    }

    return new Client(
        apiKey: $apiKey,
        publicKey: $publicKey,
    );
}
```

## Step 3: Verify the Signature (Always First)

Never trust an inbound webhook without verifying its signature. The SDK ships a native helper: `$client->webhooks->unwrap($body, $headers)` verifies the `Telnyx-Signature-Ed25519` header over `"<telnyx-timestamp>|<raw body>"` (enforcing a 300s timestamp tolerance) and parses the event in one call. On a missing/invalid signature it throws `WebhookException`.

Read the **raw** body — not a re-encoded array — because the signature covers the exact bytes Telnyx sent.

```php
use Telnyx\Core\Exceptions\WebhookException;

$raw = file_get_contents('php://input') ?: '';
$headers = function_exists('getallheaders') ? (getallheaders() ?: []) : [];

try {
    $client = makeClient();
} catch (Throwable $e) {
    error_log('[telnyx] client init failed: ' . $e->getMessage());
    sendJson(500, ['error' => 'Server misconfigured']);
}

try {
    $event = $client->webhooks->unwrap($raw, $headers);
} catch (WebhookException $e) {
    error_log('[telnyx] webhook verification failed: ' . $e->getMessage());
    sendJson(401, ['error' => 'Invalid webhook signature']);
} catch (Throwable $e) {
    error_log('[telnyx] webhook error: ' . get_class($e) . ': ' . $e->getMessage());
    sendJson(400, ['error' => 'Bad webhook request']);
}
```

## Step 4: Read the Message from `data.payload`

Telnyx v2 webhooks carry the event under `data.payload`. For inbound SMS the event type is `message.received`. Branch on it, then pull the fields off the typed payload.

```php
function extractInboundSms(object $event): array
{
    $payload = $event->data->payload ?? null;

    $toList = $payload->to ?? [];
    $firstTo = is_array($toList) && isset($toList[0]) ? $toList[0] : null;

    return [
        'messageId'  => $payload->id ?? null,
        'from'       => $payload->from->phoneNumber ?? null,
        'to'         => $firstTo->phoneNumber ?? null,
        'text'       => $payload->text ?? '',
        'receivedAt' => $payload->receivedAt ?? null,
    ];
}
```

## Step 5: Acknowledge Quickly

Process only `message.received`; acknowledge everything else. Return `200` fast and push heavy work (persistence, replies, fan-out) out of band so Telnyx does not retry.

```php
$eventType = $event->data->eventType ?? 'unknown';
if ($eventType !== 'message.received') {
    sendJson(200, ['status' => 'ignored', 'eventType' => $eventType]);
}

$message = extractInboundSms($event);

sendJson(200, [
    'status'    => 'received',
    'messageId' => $message['messageId'],
]);
```

## Step 6: Run It

```bash
php -S localhost:8080 index.php
```

**Health check:**

```bash
curl http://localhost:8080/health
```

Then expose the server publicly and register the webhook:

```bash
ngrok http 8080
```

Set `https://<your-ngrok-subdomain>/webhooks/sms` as the webhook URL on your [Messaging Profile](https://portal.telnyx.com/#/messaging), then text your Telnyx number. A verified inbound message returns `200`:

```json
{
  "status": "received",
  "messageId": "40000000-0000-0000-0000-000000000000"
}
```

## Going to Production

- **Always verify** — keep the signature check first; never read fields from an unverified event.
- **Idempotency** — Telnyx may redeliver; de-duplicate on `data.payload.id` before persisting.
- **Fast ack** — offload work to a queue so the handler returns within Telnyx's retry window.
- **Key rotation** — read `TELNYX_PUBLIC_KEY` from the environment so you can rotate without code changes.

## Resources

- [Source code and reference](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/receive-sms-webhook-php/README.md)
- [Typed API reference](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/receive-sms-webhook-php/API.md)
- [Receive an SMS (Messaging docs)](https://developers.telnyx.com/docs/messaging/messages/receive-message)
- [PHP SDK](https://developers.telnyx.com/development/sdk/php)
- [Telnyx Portal](https://portal.telnyx.com)
