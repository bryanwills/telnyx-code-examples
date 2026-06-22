<?php

/**
 * Set up a Telnyx SIP trunk by managing credential (SIP) connections —
 * vanilla PHP front controller, no framework.
 *
 * Routes:
 *   POST /connections         Create a credential (SIP) connection.
 *   GET  /connections         List credential (SIP) connections.
 *   GET  /connections/{id}    Retrieve a single credential (SIP) connection.
 *   POST /webhooks/telnyx     Receive + Ed25519-verify Telnyx webhooks.
 *   GET  /health              Liveness probe.
 *
 * Run locally with PHP's built-in server:
 *   php -S localhost:8080 index.php
 */

declare(strict_types=1);

require __DIR__ . '/vendor/autoload.php';

use Telnyx\Client;
use Telnyx\Core\Exceptions\APIException;
use Telnyx\Core\Exceptions\APIConnectionException;
use Telnyx\Core\Exceptions\AuthenticationException;
use Telnyx\Core\Exceptions\BadRequestException;
use Telnyx\Core\Exceptions\NotFoundException;
use Telnyx\Core\Exceptions\RateLimitException;
use Telnyx\Core\Exceptions\WebhookException;

// Load .env when present (no-op in production where vars come from the environment).
if (class_exists(\Dotenv\Dotenv::class)) {
    \Dotenv\Dotenv::createImmutable(__DIR__)->safeLoad();
}

/**
 * Build the Telnyx client. apiKey defaults to TELNYX_API_KEY and publicKey to
 * TELNYX_PUBLIC_KEY; both are read from the environment, never hardcoded.
 */
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

/** Read and decode the JSON request body. Returns [] when the body is empty. */
function readJsonBody(): array
{
    $raw = file_get_contents('php://input') ?: '';
    if ($raw === '') {
        return [];
    }
    $decoded = json_decode($raw, true);
    return is_array($decoded) ? $decoded : [];
}

/** Emit a JSON response with the given HTTP status code and exit. */
function sendJson(int $status, array $body): void
{
    http_response_code($status);
    header('Content-Type: application/json');
    echo json_encode($body, JSON_UNESCAPED_SLASHES);
    exit;
}

/**
 * Map a Telnyx SDK exception to a safe HTTP response. Exception details are
 * logged server-side; clients only ever see a generic, status-appropriate message.
 */
function handleApiError(Throwable $e): void
{
    error_log('[telnyx] ' . get_class($e) . ': ' . $e->getMessage());

    if ($e instanceof AuthenticationException) {
        sendJson(401, ['error' => 'Invalid API key']);
    }
    if ($e instanceof NotFoundException) {
        sendJson(404, ['error' => 'Credential connection not found']);
    }
    if ($e instanceof BadRequestException) {
        sendJson(400, ['error' => 'Invalid request to Telnyx API']);
    }
    if ($e instanceof RateLimitException) {
        sendJson(429, ['error' => 'Rate limit exceeded. Please slow down.']);
    }
    if ($e instanceof APIConnectionException) {
        sendJson(503, ['error' => 'Network error connecting to Telnyx']);
    }
    if ($e instanceof APIException) {
        // Other 4xx/5xx from the API. $status is a public int property on APIException.
        $status = $e->status ?? 502;
        sendJson($status >= 400 ? $status : 502, ['error' => 'Telnyx API error']);
    }

    // Unknown/unexpected error — never leak details.
    sendJson(500, ['error' => 'Internal server error']);
}

/**
 * Serialize a credential-connection model (from create/retrieve responses or
 * a list item) into a plain, JSON-safe array.
 */
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

/**
 * Create a credential (SIP) connection.
 * POST /v2/credential_connections via $client->credentialConnections->create(...).
 *
 * connectionName, userName, and password are required by the API. The password
 * is supplied by the caller and never logged or echoed back in the response.
 */
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

/**
 * List credential (SIP) connections.
 * GET /v2/credential_connections via $client->credentialConnections->list().
 */
function listConnections(Client $client): array
{
    $page = $client->credentialConnections->list();

    $items = [];
    foreach ($page->getItems() as $conn) {
        $items[] = serializeConnection($conn);
    }

    return ['data' => $items];
}

/**
 * Retrieve a single credential (SIP) connection by ID.
 * GET /v2/credential_connections/{id} via $client->credentialConnections->retrieve($id).
 */
function retrieveConnection(Client $client, string $connectionId): array
{
    $response = $client->credentialConnections->retrieve($connectionId);

    return serializeConnection($response->data);
}

// ---------------------------------------------------------------------------
// Routing
// ---------------------------------------------------------------------------

$method = $_SERVER['REQUEST_METHOD'] ?? 'GET';
$path = rtrim(parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH) ?: '/', '/');
if ($path === '') {
    $path = '/';
}

// GET /health — liveness probe (no client needed).
if ($method === 'GET' && $path === '/health') {
    sendJson(200, ['status' => 'ok']);
}

// POST /webhooks/telnyx — verify Ed25519 signature, then read data.payload.
if ($method === 'POST' && $path === '/webhooks/telnyx') {
    $raw = file_get_contents('php://input') ?: '';
    $headers = function_exists('getallheaders') ? (getallheaders() ?: []) : [];

    try {
        $client = makeClient();
        // unwrap() verifies the Telnyx Ed25519 signature AND parses the event.
        $event = $client->webhooks->unwrap($raw, $headers);
    } catch (WebhookException $e) {
        error_log('[telnyx] webhook verification failed: ' . $e->getMessage());
        sendJson(401, ['error' => 'Invalid webhook signature']);
    } catch (Throwable $e) {
        error_log('[telnyx] webhook error: ' . get_class($e) . ': ' . $e->getMessage());
        sendJson(400, ['error' => 'Bad webhook request']);
    }

    // Telnyx v2 webhooks carry fields under data.payload.
    $eventType = $event->data->eventType ?? 'unknown';
    error_log('[telnyx] received webhook: ' . $eventType);

    // Acknowledge quickly; do heavy work out of band.
    sendJson(200, ['received' => true]);
}

// All connection routes need a client.
try {
    $client = makeClient();
} catch (Throwable $e) {
    error_log('[telnyx] client init failed: ' . $e->getMessage());
    sendJson(500, ['error' => 'Server misconfigured']);
}

// POST /connections — create a credential (SIP) connection.
if ($method === 'POST' && $path === '/connections') {
    try {
        sendJson(201, createConnection($client, readJsonBody()));
    } catch (Throwable $e) {
        handleApiError($e);
    }
}

// GET /connections — list credential (SIP) connections.
if ($method === 'GET' && $path === '/connections') {
    try {
        sendJson(200, listConnections($client));
    } catch (Throwable $e) {
        handleApiError($e);
    }
}

// GET /connections/{id} — retrieve a single credential (SIP) connection.
if ($method === 'GET' && preg_match('#^/connections/([^/]+)$#', $path, $m)) {
    $connectionId = rawurldecode($m[1]);
    if ($connectionId === '') {
        sendJson(400, ['error' => 'Connection ID must be a non-empty string']);
    }

    try {
        sendJson(200, retrieveConnection($client, $connectionId));
    } catch (Throwable $e) {
        handleApiError($e);
    }
}

// No route matched.
sendJson(404, ['error' => 'Not found']);
