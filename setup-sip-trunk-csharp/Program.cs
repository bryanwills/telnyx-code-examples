// Production-ready minimal ASP.NET (net8.0) app that creates, lists, and
// retrieves Telnyx credential (SIP) connections via the official Telnyx.net SDK.
//
// Endpoints:
//   POST /sip/connections        -> create a credential SIP connection
//   GET  /sip/connections        -> list credential SIP connections
//   GET  /sip/connections/{id}   -> retrieve one credential SIP connection
//   POST /webhooks/telnyx        -> receive + Ed25519-verify inbound webhooks

using Telnyx;                                          // TelnyxConfiguration, services, TelnyxException
using Telnyx.net.Entities;                             // TelnyxList<T>, TelnyxWebhook<T>
using Telnyx.net.Entities.Connections;                 // ConnectionListOptions
using Telnyx.net.Entities.Connections.CredentialConnections; // UpsertCredentialConnectionOptions, CredentialConnection
using Telnyx.net.Services.Connections.CredentialConnections; // CredentialConnectionService

// Load variables from a local .env file (if present) into the environment.
DotNetEnv.Env.Load();

var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();
var logger = app.Logger;

// --- Configuration -----------------------------------------------------------
// The Telnyx.net SDK is configured globally/statically. There is no client object.
var apiKey = Environment.GetEnvironmentVariable("TELNYX_API_KEY");
if (string.IsNullOrWhiteSpace(apiKey))
{
    logger.LogError("TELNYX_API_KEY is not set. Copy .env.example to .env and add your key.");
    throw new InvalidOperationException("TELNYX_API_KEY environment variable is required.");
}

TelnyxConfiguration.SetApiKey(apiKey);
// Optional override; defaults to https://api.telnyx.com/v2 when unset.
var apiBase = Environment.GetEnvironmentVariable("TELNYX_API_BASE_URL");
if (!string.IsNullOrWhiteSpace(apiBase))
{
    TelnyxConfiguration.SetApiBase(apiBase);
}

// --- Endpoints ---------------------------------------------------------------

// POST /sip/connections — create a credential SIP connection.
app.MapPost("/sip/connections", async (CreateConnectionRequest body) =>
{
    if (string.IsNullOrWhiteSpace(body.Name) ||
        string.IsNullOrWhiteSpace(body.Username) ||
        string.IsNullOrWhiteSpace(body.Password))
    {
        return Results.BadRequest(new { error = "name, username, and password are required" });
    }

    try
    {
        var svc = new CredentialConnectionService();
        var options = new UpsertCredentialConnectionOptions
        {
            ConnectionName = body.Name,   // inherited from UpsertConnectionOptions
            UserName = body.Username,
            Password = body.Password,
            Active = body.Active ?? true,
        };

        CredentialConnection created = await svc.CreateCredentialConnectionAsync(options);
        return Results.Created($"/sip/connections/{created.Id}", ToView(created));
    }
    catch (TelnyxException ex)
    {
        // Log the detail server-side; return a generic message to the caller.
        logger.LogError(ex, "Telnyx API error while creating credential connection.");
        return Results.Problem(
            title: "Failed to create SIP connection",
            statusCode: StatusCodes.Status502BadGateway);
    }
});

// GET /sip/connections — list credential SIP connections.
app.MapGet("/sip/connections", async (int? page, int? pageSize) =>
{
    try
    {
        var svc = new CredentialConnectionService();
        var listOptions = new ConnectionListOptions
        {
            PageNumber = page ?? 1,
            PageSize = pageSize ?? 20,
        };

        TelnyxList<CredentialConnection> list =
            await svc.ListCredentialConnectionAsync(listOptions);

        // TelnyxList<T> implements IEnumerable<T>; project to safe view objects.
        var items = list.Select(ToView).ToList();
        return Results.Ok(new { data = items });
    }
    catch (TelnyxException ex)
    {
        logger.LogError(ex, "Telnyx API error while listing credential connections.");
        return Results.Problem(
            title: "Failed to list SIP connections",
            statusCode: StatusCodes.Status502BadGateway);
    }
});

// GET /sip/connections/{id} — retrieve one credential SIP connection.
app.MapGet("/sip/connections/{id}", async (string id) =>
{
    if (string.IsNullOrWhiteSpace(id))
    {
        return Results.BadRequest(new { error = "connection id is required" });
    }

    try
    {
        var svc = new CredentialConnectionService();
        CredentialConnection one = await svc.RetrieveCredentialConnectionAsync(id);
        return Results.Ok(ToView(one));
    }
    catch (TelnyxException ex)
    {
        logger.LogError(ex, "Telnyx API error while retrieving credential connection {Id}.", id);
        return Results.Problem(
            title: "Failed to retrieve SIP connection",
            statusCode: StatusCodes.Status502BadGateway);
    }
});

// POST /webhooks/telnyx — receive + Ed25519-verify an inbound Telnyx webhook.
app.MapPost("/webhooks/telnyx", async (HttpRequest req) =>
{
    // Read the RAW body BEFORE any model binding / JSON parsing — re-serialized
    // bodies break the Ed25519 signature.
    using var reader = new StreamReader(req.Body);
    string rawBody = await reader.ReadToEndAsync();

    string signature = req.Headers["telnyx-signature-ed25519"].ToString();
    string timestamp = req.Headers["telnyx-timestamp"].ToString();
    string? publicKey = Environment.GetEnvironmentVariable("TELNYX_PUBLIC_KEY");

    if (string.IsNullOrWhiteSpace(publicKey))
    {
        logger.LogError("TELNYX_PUBLIC_KEY is not set; cannot verify webhook signatures.");
        return Results.StatusCode(StatusCodes.Status500InternalServerError);
    }

    try
    {
        TelnyxWebhook<object> evt =
            Telnyx.net.Infrastructure.Public.Webhook.ConstructEvent(
                rawBody, signature, timestamp, publicKey);

        // Read event fields from data / data.payload per the repo standard.
        var eventType = evt.Data?.EventType;
        var payload = evt.Data?.Payload;
        logger.LogInformation("Verified Telnyx webhook: {EventType}", eventType);

        // TODO: act on `payload` (e.g. provisioning follow-ups) here.
        return Results.Ok();
    }
    catch (TelnyxException)
    {
        // Bad signature or stale timestamp. Do not leak detail.
        return Results.Unauthorized();
    }
});

app.Run();

// --- Helpers -----------------------------------------------------------------

// Project an SDK CredentialConnection into a safe, JSON-serializable view.
// Deliberately omits the password so it is never returned over HTTP.
static object ToView(CredentialConnection c) => new
{
    id = c.Id,
    connection_name = c.ConnectionName,
    username = c.UserName,
    active = c.Active,
    sip_uri_calling_preference = c.SipUriCallingPreference,
};

// Input DTO for POST /sip/connections.
public record CreateConnectionRequest(
    string? Name,
    string? Username,
    string? Password,
    bool? Active);
