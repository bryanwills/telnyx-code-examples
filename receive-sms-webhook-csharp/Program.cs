// Program.cs
// Production-ready ASP.NET (minimal API) receiver for inbound SMS via Telnyx.
//
// Security model:
//   - Every webhook is verified with the Telnyx Ed25519 signature scheme BEFORE
//     the body is trusted or parsed. The signed message is "<telnyx-timestamp>|<raw body>".
//   - Verification uses the official SDK helper Telnyx.net.Infrastructure.Public.Webhook
//     .ConstructEvent, which Ed25519-verifies the signature and enforces a timestamp
//     tolerance. On failure it throws Telnyx.TelnyxException and we return 401.
//   - The RAW request body is read first; re-serialized bodies would break the signature.
//   - Message fields are read from data.payload (the Telnyx webhook envelope).
//   - Error responses never leak exception details; full detail is logged server-side.

using System.Text.Json;
using Telnyx.net.Entities;

var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();
var logger = app.Logger;

// Load environment variables from a local .env file (if present).
DotNetEnv.Env.Load();

// Base64 account public key from portal.telnyx.com (Account > Public Key).
// Required to verify inbound webhook signatures.
var publicKey = Environment.GetEnvironmentVariable("TELNYX_PUBLIC_KEY");

// In-memory store of received messages. Replace with a database in production.
var receivedMessages = new List<InboundMessage>();
var storeLock = new object();

// ---------------------------------------------------------------------------
// POST /webhooks/sms — inbound SMS webhook receiver.
// Telnyx delivers message.received events here. We verify the Ed25519 signature
// over the raw body, then read fields from data.payload.
// ---------------------------------------------------------------------------
app.MapPost("/webhooks/sms", async (HttpRequest req) =>
{
    // 1. Read the RAW, unparsed body. Model binding / re-serialization would
    //    change the bytes and invalidate the signature.
    string rawBody;
    using (var reader = new StreamReader(req.Body))
    {
        rawBody = await reader.ReadToEndAsync();
    }

    string signature = req.Headers["telnyx-signature-ed25519"].ToString();
    string timestamp = req.Headers["telnyx-timestamp"].ToString();

    // 2. Fail closed if we have no public key configured — never trust an
    //    unverifiable webhook.
    if (string.IsNullOrEmpty(publicKey))
    {
        logger.LogError("TELNYX_PUBLIC_KEY is not set; cannot verify webhook signature.");
        return Results.StatusCode(StatusCodes.Status503ServiceUnavailable);
    }

    if (string.IsNullOrEmpty(signature) || string.IsNullOrEmpty(timestamp))
    {
        logger.LogWarning("Webhook rejected: missing telnyx-signature-ed25519 or telnyx-timestamp header.");
        return Results.Unauthorized();
    }

    // 3. Verify the Ed25519 signature over "<timestamp>|<raw body>" using the SDK
    //    helper. Throws Telnyx.TelnyxException on a bad signature or stale timestamp.
    TelnyxWebhook<object> evt;
    try
    {
        evt = Telnyx.net.Infrastructure.Public.Webhook.ConstructEvent(
            rawBody, signature, timestamp, publicKey);
    }
    catch (Telnyx.TelnyxException ex)
    {
        // Bad signature or timestamp outside the tolerance window.
        logger.LogWarning(ex, "Webhook signature verification failed.");
        return Results.Unauthorized();
    }

    // 4. Only inbound SMS (message.received) carries a message to process.
    var eventType = evt.Data?.EventType;
    if (eventType != "message.received")
    {
        logger.LogInformation("Ignoring event type: {EventType}", eventType ?? "(none)");
        return Results.Ok(new { status = "ignored" });
    }

    // 5. Read message fields from data.payload. We parse the verified raw body
    //    with System.Text.Json to safely extract the nested payload fields.
    try
    {
        using var doc = JsonDocument.Parse(rawBody);
        if (!doc.RootElement.TryGetProperty("data", out var data) ||
            !data.TryGetProperty("payload", out var payload))
        {
            logger.LogWarning("Webhook rejected: missing data.payload.");
            return Results.BadRequest(new { error = "Invalid webhook payload structure" });
        }

        var message = new InboundMessage
        {
            MessageId = GetString(payload, "id"),
            From = GetPhoneNumber(payload, "from"),
            To = GetFirstToPhoneNumber(payload),
            Text = GetString(payload, "text") ?? string.Empty,
            ReceivedAt = GetString(payload, "received_at") ?? DateTime.UtcNow.ToString("o"),
            Direction = GetString(payload, "direction") ?? "inbound",
        };

        if (string.IsNullOrEmpty(message.From) || string.IsNullOrEmpty(message.To))
        {
            logger.LogWarning("Webhook rejected: missing sender or recipient phone number.");
            return Results.BadRequest(new { error = "Missing sender or recipient phone number" });
        }

        lock (storeLock)
        {
            receivedMessages.Add(message);
        }

        logger.LogInformation(
            "Inbound SMS received. From: {From}, To: {To}", message.From, message.To);

        // Telnyx expects a 2xx response within 5 seconds, otherwise it retries.
        return Results.Ok(new
        {
            success = true,
            message_id = message.MessageId,
            status = "received",
        });
    }
    catch (JsonException ex)
    {
        // Body passed signature verification but is not valid JSON — should not
        // happen for real Telnyx traffic. Log detail, return a generic message.
        logger.LogWarning(ex, "Failed to parse verified webhook body as JSON.");
        return Results.BadRequest(new { error = "Invalid webhook payload" });
    }
});

// ---------------------------------------------------------------------------
// GET /messages — debug endpoint listing received messages (remove in production).
// ---------------------------------------------------------------------------
app.MapGet("/messages", () =>
{
    lock (storeLock)
    {
        return Results.Ok(new { count = receivedMessages.Count, messages = receivedMessages });
    }
});

// ---------------------------------------------------------------------------
// GET /health — liveness check.
// ---------------------------------------------------------------------------
app.MapGet("/health", () =>
    Results.Ok(new { status = "ok", timestamp = DateTime.UtcNow.ToString("o") }));

app.Run();

// ---- helpers -------------------------------------------------------------

static string? GetString(JsonElement obj, string name) =>
    obj.TryGetProperty(name, out var v) && v.ValueKind == JsonValueKind.String
        ? v.GetString()
        : null;

// Telnyx nests the sender under data.payload.from.phone_number.
static string? GetPhoneNumber(JsonElement payload, string name) =>
    payload.TryGetProperty(name, out var node) &&
    node.ValueKind == JsonValueKind.Object
        ? GetString(node, "phone_number")
        : null;

// Telnyx nests recipients under data.payload.to[0].phone_number.
static string? GetFirstToPhoneNumber(JsonElement payload)
{
    if (payload.TryGetProperty("to", out var to) &&
        to.ValueKind == JsonValueKind.Array &&
        to.GetArrayLength() > 0)
    {
        return GetString(to[0], "phone_number");
    }
    return null;
}

// Processed inbound message shape stored in memory / returned by /messages.
internal sealed class InboundMessage
{
    public string? MessageId { get; set; }
    public string? From { get; set; }
    public string? To { get; set; }
    public string Text { get; set; } = string.Empty;
    public string ReceivedAt { get; set; } = string.Empty;
    public string Direction { get; set; } = "inbound";
}
