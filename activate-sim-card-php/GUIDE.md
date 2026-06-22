# Activate a Telnyx IoT SIM Card with PHP

Build a small vanilla-PHP API that retrieves and activates (enables) Telnyx IoT SIM cards using the Telnyx PHP SDK — no framework required.

## How It Works

```
  HTTP Request
        │
        ▼
  ┌──────────────────────┐
  │  Vanilla PHP router   │
  │  (index.php)          │
  └──────────┬───────────┘
             │  Telnyx PHP SDK
             ▼
  ┌──────────────────────┐
  │  Telnyx IoT SIM API   │
  └──────────────────────┘
```

## Telnyx Products Used

- **IoT SIM** — provision and manage cellular connectivity programmatically

## API Endpoints

- **Get SIM Card**: `GET /v2/sim_cards/{id}` — [API reference](https://developers.telnyx.com/api-reference/sim-cards/get-sim-card)
- **Enable (Activate) SIM Card**: `POST /v2/sim_cards/{id}/actions/enable` — [API reference](https://developers.telnyx.com/api-reference/sim-cards/enable-sim-card)

## Prerequisites

- PHP 8.1+ with `ext-sodium` (bundled in standard PHP 8 builds; used for webhook signature verification)
- [Composer](https://getcomposer.org/)
- [Telnyx account](https://portal.telnyx.com/sign-up) and [API key](https://portal.telnyx.com/api-keys)
- At least one SIM card in your account, already assigned to a SIM card group (visible under IoT → SIM Cards)

## Step 1: Set Up the Project

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/activate-sim-card-php
cp .env.example .env
composer install
```

Edit `.env` and set `TELNYX_API_KEY`. If you plan to receive webhooks, also set `TELNYX_PUBLIC_KEY` (the base64 Ed25519 public key from Mission Control).

## Step 2: Build the Telnyx Client

The SDK constructor takes named parameters. `apiKey` defaults to `TELNYX_API_KEY` and `publicKey` to `TELNYX_PUBLIC_KEY`; here we read them from the environment explicitly so the example fails fast when the key is missing.

```php
use Telnyx\Client;

function makeClient(): Client
{
    $apiKey = getenv('TELNYX_API_KEY') ?: ($_ENV['TELNYX_API_KEY'] ?? null);
    if (!$apiKey) {
        throw new RuntimeException('TELNYX_API_KEY is not set');
    }

    $publicKey = getenv('TELNYX_PUBLIC_KEY') ?: ($_ENV['TELNYX_PUBLIC_KEY'] ?? null);

    return new Client(
        apiKey: $apiKey,
        publicKey: $publicKey ?: null,
    );
}
```

## Step 3: Retrieve a SIM Card

`$client->simCards->retrieve($id)` returns a response whose `->data` is the SIM card. Read the SIM's own status here — the SIM is what carries `status`, not the action.

```php
function retrieveSim(Client $client, string $simCardId): array
{
    $response = $client->simCards->retrieve($simCardId);
    $sim = $response->data;

    return [
        'id'            => $sim->id,
        'iccid'         => $sim->iccid ?? null,
        'status'        => $sim->status ?? null,
        'simCardGroupId' => $sim->simCardGroupID ?? null,
    ];
}
```

## Step 4: Enable (Activate) the SIM Card

Activation is the SIM cards **enable** action, reached through the `actions` sub-service: `$client->simCards->actions->enable(id: $id)`. There is no `$client->simCards->activate()` method. The call returns a `SimCardAction` that tracks the async enable; the SIM does not flip to `enabled` synchronously.

```php
function activateSim(Client $client, string $simCardId): array
{
    $response = $client->simCards->actions->enable(id: $simCardId);
    $action = $response->data;

    return [
        'actionId'   => $action->id ?? null,
        'simCardId'  => $action->simCardID ?? $simCardId,
        'actionType' => $action->actionType ?? 'enable',
        'status'     => $action->status ?? null,
    ];
}
```

To follow the activation to completion, poll `$client->simCards->actions->retrieve(id: <action_id>)`, or read the SIM state again with `$client->simCards->retrieve($simCardId)->data->status`.

## Step 5: Verify Webhooks (Ed25519)

Never trust an inbound webhook without verifying its signature. The SDK ships a native helper — `$client->webhooks->unwrap($body, $headers)` verifies the `Telnyx-Signature-Ed25519` header (enforcing a 300s timestamp tolerance) and parses the event in one call. Read event fields from `data.payload`.

```php
$raw = file_get_contents('php://input') ?: '';
$headers = function_exists('getallheaders') ? (getallheaders() ?: []) : [];

try {
    $client = makeClient();
    $event = $client->webhooks->unwrap($raw, $headers);
} catch (\Telnyx\Core\Exceptions\WebhookException $e) {
    error_log('[telnyx] webhook verification failed: ' . $e->getMessage());
    http_response_code(401);
    exit;
}

$eventType = $event->data->eventType ?? 'unknown';
```

## Step 6: Route Requests

The front controller dispatches on the HTTP method and path. Errors are mapped to safe HTTP responses without leaking exception details.

```php
if ($method === 'POST' && preg_match('#^/sim/([^/]+)/activate$#', $path, $m)) {
    $simCardId = rawurldecode($m[1]);
    if ($simCardId === '') {
        sendJson(400, ['error' => 'SIM card ID must be a non-empty string']);
    }

    try {
        sendJson(202, [
            'message' => 'SIM card activation requested',
            'action'  => activateSim($client, $simCardId),
        ]);
    } catch (Throwable $e) {
        handleApiError($e);
    }
}
```

## Step 7: Run It

```bash
php -S localhost:8080 index.php
```

**Health check:**

```bash
curl http://localhost:8080/health
```

**Retrieve a SIM card:**

```bash
curl http://localhost:8080/sim/<sim_card_id>
```

**Activate a SIM card:**

```bash
curl -X POST http://localhost:8080/sim/<sim_card_id>/activate
```

A successful activation returns `202 Accepted`:

```json
{
  "message": "SIM card activation requested",
  "action": {
    "actionId": "a1b2c3d4-0000-1111-2222-333344445555",
    "simCardId": "<sim_card_id>",
    "actionType": "enable",
    "status": "in-progress"
  }
}
```

## Going to Production

- **Authentication** — add API key or token validation on your own endpoints.
- **Idempotency** — guard against repeat enable requests for the same SIM.
- **Polling/webhooks** — confirm activation by polling the action or handling the verified SIM status webhook.
- **Retries** — add exponential backoff for `429` and transient `503` responses.

## Resources

- [Source code and reference](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/activate-sim-card-php/README.md)
- [Typed API reference](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/activate-sim-card-php/API.md)
- [IoT SIM Get Started](https://developers.telnyx.com/docs/iot-sim/get-started)
- [PHP SDK](https://developers.telnyx.com/development/sdk/php)
- [Telnyx Portal](https://portal.telnyx.com)
