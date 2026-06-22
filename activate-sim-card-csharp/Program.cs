// Production-ready minimal ASP.NET app that enables (activates) a Telnyx SIM card.
//
// Endpoints:
//   POST /sim-cards/{id}/enable  -> enable (activate) a SIM card via the Telnyx SDK
//   POST /webhooks/sim           -> receive + Ed25519-verify Telnyx SIM webhooks
//   GET  /health                 -> liveness probe
//
// The Telnyx .NET SDK uses static configuration (TelnyxConfiguration.SetApiKey) plus
// per-resource service classes. There is NO `new TelnyxClient(...)`. Every SDK call
// throws a single Telnyx.TelnyxException on failure.

using Telnyx;                              // TelnyxConfiguration, SimCardsService, TelnyxException
using Telnyx.net.Entities;                 // TelnyxWebhook<T>
using Telnyx.net.Services.Wireless.SimCards;
using Telnyx.net.Entities.Wireless.SimCards;

DotNetEnv.Env.Load();

var apiKey = Environment.GetEnvironmentVariable("TELNYX_API_KEY");
if (string.IsNullOrWhiteSpace(apiKey))
{
    Console.Error.WriteLine("FATAL: TELNYX_API_KEY is not set. Copy .env.example to .env and fill it in.");
    Environment.Exit(1);
}

// API key is set globally/statically for the SDK.
TelnyxConfiguration.SetApiKey(apiKey);

var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();

// ---------------------------------------------------------------------------
// POST /sim-cards/{id}/enable
// Enable (activate) a SIM card. Maps to POST /sim_cards/{id}/actions/enable.
// ---------------------------------------------------------------------------
app.MapPost("/sim-cards/{id}/enable", async (string id, ILogger<Program> logger) =>
{
    if (string.IsNullOrWhiteSpace(id))
    {
        return Results.BadRequest(new { error = "SIM card id is required." });
    }

    try
    {
        var sim = new SimCardsService();
        SimCardRecord record = await sim.EnableAsync(id);

        return Results.Ok(new
        {
            id = record.Id,
            status = record.Status,
            message = "SIM card enable requested.",
        });
    }
    catch (TelnyxException ex)
    {
        // Log the detail server-side; return a generic message to the caller.
        logger.LogError(ex, "Telnyx API error while enabling SIM card {SimCardId}", id);
        return Results.Problem(
            title: "Failed to enable SIM card.",
            statusCode: StatusCodes.Status502BadGateway);
    }
    catch (Exception ex)
    {
        logger.LogError(ex, "Unexpected error while enabling SIM card {SimCardId}", id);
        return Results.Problem(
            title: "Internal server error.",
            statusCode: StatusCodes.Status500InternalServerError);
    }
});

// ---------------------------------------------------------------------------
// POST /webhooks/sim
// Receive a Telnyx webhook and verify its Ed25519 signature before trusting it.
// The RAW request body MUST be read before any model binding / JSON parsing.
// ---------------------------------------------------------------------------
app.MapPost("/webhooks/sim", async (HttpRequest req, ILogger<Program> logger) =>
{
    using var reader = new StreamReader(req.Body);
    string rawBody = await reader.ReadToEndAsync();

    string signature = req.Headers["telnyx-signature-ed25519"].ToString();
    string timestamp = req.Headers["telnyx-timestamp"].ToString();
    string? publicKey = Environment.GetEnvironmentVariable("TELNYX_PUBLIC_KEY");

    if (string.IsNullOrWhiteSpace(publicKey))
    {
        logger.LogError("TELNYX_PUBLIC_KEY is not set; cannot verify webhook signatures.");
        return Results.Problem(
            title: "Webhook verification is not configured.",
            statusCode: StatusCodes.Status500InternalServerError);
    }

    try
    {
        // ConstructEvent base64-decodes the signature + public key, rebuilds the signed
        // message as "{timestamp}|{rawBody}", Ed25519-verifies it, and enforces the
        // 300s timestamp tolerance. Throws TelnyxException on any failure.
        TelnyxWebhook<object> evt =
            Telnyx.net.Infrastructure.Public.Webhook.ConstructEvent(rawBody, signature, timestamp, publicKey);

        var eventType = evt.Data?.EventType;
        // evt.Data.Payload carries the data.payload object for downstream handling.
        logger.LogInformation("Verified Telnyx webhook: {EventType}", eventType);

        return Results.Ok(new { received = true, event_type = eventType });
    }
    catch (TelnyxException)
    {
        // Bad signature or stale timestamp — never reveal details.
        return Results.Unauthorized();
    }
});

// ---------------------------------------------------------------------------
// GET /health
// ---------------------------------------------------------------------------
app.MapGet("/health", () => Results.Ok(new { status = "ok" }));

app.Run();
