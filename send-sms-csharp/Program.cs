using System.Text.Json.Serialization;
using Telnyx;                       // TelnyxConfiguration, MessagingSenderIdService, TelnyxException
using Telnyx.net.Entities;          // MessagingSenderId, NewMessagingSenderId, TelnyxWebhook<T>

// ---------------------------------------------------------------------------
// Bootstrap
// ---------------------------------------------------------------------------
DotNetEnv.Env.Load();   // load .env into the environment (no-op if the file is absent)

var apiKey = Environment.GetEnvironmentVariable("TELNYX_API_KEY");
if (string.IsNullOrWhiteSpace(apiKey))
{
    Console.Error.WriteLine("FATAL: TELNYX_API_KEY is not set. Copy .env.example to .env and fill it in.");
    return;
}

// The Telnyx.net SDK uses a GLOBAL/static API key — there is no `new TelnyxClient(...)`.
TelnyxConfiguration.SetApiKey(apiKey);

var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();

// ---------------------------------------------------------------------------
// POST /sms/send  — send a single SMS
// ---------------------------------------------------------------------------
app.MapPost("/sms/send", async (SendSmsRequest request) =>
{
    if (string.IsNullOrWhiteSpace(request.To) || string.IsNullOrWhiteSpace(request.Message))
    {
        return Results.BadRequest(new { error = "Missing required fields: 'to' and 'message'" });
    }

    var fromNumber = Environment.GetEnvironmentVariable("TELNYX_PHONE_NUMBER");
    if (string.IsNullOrWhiteSpace(fromNumber))
    {
        return Results.BadRequest(new { error = "TELNYX_PHONE_NUMBER environment variable not set" });
    }

    // Validate E.164 format up front to avoid an avoidable round trip to the API.
    if (!request.To.StartsWith('+'))
    {
        return Results.BadRequest(new { error = "Phone number must be in E.164 format (e.g., +15551234567)" });
    }

    try
    {
        // MessagingSenderIdService POSTs to /messages — the canonical send path in this SDK.
        var service = new MessagingSenderIdService();
        var options = new NewMessagingSenderId
        {
            From = fromNumber,       // +E.164, alphanumeric, or short code
            To = request.To,         // +E.164
            Text = request.Message,
        };

        MessagingSenderId message = await service.CreateAsync(options);

        // Return only serializable, non-sensitive fields — never the raw SDK object.
        return Results.Ok(new
        {
            message_id = message.Id,
            from = fromNumber,
            to = request.To,
        });
    }
    catch (TelnyxException ex)
    {
        // Every SDK call throws a single Telnyx.TelnyxException. Log the detail
        // server-side; return a generic message so we never leak it to the client.
        app.Logger.LogError(ex, "Telnyx API error while sending SMS");
        return Results.Json(new { error = "Failed to send message" }, statusCode: 502);
    }
    catch (Exception ex)
    {
        app.Logger.LogError(ex, "Unexpected error while sending SMS");
        return Results.Json(new { error = "Internal server error" }, statusCode: 500);
    }
});

// ---------------------------------------------------------------------------
// POST /webhooks/sms  — receive + signature-verify inbound message webhooks
// ---------------------------------------------------------------------------
app.MapPost("/webhooks/sms", async (HttpRequest req) =>
{
    // CRITICAL: read the RAW body BEFORE any model binding / JSON parsing.
    // A re-serialized body changes the bytes and breaks Ed25519 verification.
    using var reader = new StreamReader(req.Body);
    string rawBody = await reader.ReadToEndAsync();

    string signature = req.Headers["telnyx-signature-ed25519"].ToString();
    string timestamp = req.Headers["telnyx-timestamp"].ToString();
    var publicKey = Environment.GetEnvironmentVariable("TELNYX_PUBLIC_KEY");

    if (string.IsNullOrWhiteSpace(publicKey))
    {
        app.Logger.LogError("TELNYX_PUBLIC_KEY is not set; cannot verify webhook signatures");
        return Results.Json(new { error = "Server not configured for webhooks" }, statusCode: 500);
    }

    try
    {
        // ConstructEvent rebuilds the signed message as "{timestamp}|{rawBody}",
        // Ed25519-verifies it, and enforces a 300s timestamp tolerance.
        TelnyxWebhook<object> evt = Telnyx.net.Infrastructure.Public.Webhook.ConstructEvent(
            rawBody, signature, timestamp, publicKey);

        var eventType = evt.Data.EventType;   // e.g. "message.received"
        var payload = evt.Data.Payload;       // the data.payload object

        app.Logger.LogInformation("Received verified Telnyx webhook: {EventType}", eventType);
        _ = payload; // process inbound payload here (store, reply, enqueue, ...)

        return Results.Ok();
    }
    catch (TelnyxException)
    {
        // Bad signature or stale timestamp — reject without leaking detail.
        return Results.Unauthorized();
    }
});

app.Run();

// ---------------------------------------------------------------------------
// Request model
// ---------------------------------------------------------------------------
public class SendSmsRequest
{
    [JsonPropertyName("to")]
    public string? To { get; set; }

    [JsonPropertyName("message")]
    public string? Message { get; set; }
}
