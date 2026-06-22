# Set Up a SIP Trunk with Telnyx and C# (.NET)

Create, list, and retrieve credential-authenticated SIP connections using the official Telnyx.net SDK and a minimal ASP.NET (net8.0) app.

## How It Works

```
  HTTP Request
        │
        ▼
  ┌───────────────────────────┐
  │  Minimal ASP.NET Program.cs│
  │  /sip/connections          │
  └────────────┬──────────────┘
               │ Telnyx.net SDK
               │ (CredentialConnectionService)
               ▼
  ┌───────────────────────────┐
  │  Telnyx SIP Trunking       │
  │  /credential_connections   │
  └───────────────────────────┘
```

## Telnyx Products Used

- **SIP Trunking** — provision credential-authenticated SIP connections that route calls over the Telnyx private network.

## API Endpoints

- **Create credential connection**: `POST /v2/credential_connections`
- **List credential connections**: `GET /v2/credential_connections`
- **Retrieve credential connection**: `GET /v2/credential_connections/{id}`

## Prerequisites

- .NET 8 SDK
- [Telnyx account](https://portal.telnyx.com/sign-up)
- [API key](https://portal.telnyx.com/api-keys)
- For webhook verification: your account's base64 Ed25519 public key (Portal > Account > Public Key)

## Step 1: Set Up the Project

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/setup-sip-trunk-csharp
cp .env.example .env
dotnet restore
```

Edit `.env` and set `TELNYX_API_KEY` (and `TELNYX_PUBLIC_KEY` if you will receive webhooks).

## Step 2: Understand the Code

Everything lives in `Program.cs` using top-level statements (no controllers).

### Configure the SDK statically

The Telnyx.net SDK uses a static configuration — there is no client object. The key is read from the environment after `DotNetEnv` loads `.env`:

```csharp
DotNetEnv.Env.Load();
TelnyxConfiguration.SetApiKey(Environment.GetEnvironmentVariable("TELNYX_API_KEY"));
```

### Create a credential connection

```csharp
var svc = new CredentialConnectionService();
var options = new UpsertCredentialConnectionOptions
{
    ConnectionName = body.Name,   // inherited from UpsertConnectionOptions
    UserName = body.Username,
    Password = body.Password,
    Active = body.Active ?? true,
};

CredentialConnection created = await svc.CreateCredentialConnectionAsync(options);
```

`CredentialConnection` exposes `.Id`, `.ConnectionName`, `.UserName`, `.Active`, and `.SipUriCallingPreference`. The app projects these into a view object and never returns the password.

### List connections

`ListCredentialConnectionAsync` takes `ConnectionListOptions` (which maps to `page[number]` / `page[size]`) and returns a `TelnyxList<CredentialConnection>` that implements `IEnumerable<T>`:

```csharp
var listOptions = new ConnectionListOptions { PageNumber = 1, PageSize = 20 };
TelnyxList<CredentialConnection> list = await svc.ListCredentialConnectionAsync(listOptions);
var items = list.Select(ToView).ToList();
```

### Retrieve one connection

```csharp
CredentialConnection one = await svc.RetrieveCredentialConnectionAsync(id);
```

### Error handling

Every SDK call throws a single `Telnyx.TelnyxException`. The detail is logged server-side; callers receive a generic message so exception details never leak:

```csharp
catch (TelnyxException ex)
{
    logger.LogError(ex, "Telnyx API error while creating credential connection.");
    return Results.Problem(
        title: "Failed to create SIP connection",
        statusCode: StatusCodes.Status502BadGateway);
}
```

### Verify inbound webhooks

The webhook route reads the **raw** body before any parsing, then verifies the Telnyx Ed25519 signature with the SDK helper. Event data is read from `data.payload`:

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

    var eventType = evt.Data?.EventType;
    var payload = evt.Data?.Payload;   // the data.payload object
    return Results.Ok();
}
catch (TelnyxException)
{
    return Results.Unauthorized();     // bad signature or stale timestamp
}
```

`ConstructEvent` recomputes the signed message as `"{telnyx-timestamp}|{raw body}"`, Ed25519-verifies it against your base64 public key, and enforces a 300-second timestamp tolerance.

## Step 3: Run It

```bash
dotnet run
```

The startup log prints the listening address (typically `http://localhost:5000`).

## Step 4: Test It

**Create a connection:**

```bash
curl -X POST http://localhost:5000/sip/connections \
  -H "Content-Type: application/json" \
  -d '{
    "name": "office-pbx",
    "username": "myuser12345",
    "password": "mySecret1234567",
    "active": true
  }'
```

**Retrieve it** (use the `id` from the create response):

```bash
curl http://localhost:5000/sip/connections/1293384261075731499
```

**List all connections:**

```bash
curl "http://localhost:5000/sip/connections?page=1&pageSize=20"
```

## Going to Production

- **Authentication** — the management routes are unauthenticated as written; add API key or token validation on your own endpoints.
- **Secrets** — keep `TELNYX_API_KEY`, `TELNYX_PUBLIC_KEY`, and SIP credentials out of source control; load them from a secrets manager.
- **Webhook proxy** — ensure any reverse proxy forwards the raw request body unmodified, or signature verification will fail.
- **Monitoring** — add structured logging and health checks around the connection lifecycle.
- **Rate limiting** — protect your endpoints and respect Telnyx API limits with backoff.

## Resources

- [Source code and reference](./README.md)
- [Typed endpoint reference](./API.md)
- [SIP Trunking Get Started](https://developers.telnyx.com/docs/voice/sip-trunking/get-started)
- [.NET SDK](https://developers.telnyx.com/development/sdk/dotnet)
- [Telnyx Portal](https://portal.telnyx.com)
