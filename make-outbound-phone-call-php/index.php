<?php

declare(strict_types=1);

/**
 * Production-ready vanilla-PHP front controller for placing outbound calls
 * via the Telnyx Call Control API (calls.dial), with an Ed25519-verified
 * webhook receiver for call lifecycle events.
 *
 * Routes:
 *   POST /calls/dial       Place an outbound call.
 *   POST /webhooks/calls   Receive + verify Telnyx call control webhooks.
 *
 * Run locally:
 *   composer install
 *   php -S localhost:8080 index.php
 */

require __DIR__ . '/vendor/autoload.php';

use Dotenv\Dotenv;
use Telnyx\Client;
use Telnyx\Core\Exceptions\APIConnectionException;
use Telnyx\Core\Exceptions\APIStatusException;
use Telnyx\Core\Exceptions\AuthenticationException;
use Telnyx\Core\Exceptions\RateLimitException;
use Telnyx\Core\Exceptions\WebhookException;

// Load .env when running locally (no-op if the file is absent).
if (class_exists(Dotenv::class)) {
    Dotenv::createImmutable(__DIR__)->safeLoad();
}

/**
 * Build a Telnyx client from environment credentials.
 *
 * apiKey is required to dial; publicKey is required to verify webhooks.
 * The constructor uses named parameters and falls back to the
 * TELNYX_API_KEY / TELNYX_PUBLIC_KEY environment variables when null.
 */
function makeClient(): Client
{
    return new Client(
        apiKey: getenv('TELNYX_API_KEY') ?: null,
        publicKey: getenv('TELNYX_PUBLIC_KEY') ?: null,
    );
}

/**
 * Send a JSON response and end the request.
 *
 * @param array<string,mixed> $body
 */
function jsonResponse(int $status, array $body): void
{
    http_response_code($status);
    header('Content-Type: application/json');
    echo json_encode($body);
    exit;
}

/**
 * Place an outbound call via Call Control and return JSON-serializable data.
 *
 * connectionID links the call to your Call Control Application and is REQUIRED.
 * The call_control_id is RETURNED in the response — use it for follow-up commands.
 *
 * @return array<string,mixed>
 */
function initiateCall(Client $client, string $toNumber): array
{
    $fromNumber   = getenv('TELNYX_PHONE_NUMBER') ?: '';
    $connectionId = getenv('TELNYX_CONNECTION_ID') ?: '';

    if ($fromNumber === '') {
        throw new InvalidArgumentException('TELNYX_PHONE_NUMBER environment variable not set');
    }
    if ($connectionId === '') {
        throw new InvalidArgumentException('TELNYX_CONNECTION_ID environment variable not set');
    }
    // Validate E.164 format to fail fast before hitting the API.
    if (!str_starts_with($toNumber, '+')) {
        throw new InvalidArgumentException('Phone number must be in E.164 format (e.g., +15551234567)');
    }

    // POST /v2/calls — first three params in order: connectionID, from, to (all camelCase).
    $response = $client->calls->dial(
        connectionID: $connectionId,
        from: $fromNumber,
        to: $toNumber,
    );

    // SDK objects are not directly JSON-serializable; map to a plain array.
    return [
        'call_control_id' => $response->data->callControlID,
        'call_leg_id'     => $response->data->callLegID,
        'call_session_id' => $response->data->callSessionID,
        'is_alive'        => $response->data->isAlive,
        'from'            => $fromNumber,
        'to'              => $toNumber,
    ];
}

/**
 * POST /calls/dial — read `to` from the JSON body and place the call.
 */
function handleDial(Client $client): void
{
    $raw  = file_get_contents('php://input') ?: '';
    $body = json_decode($raw, true);

    if (!is_array($body) || !isset($body['to']) || !is_string($body['to']) || $body['to'] === '') {
        jsonResponse(400, ['error' => "Missing required field: 'to'"]);
    }

    try {
        $result = initiateCall($client, $body['to']);
        jsonResponse(200, $result);
    } catch (InvalidArgumentException $e) {
        // Input/configuration validation — safe to surface the message.
        jsonResponse(400, ['error' => $e->getMessage()]);
    } catch (AuthenticationException $e) {
        error_log('Telnyx authentication error: ' . $e->getMessage());
        jsonResponse(401, ['error' => 'Invalid API key']);
    } catch (RateLimitException $e) {
        error_log('Telnyx rate limit: ' . $e->getMessage());
        jsonResponse(429, ['error' => 'Rate limit exceeded. Please slow down.']);
    } catch (APIConnectionException $e) {
        error_log('Telnyx connection error: ' . $e->getMessage());
        jsonResponse(503, ['error' => 'Network error connecting to Telnyx']);
    } catch (APIStatusException $e) {
        // Upstream 4xx/5xx — log details, return a generic message + the status.
        error_log('Telnyx API status error: ' . $e->getMessage());
        $status = $e->status ?? 502;
        jsonResponse($status, ['error' => 'Telnyx API error', 'status_code' => $status]);
    } catch (Throwable $e) {
        // Never leak internal exception details to the client.
        error_log('Unhandled error in handleDial: ' . $e->getMessage());
        jsonResponse(500, ['error' => 'Internal server error']);
    }
}

/**
 * POST /webhooks/calls — verify the Ed25519 signature and acknowledge.
 *
 * unwrap() verifies the signature using TELNYX_PUBLIC_KEY and parses the
 * payload in one call; on a bad signature it throws WebhookException.
 */
function handleWebhook(Client $client): void
{
    $payload = file_get_contents('php://input') ?: '';
    $headers = function_exists('getallheaders') ? (getallheaders() ?: []) : [];

    try {
        $event = $client->webhooks->unwrap($payload, $headers);
    } catch (WebhookException $e) {
        error_log('Webhook signature verification failed: ' . $e->getMessage());
        jsonResponse(401, ['error' => 'Invalid signature']);
    } catch (Throwable $e) {
        error_log('Webhook processing error: ' . $e->getMessage());
        jsonResponse(400, ['error' => 'Bad request']);
    }

    // Telnyx v2 webhooks carry event data under data.payload.
    $eventType = $event->data->eventType ?? 'unknown';
    error_log('Received verified call webhook: ' . $eventType);

    // Acknowledge quickly; drive your call flow off data.payload here.
    jsonResponse(200, ['status' => 'ok', 'event_type' => $eventType]);
}

// ---------------------------------------------------------------------------
// Router
// ---------------------------------------------------------------------------

$method = $_SERVER['REQUEST_METHOD'] ?? 'GET';
$path   = parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH) ?: '/';

$client = makeClient();

if ($method === 'POST' && $path === '/calls/dial') {
    handleDial($client);
} elseif ($method === 'POST' && $path === '/webhooks/calls') {
    handleWebhook($client);
} else {
    jsonResponse(404, ['error' => 'Not found']);
}
