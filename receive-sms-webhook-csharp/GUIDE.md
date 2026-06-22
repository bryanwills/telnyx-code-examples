# Receive Your First Inbound SMS with Telnyx and ASP.NET (C#)

Build a minimal ASP.NET (net8.0) server that receives inbound SMS messages via
Telnyx webhooks and verifies the Telnyx Ed25519 signature before trusting any payload.

## How It Works

```
  Inbound SMS
        │
        ▼
  ┌──────────────────┐
  │  Telnyx Messaging │
  └────────┬─────────┘
           │ POST webhook (signed Ed25519)
           ▼
  ┌──────────────────────────┐
  │  ASP.NET minimal API      │
  │  POST /webhooks/sms        │
  └────────┬─────────────────┘
           │
           └─► verify signature → read data.payload → store → 200 OK
```

## Telnyx Products Used

- **Messaging** — send and receive messages with delivery receipts

## API Endpoints

- **Inbound Message webhook**: `POST /webhooks/sms` (your endpoint, called by Telnyx) — [Webhook reference](https://developers.telnyx.com/docs/messaging/messages/receive-message)

## Prerequisites

- [.NET 8 SDK](https://dotnet.microsoft.com/download)
- [Telnyx account](https://portal.telnyx.com/sign-up)
- [API key](https://portal.telnyx.com/api-keys)
- Your base64 [account public key](https://portal.telnyx.com) (Account → Public Key)
- [Phone number](https://portal.telnyx.com/numbers/my-numbers) enabled for inbound SMS
- A [Messaging Profile](https://portal.telnyx.com/messaging/profiles) with an inbound webhook URL
- [ngrok](https://ngrok.com) to expose your local server to Telnyx webhooks

## Step 1: Set Up the Project

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/receive-sms-webhook-csharp
cp .env.example .env
dotnet restore
```

Edit `.env` with your credentials. `TELNYX_API_KEY` configures the SDK and
`TELNYX_PUBLIC_KEY` (the base64 account public key) is required to verify the
Ed25519 signature on every inbound webhook.

The project file pins the dependencies:

```xml
<ItemGroup>
  <PackageReference Include="Telnyx.net" Version="3.1.0" />
  <PackageReference Include="DotNetEnv" Version="3.1.0" />
</ItemGroup>
```

> Note: the NuGet package id is `Telnyx.net` (not `Telnyx`). 3.1.0 is the closest
> published 3.x release.

## Step 2: Understand the Code

Everything lives in `Program.cs` (top-level statements, minimal API).

### Read the raw body and verify the signature

Telnyx signs `"<telnyx-timestamp>|<raw body>"`. You must read the **raw** request
body before any parsing — re-serializing the JSON would change the bytes and break
verification. The SDK helper `Webhook.ConstructEvent` Ed25519-verifies the signature
and enforces a timestamp tolerance, throwing `Telnyx.TelnyxException` on failure.

```csharp
string rawBody;
using (var reader = new StreamReader(req.Body))
{
    rawBody = await reader.ReadToEndAsync();
}

string signature = req.Headers["telnyx-signature-ed25519"].ToString();
string timestamp = req.Headers["telnyx-timestamp"].ToString();

TelnyxWebhook<object> evt;
try
{
    evt = Telnyx.net.Infrastructure.Public.Webhook.ConstructEvent(
        rawBody, signature, timestamp, publicKey);
}
catch (Telnyx.TelnyxException ex)
{
    logger.LogWarning(ex, "Webhook signature verification failed.");
    return Results.Unauthorized();
}
```

`publicKey` is read once from the environment:

```csharp
var publicKey = Environment.GetEnvironmentVariable("TELNYX_PUBLIC_KEY");
```

If it is missing, the handler returns `503` and never trusts the request.

### Read fields from data.payload

Only `message.received` carries an inbound SMS. Fields are nested under
`data.payload`; this example parses the verified raw body with `System.Text.Json`
and pulls them out safely:

```csharp
var eventType = evt.Data?.EventType;
if (eventType != "message.received")
{
    return Results.Ok(new { status = "ignored" });
}

using var doc = JsonDocument.Parse(rawBody);
if (!doc.RootElement.TryGetProperty("data", out var data) ||
    !data.TryGetProperty("payload", out var payload))
{
    return Results.BadRequest(new { error = "Invalid webhook payload structure" });
}

var message = new InboundMessage
{
    MessageId = GetString(payload, "id"),
    From = GetPhoneNumber(payload, "from"),       // data.payload.from.phone_number
    To = GetFirstToPhoneNumber(payload),          // data.payload.to[0].phone_number
    Text = GetString(payload, "text") ?? string.Empty,
    ReceivedAt = GetString(payload, "received_at") ?? DateTime.UtcNow.ToString("o"),
    Direction = GetString(payload, "direction") ?? "inbound",
};
```

### Acknowledge fast

Telnyx requires a 2xx response within 5 seconds or it retries:

```csharp
return Results.Ok(new
{
    success = true,
    message_id = message.MessageId,
    status = "received",
});
```

### All endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/webhooks/sms` | Receive and verify inbound SMS events from Telnyx |
| `GET` | `/messages` | View stored messages (debug; remove in production) |
| `GET` | `/health` | Liveness check |

## Step 3: Run It

```bash
dotnet run
```

The server starts on `http://localhost:5000`.

In a separate terminal, expose it for webhooks:

```bash
ngrok http 5000
```

Copy the HTTPS URL and set it in the [Telnyx Portal](https://portal.telnyx.com):

- **Messaging Profile** → Inbound Settings → Webhook URL → `https://<id>.ngrok.io/webhooks/sms`

Then assign your inbound-enabled number to that Messaging Profile.

## Step 4: Test It

**Health check:**

```bash
curl http://localhost:5000/health
```

**Real inbound SMS:** text your Telnyx number from a phone and watch the server logs
print the inbound message. Because every webhook must carry a valid Ed25519 signature,
the most reliable test is a real (or Portal-simulated) Telnyx event — a hand-rolled
`curl` without `telnyx-signature-ed25519` and `telnyx-timestamp` headers correctly
returns `401`.

**View what was received:**

```bash
curl http://localhost:5000/messages
```

## Going to Production

- **Database** — replace the in-memory list with PostgreSQL or Redis.
- **Background processing** — acknowledge `200` immediately and move heavy work to a queue to stay under the 5-second window.
- **Keep verification on** — never disable Ed25519 verification; rotate the public key from the Portal if needed.
- **Lock down debug routes** — remove or authenticate `/messages`.
- **Monitoring** — add structured logging and health-check alerts.

## Resources

- [Source and reference](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/receive-sms-webhook-csharp/README.md)
- [Typed API reference](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/receive-sms-webhook-csharp/API.md)
- [Receive a Message guide](https://developers.telnyx.com/docs/messaging/messages/receive-message)
- [Webhook signing overview](https://developers.telnyx.com/docs/messaging/webhooks)
- [.NET SDK](https://developers.telnyx.com/development/sdk/dotnet)
- [Telnyx Portal](https://portal.telnyx.com)
