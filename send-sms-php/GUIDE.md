# Guide: Send an SMS with PHP and Telnyx

This walkthrough builds a tiny vanilla-PHP HTTP endpoint that sends an SMS through the
Telnyx Messaging API using the official `telnyx/telnyx-php` SDK (7.x). No framework, no
Docker — just a single `index.php` front controller you can run with PHP's built-in server.

## Prerequisites

- PHP 8.1 or newer with the `sodium` extension (bundled in standard PHP 8 builds).
- [Composer](https://getcomposer.org/).
- A Telnyx account with:
  - An API key — [portal.telnyx.com/api-keys](https://portal.telnyx.com/api-keys).
  - A messaging-enabled phone number in E.164 format — [portal.telnyx.com/numbers/my-numbers](https://portal.telnyx.com/numbers/my-numbers).

## 1. Install dependencies

Create `composer.json`:

```json
{
    "require": {
        "php": ">=8.1",
        "ext-sodium": "*",
        "telnyx/telnyx-php": "^7.84",
        "guzzlehttp/guzzle": "^7.8",
        "vlucas/phpdotenv": "^5.6"
    }
}
```

Then install:

```bash
composer install
```

`guzzlehttp/guzzle` is a PSR-18 HTTP client; the SDK auto-discovers it via
`php-http/discovery`. `vlucas/phpdotenv` loads your local `.env` file.

## 2. Configure credentials

Copy the example env file and fill it in:

```bash
cp .env.example .env
```

```dotenv
TELNYX_API_KEY=your_telnyx_api_key_here
TELNYX_PHONE_NUMBER=+15551234567
```

Never commit `.env` — only `.env.example` with placeholder values.

## 3. Create the client

The 7.x SDK constructor takes **named parameters**. `apiKey` falls back to the
`TELNYX_API_KEY` environment variable when omitted:

```php
use Telnyx\Client;

$client = new Client(
    apiKey: getenv('TELNYX_API_KEY') ?: null,
);
```

## 4. Send the message

Use `messages->send()` with named params. (There is no `messages->create()` in 7.x.)

```php
$response = $client->messages->send(
    to: $toNumber,
    from: $fromNumber,
    text: $message,
);

$messageId = $response->data->id;
$status = $response->data->to[0]->status ?? 'unknown';
```

`$response` is a `Telnyx\Messages\MessageSendResponse`. The outbound payload lives under
`$response->data` (`Telnyx\Messages\OutboundMessagePayload`): `->id`, `->to` (array of
recipient objects with `phone_number`/`status`), `->from`, `->text`, `->parts`, `->cost`.

## 5. Wire up the front controller

`index.php` routes `POST /sms/send`, validates input, sends the message, and returns JSON.
Keep error bodies generic and log details server-side so nothing leaks to the client:

```php
use Telnyx\Core\Exceptions\AuthenticationException;
use Telnyx\Core\Exceptions\RateLimitException;
use Telnyx\Core\Exceptions\APIStatusException;
use Telnyx\Core\Exceptions\APIConnectionException;
use Telnyx\Core\Exceptions\APIException;

try {
    $response = $client->messages->send(to: $toNumber, from: $fromNumber, text: $message);
    // ... return JSON ...
} catch (AuthenticationException $e) {
    error_log('Telnyx authentication error: ' . $e->getMessage());
    send_json(401, ['error' => 'Invalid API key']);
} catch (RateLimitException $e) {
    send_json(429, ['error' => 'Rate limit exceeded. Please slow down.']);
} catch (APIConnectionException $e) {
    send_json(503, ['error' => 'Network error connecting to Telnyx']);
} catch (APIStatusException $e) {
    // $e->status is the HTTP status Telnyx returned (public int property).
    $status = ($e->status >= 400 && $e->status < 600) ? $e->status : 502;
    send_json($status, ['error' => 'Telnyx rejected the request']);
} catch (APIException $e) {
    send_json(502, ['error' => 'Failed to send message']);
}
```

The exception classes live under `Telnyx\Core\Exceptions\`. `APIException` is the base
class and exposes a public `?int $status` property — there is no `getHttpStatus()`.

## 6. Run it

```bash
php -S localhost:8080 index.php
```

Send a test message:

```bash
curl -X POST http://localhost:8080/sms/send \
  -H "Content-Type: application/json" \
  -d '{"to": "+12125551234", "message": "Hello from Telnyx!"}'
```

You should get back:

```json
{
  "message_id": "40385f64-5717-4562-b3fc-2c963f66afa6",
  "status": "queued",
  "from": "+15551234567",
  "to": "+12125551234"
}
```

## Optional: verifying inbound webhooks

If you extend this to receive delivery receipts or inbound SMS, verify the Telnyx Ed25519
signature with the SDK's built-in helper — do not roll your own. Set `TELNYX_PUBLIC_KEY`
(base64 Ed25519 public key from Mission Control), then:

```php
$payload = file_get_contents('php://input');
$headers = getallheaders(); // includes Telnyx-Signature-Ed25519 and Telnyx-Timestamp

try {
    // Verifies the signature AND parses the event in one call.
    $event = $client->webhooks->unwrap($payload, $headers);
} catch (\Telnyx\Core\Exceptions\WebhookException $e) {
    http_response_code(401);
    exit;
}

// Read inbound fields from data.payload (Telnyx v2 webhook shape):
$from = $event->data->payload->from;
$text = $event->data->payload->text;
```

`unwrap()` enforces a 300s timestamp tolerance (replay protection) and uses
`sodium_crypto_sign_verify_detached`, which is why `ext-sodium` is required.

## Next steps

- [send-bulk-sms-python](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/send-bulk-sms-python/README.md) — fan out to many recipients.
- [receive-sms-webhook-python](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/receive-sms-webhook-python/README.md) — handle inbound SMS.
- [Messaging Guide](https://developers.telnyx.com/docs/messaging) — concepts and deliverability.
