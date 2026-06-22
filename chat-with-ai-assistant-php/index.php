<?php

declare(strict_types=1);

/**
 * Chat with a Telnyx AI Assistant — vanilla PHP front controller.
 *
 * Routes:
 *   POST /chat          Send a message to the assistant; keeps conversation context.
 *   GET  /health        Liveness check.
 *   POST /webhooks      Receive + Ed25519-verify Telnyx webhooks (e.g. conversation events).
 *
 * Credentials are read from the environment only — never hardcode keys.
 */

require __DIR__ . '/vendor/autoload.php';

use Telnyx\Client;
use Telnyx\Core\Exceptions\APIException;
use Telnyx\Core\Exceptions\AuthenticationException;
use Telnyx\Core\Exceptions\RateLimitException;
use Telnyx\Core\Exceptions\APIConnectionException;
use Telnyx\Core\Exceptions\WebhookException;

// Load .env locally if present (no-op in production where env is already set).
if (class_exists(\Dotenv\Dotenv::class)) {
    \Dotenv\Dotenv::createImmutable(__DIR__)->safeLoad();
}

/**
 * Send a JSON response and stop. Keeps every exit path consistent.
 *
 * @param array<string,mixed> $payload
 */
function send_json(int $status, array $payload): void
{
    http_response_code($status);
    header('Content-Type: application/json');
    echo json_encode($payload);
    exit;
}

/**
 * Build a Telnyx client from the environment. apiKey defaults to TELNYX_API_KEY
 * and publicKey to TELNYX_PUBLIC_KEY inside the SDK, but we pass them explicitly
 * so a missing key is obvious.
 */
function make_client(): Client
{
    return new Client(
        apiKey: getenv('TELNYX_API_KEY') ?: null,
        publicKey: getenv('TELNYX_PUBLIC_KEY') ?: null,
    );
}

/**
 * Map a Telnyx SDK exception to an HTTP status + safe, generic message.
 * Never leak exception detail to the client; log the real error server-side.
 *
 * @return array{0:int,1:string}
 */
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
        // $status is a public property on APIException (may be null).
        $status = $e->status ?? 502;
        return [$status, 'The Telnyx API returned an error.'];
    }

    return [500, 'An unexpected error occurred.'];
}

// --- Routing ---------------------------------------------------------------

$method = $_SERVER['REQUEST_METHOD'] ?? 'GET';
$path   = rtrim(parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH) ?: '/', '/');
if ($path === '') {
    $path = '/';
}

// GET /health -- liveness check.
if ($method === 'GET' && $path === '/health') {
    send_json(200, ['status' => 'ok']);
}

// POST /chat -- send a message to the assistant and keep conversation context.
if ($method === 'POST' && $path === '/chat') {
    $assistantId = getenv('TELNYX_ASSISTANT_ID') ?: '';
    if ($assistantId === '') {
        send_json(500, ['error' => 'TELNYX_ASSISTANT_ID is not configured.']);
    }

    $raw  = file_get_contents('php://input') ?: '';
    $body = json_decode($raw, true);
    if (!is_array($body)) {
        send_json(400, ['error' => 'Request body must be valid JSON.']);
    }

    $message = isset($body['message']) && is_string($body['message']) ? trim($body['message']) : '';
    if ($message === '') {
        send_json(400, ['error' => "Missing required field: 'message'."]);
    }

    // Reuse a conversation id across turns to keep context. The client may pass
    // one in; otherwise we create a fresh conversation for this turn.
    $conversationId = isset($body['conversation_id']) && is_string($body['conversation_id'])
        ? trim($body['conversation_id'])
        : '';

    try {
        $client = make_client();

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
    } catch (\Throwable $e) {
        [$status, $msg] = classify_error($e);
        send_json($status, ['error' => $msg]);
    }
}

// POST /webhooks -- Ed25519-verify inbound Telnyx webhooks, then read data.payload.
if ($method === 'POST' && $path === '/webhooks') {
    $raw     = file_get_contents('php://input') ?: '';
    $headers = function_exists('getallheaders') ? getallheaders() : [];

    try {
        $client = make_client();
        // Verifies the Ed25519 signature (telnyx-signature-ed25519 + telnyx-timestamp)
        // against TELNYX_PUBLIC_KEY, enforces replay tolerance, then parses the event.
        $event = $client->webhooks->unwrap($raw, $headers);
    } catch (WebhookException $e) {
        error_log('[chat-with-ai-assistant] webhook verification failed: ' . $e->getMessage());
        send_json(401, ['error' => 'Invalid webhook signature.']);
    }

    // Telnyx v2 webhooks carry fields under data.payload — read from there.
    $eventType = $event->data->eventType ?? 'unknown';
    error_log('[chat-with-ai-assistant] received webhook event: ' . $eventType);

    // Acknowledge quickly with 200.
    send_json(200, ['status' => 'received']);
}

// Fallback.
send_json(404, ['error' => 'Not found.']);
