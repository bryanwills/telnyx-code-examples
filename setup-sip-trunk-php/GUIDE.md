# Set Up a SIP Trunk with PHP

Build a small vanilla-PHP API that creates, lists, and retrieves Telnyx credential (SIP) connections using the Telnyx PHP SDK — no framework required.

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
  ┌──────────────────────────────┐
  │  Telnyx Credential Conn. API  │
  └──────────────────────────────┘
```

A **credential connection** is a SIP trunk that authenticates with a username and password (as opposed to FQDN- or IP-based authentication). It is the simplest trunk to stand up: create it, then register your PBX/SBC against `sip.telnyx.com` with the credentials you chose.

## Telnyx Products Used

- **SIP Trunking** — connect your PBX/SBC to the PSTN over the Telnyx network

## API Endpoints

- **Create Credential Connection**: `POST /v2/credential_connections` — [API reference](https://developers.telnyx.com/api-reference/credential-connections/create-credential-connection)
- **List Credential Connections**: `GET /v2/credential_connections` — [API reference](https://developers.telnyx.com/api-reference/credential-connections/list-credential-connections)
- **Get Credential Connection**: `GET /v2/credential_connections/{id}` — [API reference](https://developers.telnyx.com/api-reference/credential-connections/get-credential-connection)

## Prerequisites

- PHP 8.1+ with `ext-sodium` (bundled in standard PHP 8 builds; used for webhook signature verification)
- [Composer](https://getcomposer.org/)
- [Telnyx account](https://portal.telnyx.com/sign-up) and [API key](https://portal.telnyx.com/api-keys)

## Step 1: Set Up the Project

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/setup-sip-trunk-php
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

## Step 3: Create a Credential Connection

`$client->credentialConnections->create(...)` takes named parameters. `connectionName`, `userName`, and `password` are required by the API. We validate the inputs first and never echo the plaintext password back to the caller.

```php
function createConnection(Client $client, array $body): array
{
    $connectionName = trim((string) ($body['connectionName'] ?? ''));
    $userName       = trim((string) ($body['userName'] ?? ''));
    $password       = (string) ($body['password'] ?? '');

    if ($connectionName === '' || $userName === '' || $password === '') {
        sendJson(400, [
            'error' => 'connectionName, userName, and password are required',
        ]);
    }

    $created = $client->credentialConnections->create(
        connectionName: $connectionName,
        userName: $userName,
        password: $password,
    );

    return serializeConnection($created->data);
}
```

The create response is a `CredentialConnectionNewResponse`; read the connection from `->data`. A small helper turns the typed model into a JSON-safe array:

```php
function serializeConnection(object $conn): array
{
    return [
        'id'             => $conn->id ?? null,
        'connectionName' => $conn->connectionName ?? null,
        'userName'       => $conn->userName ?? null,
        'active'         => $conn->active ?? null,
        'createdAt'      => $conn->createdAt ?? null,
    ];
}
```

## Step 4: List Credential Connections

`$client->credentialConnections->list()` returns a paginated result. Iterate the current page with `$page->getItems()`.

```php
function listConnections(Client $client): array
{
    $page = $client->credentialConnections->list();

    $items = [];
    foreach ($page->getItems() as $conn) {
        $items[] = serializeConnection($conn);
    }

    return ['data' => $items];
}
```

To walk every page automatically, use `$page->pagingEachItem()` instead.

## Step 5: Retrieve a Credential Connection

`$client->credentialConnections->retrieve($id)` takes the ID positionally and returns a `CredentialConnectionGetResponse`; read the connection from `->data`.

```php
function retrieveConnection(Client $client, string $connectionId): array
{
    $response = $client->credentialConnections->retrieve($connectionId);

    return serializeConnection($response->data);
}
```

## Step 6: Verify Webhooks (Ed25519)

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

## Step 7: Route Requests

The front controller dispatches on the HTTP method and path. Errors are mapped to safe HTTP responses without leaking exception details.

```php
if ($method === 'POST' && $path === '/connections') {
    try {
        sendJson(201, createConnection($client, readJsonBody()));
    } catch (Throwable $e) {
        handleApiError($e);
    }
}
```

## Step 8: Run It

```bash
php -S localhost:8080 index.php
```

**Health check:**

```bash
curl http://localhost:8080/health
```

**Create a connection:**

```bash
curl -X POST http://localhost:8080/connections \
  -H 'Content-Type: application/json' \
  -d '{"connectionName": "My SIP Trunk", "userName": "myuser1234", "password": "SuperSecret123"}'
```

A successful create returns `201 Created`:

```json
{
  "id": "1234567890",
  "connectionName": "My SIP Trunk",
  "userName": "myuser1234",
  "active": true,
  "createdAt": "2026-06-19T12:00:00.000Z"
}
```

**List connections:**

```bash
curl http://localhost:8080/connections
```

**Retrieve one connection:**

```bash
curl http://localhost:8080/connections/<connection_id>
```

## Going to Production

- **Authentication** — add API key or token validation on your own endpoints.
- **Credential hygiene** — generate strong SIP passwords; never log or echo them.
- **Trunk type** — for FQDN- or IP-authenticated trunks use `$client->fqdnConnections` or `$client->ipConnections` instead of `credentialConnections`.
- **Retries** — add exponential backoff for `429` and transient `503` responses.

## Resources

- [Source code and reference](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/setup-sip-trunk-php/README.md)
- [Typed API reference](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/setup-sip-trunk-php/API.md)
- [SIP Trunking Get Started](https://developers.telnyx.com/docs/voice/sip-trunking/get-started)
- [PHP SDK](https://developers.telnyx.com/development/sdk/php)
- [Telnyx Portal](https://portal.telnyx.com)
