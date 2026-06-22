# Send Your First SMS with Telnyx and C#

Build a small minimal ASP.NET endpoint that sends an SMS message using the Telnyx Messaging API and the official `Telnyx.net` SDK.

## How It Works

```
  POST /sms/send
        │
        ▼
  ┌────────────────────────┐
  │ Minimal ASP.NET handler │
  │ (validate input)        │
  └───────────┬────────────┘
              │ MessagingSenderIdService.CreateAsync()
              ▼
  ┌────────────────────────┐
  │ Telnyx Messaging        │
  └───────────┬────────────┘
              │
              └──► SMS delivered
```

## Telnyx Products Used

- **Messaging** — send messages with delivery status

## API Endpoints

- **Send Message**: `POST /v2/messages` -- [API reference](https://developers.telnyx.com/api-reference/messages/send-a-message)

## Prerequisites

- .NET 8.0 SDK and the `dotnet` CLI
- [Telnyx account](https://portal.telnyx.com/sign-up) with a funded balance
- [API key](https://portal.telnyx.com/api-keys)
- [Phone number](https://portal.telnyx.com/numbers/my-numbers) with messaging enabled and a [Messaging Profile](https://portal.telnyx.com/messaging/profiles) assigned

## Step 1: Set Up the Project

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/send-sms-csharp
cp .env.example .env
dotnet restore
```

Edit `.env` and fill in your `TELNYX_API_KEY` and `TELNYX_PHONE_NUMBER` (E.164, e.g. `+15551234567`). Each value comes from the [Telnyx Portal](https://portal.telnyx.com).

The `.csproj` pins the two dependencies — note the package id is `Telnyx.net`, **not** `Telnyx`:

```xml
<ItemGroup>
  <PackageReference Include="Telnyx.net" Version="3.1.0" />
  <PackageReference Include="DotNetEnv" Version="3.1.0" />
</ItemGroup>
```

## Step 2: Understand the Code

Everything lives in `Program.cs` as top-level statements.

### Configure the SDK

The Telnyx.net SDK uses a **static/global** API key — there is no `new TelnyxClient(...)`:

```csharp
using Telnyx;
using Telnyx.net.Entities;

DotNetEnv.Env.Load();

var apiKey = Environment.GetEnvironmentVariable("TELNYX_API_KEY");
if (string.IsNullOrWhiteSpace(apiKey))
{
    Console.Error.WriteLine("FATAL: TELNYX_API_KEY is not set. Copy .env.example to .env and fill it in.");
    return;
}

TelnyxConfiguration.SetApiKey(apiKey);
```

### Send the SMS

`MessagingSenderIdService.CreateAsync` POSTs to `/messages` — the canonical send path in this SDK:

```csharp
var service = new MessagingSenderIdService();
var options = new NewMessagingSenderId
{
    From = fromNumber,       // +E.164, alphanumeric, or short code
    To = request.To,         // +E.164
    Text = request.Message,
};

MessagingSenderId message = await service.CreateAsync(options);

return Results.Ok(new
{
    message_id = message.Id,
    from = fromNumber,
    to = request.To,
});
```

### Handle errors safely

Every SDK call throws a single `Telnyx.TelnyxException`. Log the detail server-side and return a generic message — never leak exception text to the caller:

```csharp
catch (TelnyxException ex)
{
    app.Logger.LogError(ex, "Telnyx API error while sending SMS");
    return Results.Json(new { error = "Failed to send message" }, statusCode: 502);
}
```

### Verify inbound webhooks

The `POST /webhooks/sms` handler reads the **raw** body before any parsing, then verifies the Telnyx Ed25519 signature with the SDK helper:

```csharp
using var reader = new StreamReader(req.Body);
string rawBody = await reader.ReadToEndAsync();   // MUST be the raw, unparsed body

string signature = req.Headers["telnyx-signature-ed25519"].ToString();
string timestamp = req.Headers["telnyx-timestamp"].ToString();
var publicKey = Environment.GetEnvironmentVariable("TELNYX_PUBLIC_KEY");

try
{
    TelnyxWebhook<object> evt = Telnyx.net.Infrastructure.Public.Webhook.ConstructEvent(
        rawBody, signature, timestamp, publicKey);

    var eventType = evt.Data.EventType;   // e.g. "message.received"
    var payload = evt.Data.Payload;       // the data.payload object
    return Results.Ok();
}
catch (TelnyxException)
{
    return Results.Unauthorized();        // bad signature or stale timestamp
}
```

`ConstructEvent` rebuilds the signed message as `"{telnyx-timestamp}|{rawBody}"`, Ed25519-verifies it against the account public key, and enforces a 300-second timestamp tolerance.

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/sms/send` | Send a single SMS |
| `POST` | `/webhooks/sms` | Receive + verify inbound message webhooks |

## Step 3: Run It

```bash
dotnet run
```

The server starts on `http://localhost:5000` (override with `ASPNETCORE_URLS`).

## Step 4: Test It

Send a message:

```bash
curl -X POST http://localhost:5000/sms/send \
  -H "Content-Type: application/json" \
  -d '{
    "to": "+12125559999",
    "message": "Hello from Telnyx!"
  }'
```

A successful call returns:

```json
{
  "message_id": "40017f3c-bba0-4f3f-8b2c-1a8d0c1f9c11",
  "from": "+15551234567",
  "to": "+12125559999"
}
```

## Going to Production

- **Authentication** — add API key validation on your `/sms/send` endpoint
- **Input validation** — validate and normalize destination numbers beyond the `+` check
- **Retries** — handle transient `502`s from Telnyx with backoff
- **Monitoring** — the example already logs via `app.Logger`; add structured logging and health checks
- **Delivery receipts** — point a Messaging Profile webhook at `/webhooks/sms` to track final delivery status

## Resources

- [Source code and reference](./README.md)
- [Typed endpoint reference](./API.md)
- [Messaging quickstart](https://developers.telnyx.com/docs/messaging)
- [.NET / C# SDK](https://developers.telnyx.com/development/sdk/dotnet)
- [Telnyx Portal](https://portal.telnyx.com)
