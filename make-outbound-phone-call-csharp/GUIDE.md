# Make Your First Outbound Call with Telnyx and C#

Place an outbound phone call with the Telnyx Call Control API. This guide walks through a minimal ASP.NET app that exposes a single endpoint, dials a number through the official Telnyx .NET SDK, and returns the call control ID. It also adds a signature-verified webhook receiver for call lifecycle events.

## How It Works

```
  POST /calls/dial
        │
        ▼
  ┌──────────────────────────┐
  │  ASP.NET minimal API       │
  │  CallControlService.Dial   │
  └────────────┬─────────────┘
               │  POST /v2/calls (Telnyx.net SDK)
               ▼
  ┌──────────────────────────┐
  │  Telnyx Voice              │
  │  (Call Control)            │
  └────────────┬─────────────┘
               │
               └──► Outbound call placed → call_control_id returned
```

## Telnyx Products Used

- **Voice (Call Control)** — programmatically dial outbound calls and control them via a Call Control Application

## API Endpoints

- **Dial**: `POST /v2/calls` — [API reference](https://developers.telnyx.com/api-reference/call-commands/dial)

## Prerequisites

- The [.NET 8 SDK](https://dotnet.microsoft.com/download)
- A [Telnyx account](https://portal.telnyx.com/sign-up) with a funded balance
- An [API key](https://portal.telnyx.com/api-keys)
- A [Telnyx phone number](https://portal.telnyx.com/numbers/my-numbers) enabled for voice
- A [Call Control Application](https://portal.telnyx.com/call-control/applications) (its ID is your connection ID)

## Step 1: Set Up the Project

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/make-outbound-phone-call-csharp
cp .env.example .env
dotnet restore
```

Edit `.env` with your Telnyx credentials:

| Variable | Description |
|----------|-------------|
| `TELNYX_API_KEY` | Your Telnyx API v2 key |
| `TELNYX_PHONE_NUMBER` | The Telnyx number you dial from (E.164) |
| `TELNYX_CONNECTION_ID` | Your Call Control Application ID |
| `TELNYX_PUBLIC_KEY` | Base64 public key for verifying inbound webhooks |

## Step 2: Understand the Code

Everything lives in `Program.cs`. The Telnyx SDK uses a **global, static** API key — there is no client object to construct. Configure it once at startup, after loading `.env`:

```csharp
DotNetEnv.Env.Load();

var apiKey = Environment.GetEnvironmentVariable("TELNYX_API_KEY");
if (string.IsNullOrWhiteSpace(apiKey))
{
    throw new InvalidOperationException("TELNYX_API_KEY environment variable not set");
}
TelnyxConfiguration.SetApiKey(apiKey);
```

### Dialing the call

The `/calls/dial` endpoint validates the destination, then instantiates `CallControlService` and calls `DialAsync`. `ConnectionId` is required — it links the call to your Call Control Application. `CallControlId` is returned on the response; you never pass it in:

```csharp
var callControl = new CallControlService();
var options = new CallControlDialOptions
{
    To = request.To,                 // +E.164 or sip:user@sip.telnyx.com
    From = fromNumber,               // your Telnyx number (E.164)
    ConnectionId = connectionId,     // Call Control Application ID (required)
};

CallDialResponse response = await callControl.DialAsync(options);
```

The response is mapped to a plain JSON object:

```csharp
return Results.Ok(new
{
    call_control_id = response.CallControlId,
    call_session_id = response.CallSessionId,
    call_leg_id = response.CallLegId,
    is_alive = response.IsAlive,
    from = fromNumber,
    to = request.To,
});
```

### Error handling

Every SDK failure surfaces as a single `Telnyx.TelnyxException`. Log it server-side and return a generic status so internal detail never leaks to the caller:

```csharp
catch (TelnyxException ex)
{
    logger.LogError(ex, "Telnyx API error while dialing {To}", request.To);
    return Results.StatusCode(StatusCodes.Status502BadGateway);
}
```

### Verifying webhooks

The `/webhooks/calls` endpoint reads the **raw** body before any parsing (a re-serialized body breaks the signature), then verifies the Telnyx Ed25519 signature with the SDK helper and reads event fields from `data.payload`:

```csharp
using var reader = new StreamReader(req.Body);
string rawBody = await reader.ReadToEndAsync();

string signature = req.Headers["telnyx-signature-ed25519"].ToString();
string timestamp = req.Headers["telnyx-timestamp"].ToString();
string? publicKey = Environment.GetEnvironmentVariable("TELNYX_PUBLIC_KEY");

try
{
    TelnyxWebhook<object> evt =
        Telnyx.net.Infrastructure.Public.Webhook.ConstructEvent(
            rawBody, signature, timestamp, publicKey);

    var eventType = evt.Data.EventType;   // e.g. call.answered, call.hangup
    var payload = evt.Data.Payload;       // the data.payload object
    return Results.Ok();
}
catch (TelnyxException)
{
    return Results.Unauthorized();        // bad signature or stale timestamp
}
```

`ConstructEvent` recomputes the signed message as `"{timestamp}|{rawBody}"`, Ed25519-verifies it against your base64 public key, and enforces a 300-second timestamp tolerance.

## Step 3: Run It

```bash
dotnet run
```

The server starts on `http://localhost:5000` (or the configured port).

## Step 4: Test It

Place a call:

```bash
curl -X POST http://localhost:5000/calls/dial \
  -H "Content-Type: application/json" \
  -d '{"to": "+12125551234"}'
```

Successful response:

```json
{
  "call_control_id": "v3:abc123def456...",
  "call_session_id": "00000000-0000-0000-0000-000000000000",
  "call_leg_id": "00000000-0000-0000-0000-000000000000",
  "is_alive": true,
  "from": "+15551234567",
  "to": "+12125551234"
}
```

## Going to Production

- **Webhook handling** — register the `/webhooks/calls` URL on your Call Control Application to receive `call.answered`, `call.hangup`, and other events, and drive the rest of the call flow.
- **In-call commands** — after dialing, set `callControl.CallControlId = response.CallControlId` and call `SpeakAsync(...)`, `HangupAsync(...)`, etc.
- **Authentication** — add API key or token validation on your `/calls/dial` endpoint.
- **Monitoring** — add structured logging and alerting around dial failures.
- **Rate limiting** — protect the endpoint from abuse.

## Resources

- [Source code and reference](./README.md)
- [Typed API reference](./API.md)
- [Voice / Call Control Guide](https://developers.telnyx.com/docs/voice/programmable-voice/voice-api-commands-and-resources)
- [Dial API Reference](https://developers.telnyx.com/api-reference/call-commands/dial)
- [.NET SDK](https://developers.telnyx.com/development/sdk/dotnet)
- [Telnyx Portal](https://portal.telnyx.com)
