<?php

declare(strict_types=1);

/**
 * Send SMS — vanilla PHP front controller.
 *
 * Exposes POST /sms/send which sends a single SMS through the Telnyx
 * Messaging API using the Telnyx PHP SDK (telnyx/telnyx-php ^7.84).
 *
 * Run locally with the built-in PHP web server:
 *   php -S localhost:8080 index.php
 */

require __DIR__ . '/vendor/autoload.php';

use Telnyx\Client;
use Telnyx\Core\Exceptions\AuthenticationException;
use Telnyx\Core\Exceptions\RateLimitException;
use Telnyx\Core\Exceptions\APIStatusException;
use Telnyx\Core\Exceptions\APIConnectionException;
use Telnyx\Core\Exceptions\APIException;

// Load .env when running locally (no-op if the file is absent).
if (class_exists(\Dotenv\Dotenv::class)) {
    \Dotenv\Dotenv::createImmutable(__DIR__)->safeLoad();
}

/**
 * Send a JSON response and stop. Keeps error bodies generic so internal
 * exception detail never leaks to the client.
 */
function send_json(int $status, array $body): void
{
    http_response_code($status);
    header('Content-Type: application/json');
    echo json_encode($body);
    exit;
}

// --- Routing -----------------------------------------------------------------

$method = $_SERVER['REQUEST_METHOD'] ?? 'GET';
$path = parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH);

if ($method !== 'POST' || $path !== '/sms/send') {
    send_json(404, ['error' => 'Not found']);
}

// --- Parse request body ------------------------------------------------------

$raw = file_get_contents('php://input');
$input = json_decode($raw ?: '{}', true);

if (!is_array($input)) {
    send_json(400, ['error' => 'Request body must be valid JSON']);
}

$toNumber = isset($input['to']) && is_string($input['to']) ? trim($input['to']) : '';
$message = isset($input['message']) && is_string($input['message']) ? $input['message'] : '';

// Validate presence of required fields.
if ($toNumber === '' || $message === '') {
    send_json(400, ['error' => "Missing required fields: 'to' and 'message'"]);
}

// Validate E.164 format to prevent API errors.
if (!str_starts_with($toNumber, '+')) {
    send_json(400, ['error' => 'Phone number must be in E.164 format (e.g., +15551234567)']);
}

$fromNumber = getenv('TELNYX_PHONE_NUMBER') ?: ($_ENV['TELNYX_PHONE_NUMBER'] ?? '');
if ($fromNumber === '') {
    send_json(500, ['error' => 'TELNYX_PHONE_NUMBER environment variable not set']);
}

// --- Send the message --------------------------------------------------------

try {
    // Constructor uses named params; apiKey falls back to the TELNYX_API_KEY env var.
    $client = new Client(
        apiKey: getenv('TELNYX_API_KEY') ?: ($_ENV['TELNYX_API_KEY'] ?? null),
    );

    // Telnyx PHP SDK 7.x: messages->send() with NAMED params (not messages->create()).
    $response = $client->messages->send(
        to: $toNumber,
        from: $fromNumber,
        text: $message,
    );

    $recipients = $response->data->to ?? [];
    $status = (is_array($recipients) && isset($recipients[0]->status)) ? $recipients[0]->status : 'unknown';

    send_json(200, [
        'message_id' => $response->data->id,
        'status' => $status,
        'from' => $fromNumber,
        'to' => $toNumber,
    ]);
} catch (AuthenticationException $e) {
    error_log('Telnyx authentication error: ' . $e->getMessage());
    send_json(401, ['error' => 'Invalid API key']);
} catch (RateLimitException $e) {
    error_log('Telnyx rate limit: ' . $e->getMessage());
    send_json(429, ['error' => 'Rate limit exceeded. Please slow down.']);
} catch (APIConnectionException $e) {
    error_log('Telnyx connection error: ' . $e->getMessage());
    send_json(503, ['error' => 'Network error connecting to Telnyx']);
} catch (APIStatusException $e) {
    // $e->status is the HTTP status returned by Telnyx (public int property).
    error_log('Telnyx API error (' . $e->status . '): ' . $e->getMessage());
    $status = ($e->status >= 400 && $e->status < 600) ? $e->status : 502;
    send_json($status, ['error' => 'Telnyx rejected the request']);
} catch (APIException $e) {
    error_log('Telnyx error: ' . $e->getMessage());
    send_json(502, ['error' => 'Failed to send message']);
}
