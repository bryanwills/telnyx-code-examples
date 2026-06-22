# Guide: Activate (Enable) a Telnyx SIM Card in C# / .NET

This walkthrough builds a small ASP.NET (net8.0) service that enables a Telnyx SIM card
and safely receives Telnyx webhooks. It uses the official `Telnyx.net` SDK and minimal
APIs — no controllers, no DI ceremony.

## Prerequisites

- .NET 8 SDK
- A Telnyx account and API key ([Portal → API Keys](https://portal.telnyx.com/app/api-keys))
- At least one registered SIM card and its id

## 1. Create the project files

The project targets `net8.0` with `Microsoft.NET.Sdk.Web` and pins two packages.

```xml
<Project Sdk="Microsoft.NET.Sdk.Web">

  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
    <RootNamespace>ActivateSimCard</RootNamespace>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="Telnyx.net" Version="3.1.0" />
    <PackageReference Include="DotNetEnv" Version="3.1.0" />
  </ItemGroup>

</Project>
```

> The NuGet package id is **`Telnyx.net`**, not `Telnyx`. Version `3.1.0` is the closest
> published 3.x release.

## 2. Configure the SDK

The Telnyx .NET SDK uses **static** configuration. There is no `new TelnyxClient(...)`;
you set the key once, then instantiate per-resource service classes.

```csharp
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

TelnyxConfiguration.SetApiKey(apiKey);

var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();
```

Credentials are loaded from the environment via `DotNetEnv`. Never hardcode keys.

## 3. Enable a SIM card

`SimCardsService.EnableAsync(id)` issues `POST /sim_cards/{id}/actions/enable` and returns
a `SimCardRecord`. `Enable(string id)` takes only the SIM id — there is no options object.

```csharp
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
```

Note the error handling: every SDK call throws a single `Telnyx.TelnyxException`. We log
the detail server-side and return a generic problem response so no exception text leaks to
the HTTP client. (The synchronous variant is `sim.Enable(id)`; this example uses the async
form.)

## 4. Receive webhooks safely (Ed25519)

Telnyx signs webhooks with Ed25519. The signed string is `"{timestamp}|{raw body}"`, so you
**must read the raw body before any JSON parsing** — a re-serialized body breaks the
signature. The SDK helper `Webhook.ConstructEvent` does the base64 decode, message rebuild,
Ed25519 verification, and 300s timestamp tolerance check for you.

```csharp
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
        TelnyxWebhook<object> evt =
            Telnyx.net.Infrastructure.Public.Webhook.ConstructEvent(rawBody, signature, timestamp, publicKey);

        var eventType = evt.Data?.EventType;
        logger.LogInformation("Verified Telnyx webhook: {EventType}", eventType);

        return Results.Ok(new { received = true, event_type = eventType });
    }
    catch (TelnyxException)
    {
        return Results.Unauthorized();
    }
});
```

After verification, read event fields from `evt.Data` — `EventType`, `Id`, `OccurredAt`,
`RecordType`, and `Payload` (the `data.payload` object). For a typed payload, use
`TelnyxWebhook<MyPayloadType>`.

## 5. Run it

```bash
cp .env.example .env     # fill in TELNYX_API_KEY (and TELNYX_PUBLIC_KEY for webhooks)
dotnet restore
dotnet run
```

Then enable a SIM:

```bash
curl -X POST http://localhost:5000/sim-cards/<your-sim-id>/enable
```

```json
{
  "id": "<your-sim-id>",
  "status": "enabling",
  "message": "SIM card enable requested."
}
```

## Where to go next

- Disable a SIM with `sim.DisableAsync(id)` — the mirror of enable.
- Register freshly purchased SIMs with
  `sim.Register(new SimCardRegisterOptions { RegistrationCodes = [...], SimCardGroupId = ... })`.
- See [`API.md`](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/activate-sim-card-csharp/API.md) for the full route/response reference.
