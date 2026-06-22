<?php

/**
 * Activate (enable) a Telnyx IoT SIM card — vanilla PHP front controller.
 *
 * Routes:
 *   GET  /sim/{id}           Retrieve a SIM card's current state.
 *   POST /sim/{id}/activate  Enable (activate) a SIM card. Activation is async.
 *   POST /webhooks/telnyx    Receive + Ed25519-verify Telnyx SIM card webhooks.
 *   GET  /health             Liveness probe.
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
        sendJson(404, ['error' => 'SIM card not found']);
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
 * Retrieve a SIM card's current state.
 * GET /v2/sim_cards/{id} via $client->simCards->retrieve($id).
 */
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

/**
 * Enable (activate) a SIM card. The SIM must already belong to a SIM card group.
 * POST /v2/sim_cards/{id}/actions/enable via $client->simCards->actions->enable(id: $id).
 *
 * Activation is asynchronous: the call returns a SimCardAction you can poll with
 * $client->simCards->actions->retrieve(id: <action_id>) to follow its status.
 */
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
    error_log('[telnyx] received SIM webhook: ' . $eventType);

    // Acknowledge quickly; do heavy work out of band.
    sendJson(200, ['received' => true]);
}

// SIM routes need a client.
try {
    $client = makeClient();
} catch (Throwable $e) {
    error_log('[telnyx] client init failed: ' . $e->getMessage());
    sendJson(500, ['error' => 'Server misconfigured']);
}

// GET /sim/{id} — retrieve a SIM card.
if ($method === 'GET' && preg_match('#^/sim/([^/]+)$#', $path, $m)) {
    $simCardId = rawurldecode($m[1]);
    if ($simCardId === '') {
        sendJson(400, ['error' => 'SIM card ID must be a non-empty string']);
    }

    try {
        sendJson(200, retrieveSim($client, $simCardId));
    } catch (Throwable $e) {
        handleApiError($e);
    }
}

// POST /sim/{id}/activate — enable (activate) a SIM card.
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

// No route matched.
sendJson(404, ['error' => 'Not found']);
