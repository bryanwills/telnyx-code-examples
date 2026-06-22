<?php

/**
 * Receive inbound SMS webhooks from Telnyx — vanilla PHP front controller.
 *
 * Routes:
 *   POST /webhooks/sms   Receive + Ed25519-verify Telnyx inbound SMS webhooks,
 *                        then read the message from data.payload.
 *   GET  /health         Liveness probe.
 *
 * The webhook signature is ALWAYS verified before the event is trusted:
 * $client->webhooks->unwrap() validates the Telnyx-Signature-Ed25519 header
 * over "<telnyx-timestamp>|<raw body>" (with a 300s timestamp tolerance) and
 * parses the event in one call.
 *
 * Run locally with PHP's built-in server:
 *   php -S localhost:8080 index.php
 */

declare(strict_types=1);

require __DIR__ . '/vendor/autoload.php';

use Telnyx\Client;
use Telnyx\Core\Exceptions\WebhookException;

// Load .env when present (no-op in production where vars come from the environment).
if (class_exists(\Dotenv\Dotenv::class)) {
    \Dotenv\Dotenv::createImmutable(__DIR__)->safeLoad();
}

/**
 * Build the Telnyx client. apiKey defaults to TELNYX_API_KEY and publicKey to
 * TELNYX_PUBLIC_KEY; both are read from the environment, never hardcoded.
 * The publicKey is the base64 Ed25519 key the SDK uses to verify webhooks.
 */
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

/** Emit a JSON response with the given HTTP status code and exit. */
function sendJson(int $status, array $body): void
{
    http_response_code($status);
    header('Content-Type: application/json');
    echo json_encode($body, JSON_UNESCAPED_SLASHES);
    exit;
}

/**
 * Extract the inbound SMS fields from a verified webhook event.
 *
 * Telnyx v2 webhooks carry the event under data.payload. For an inbound SMS:
 *   $event->data->eventType            -> "message.received"
 *   $event->data->payload->id          -> message id
 *   $event->data->payload->from        -> From object (->phoneNumber)
 *   $event->data->payload->to          -> array of To objects (->phoneNumber)
 *   $event->data->payload->text        -> message body
 *   $event->data->payload->receivedAt  -> ISO-8601 timestamp
 *
 * @return array<string, mixed>
 */
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

// POST /webhooks/sms — verify Ed25519 signature, then read data.payload.
if ($method === 'POST' && $path === '/webhooks/sms') {
    $raw = file_get_contents('php://input') ?: '';
    $headers = function_exists('getallheaders') ? (getallheaders() ?: []) : [];

    // Build the client first; a misconfigured server must not look like a bad signature.
    try {
        $client = makeClient();
    } catch (Throwable $e) {
        error_log('[telnyx] client init failed: ' . $e->getMessage());
        sendJson(500, ['error' => 'Server misconfigured']);
    }

    // unwrap() verifies the Telnyx Ed25519 signature AND parses the event.
    // On a missing/invalid signature it throws WebhookException — never trust
    // an event whose signature did not verify.
    try {
        $event = $client->webhooks->unwrap($raw, $headers);
    } catch (WebhookException $e) {
        error_log('[telnyx] webhook verification failed: ' . $e->getMessage());
        sendJson(401, ['error' => 'Invalid webhook signature']);
    } catch (Throwable $e) {
        error_log('[telnyx] webhook error: ' . get_class($e) . ': ' . $e->getMessage());
        sendJson(400, ['error' => 'Bad webhook request']);
    }

    // Only inbound SMS ("message.received") is processed here; acknowledge the rest.
    $eventType = $event->data->eventType ?? 'unknown';
    if ($eventType !== 'message.received') {
        sendJson(200, ['status' => 'ignored', 'eventType' => $eventType]);
    }

    try {
        $message = extractInboundSms($event);

        // Acknowledge quickly; persist / fan out heavy work out of band.
        error_log(sprintf(
            '[telnyx] inbound SMS %s from %s',
            (string) ($message['messageId'] ?? 'unknown'),
            (string) ($message['from'] ?? 'unknown')
        ));

        sendJson(200, [
            'status'    => 'received',
            'messageId' => $message['messageId'],
        ]);
    } catch (Throwable $e) {
        // Log, but still ack with 200 so Telnyx does not retry a poison event.
        error_log('[telnyx] failed to process inbound SMS: ' . $e->getMessage());
        sendJson(200, ['status' => 'error']);
    }
}

// No route matched.
sendJson(404, ['error' => 'Not found']);
