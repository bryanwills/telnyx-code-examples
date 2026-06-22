// Production-ready minimal ASP.NET endpoint that places an outbound Call Control
// call with the official Telnyx .NET SDK (Telnyx.net), plus an optional webhook
// receiver that verifies the Telnyx Ed25519 signature.

using Telnyx;                 // TelnyxConfiguration, TelnyxException
using Telnyx.net.Entities;    // CallControlDialOptions, CallDialResponse, TelnyxWebhook<T>
using Telnyx.net.Services.Calls.CallCommands;  // CallControlService

DotNetEnv.Env.Load();

// The Telnyx SDK uses a GLOBAL/static API key — there is no `new TelnyxClient(...)`.
var apiKey = Environment.GetEnvironmentVariable("TELNYX_API_KEY");
if (string.IsNullOrWhiteSpace(apiKey))
{
    throw new InvalidOperationException("TELNYX_API_KEY environment variable not set");
}
TelnyxConfiguration.SetApiKey(apiKey);

var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();

// ---------------------------------------------------------------------------
// POST /calls/dial — place an outbound call.
// Body: { "to": "+12125551234" }
// ---------------------------------------------------------------------------
app.MapPost("/calls/dial", async (DialRequest request, ILogger<Program> logger) =>
{
    if (request is null || string.IsNullOrWhiteSpace(request.To))
    {
        return Results.BadRequest(new { error = "Missing required field: 'to'" });
    }

    // Validate E.164 format up front to avoid an avoidable upstream error.
    if (!request.To.StartsWith('+'))
    {
        return Results.BadRequest(new
        {
            error = "Phone number must be in E.164 format (e.g., +15551234567)"
        });
    }

    var fromNumber = Environment.GetEnvironmentVariable("TELNYX_PHONE_NUMBER");
    var connectionId = Environment.GetEnvironmentVariable("TELNYX_CONNECTION_ID");

    if (string.IsNullOrWhiteSpace(fromNumber))
    {
        return Results.BadRequest(new { error = "TELNYX_PHONE_NUMBER environment variable not set" });
    }
    if (string.IsNullOrWhiteSpace(connectionId))
    {
        return Results.BadRequest(new { error = "TELNYX_CONNECTION_ID environment variable not set" });
    }

    try
    {
        var callControl = new CallControlService();
        var options = new CallControlDialOptions
        {
            To = request.To,                 // +E.164 or sip:user@sip.telnyx.com
            From = fromNumber,               // your Telnyx number (E.164)
            ConnectionId = connectionId,     // Call Control Application ID (required)
        };

        // POST /calls -> CallDialResponse (parsed from the `data` token).
        CallDialResponse response = await callControl.DialAsync(options);

        return Results.Ok(new
        {
            call_control_id = response.CallControlId,
            call_session_id = response.CallSessionId,
            call_leg_id = response.CallLegId,
            is_alive = response.IsAlive,
            from = fromNumber,
            to = request.To,
        });
    }
    catch (TelnyxException ex)
    {
        // The SDK surfaces every API failure as a single TelnyxException.
        // Log the detail server-side; never leak it to the HTTP response.
        logger.LogError(ex, "Telnyx API error while dialing {To}", request.To);
        return Results.StatusCode(StatusCodes.Status502BadGateway);
    }
    catch (Exception ex)
    {
        logger.LogError(ex, "Unexpected error while dialing {To}", request.To);
        return Results.StatusCode(StatusCodes.Status500InternalServerError);
    }
});

// ---------------------------------------------------------------------------
// POST /webhooks/calls — receive call lifecycle events.
// Verifies the Telnyx Ed25519 signature before trusting the payload.
// ---------------------------------------------------------------------------
app.MapPost("/webhooks/calls", async (HttpRequest req, ILogger<Program> logger) =>
{
    // CRITICAL: read the RAW body before any model binding / JSON parsing —
    // a re-serialized body breaks the signature.
    using var reader = new StreamReader(req.Body);
    string rawBody = await reader.ReadToEndAsync();

    string signature = req.Headers["telnyx-signature-ed25519"].ToString();
    string timestamp = req.Headers["telnyx-timestamp"].ToString();
    string? publicKey = Environment.GetEnvironmentVariable("TELNYX_PUBLIC_KEY");

    if (string.IsNullOrWhiteSpace(publicKey))
    {
        logger.LogError("TELNYX_PUBLIC_KEY environment variable not set");
        return Results.StatusCode(StatusCodes.Status500InternalServerError);
    }

    try
    {
        // ConstructEvent verifies the Ed25519 signature over "{timestamp}|{rawBody}"
        // and enforces a 300s timestamp tolerance; throws TelnyxException on failure.
        TelnyxWebhook<object> evt =
            Telnyx.net.Infrastructure.Public.Webhook.ConstructEvent(
                rawBody, signature, timestamp, publicKey);

        var eventType = evt.Data.EventType;   // e.g. call.answered, call.hangup
        var payload = evt.Data.Payload;       // the data.payload object

        logger.LogInformation("Received verified webhook: {EventType}", eventType);

        // Act on payload fields here (read from data.payload), then acknowledge.
        return Results.Ok();
    }
    catch (TelnyxException)
    {
        // Bad signature or stale timestamp.
        return Results.Unauthorized();
    }
});

app.Run();

// Request body for POST /calls/dial.
public record DialRequest(string To);
