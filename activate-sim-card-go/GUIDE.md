# Activate a Telnyx SIM Card with Go

Activate a Telnyx IoT SIM card over HTTP using the Telnyx Go SDK and Gin.

## How It Works

```
  POST /sim/activate
        │
        ▼
  ┌──────────────────┐
  │   Gin handler     │
  │  (validate body)  │
  └────────┬─────────┘
           │ client.SimCards.Activate(id)
           ▼
  ┌──────────────────┐
  │  Telnyx IoT SIM   │
  └────────┬─────────┘
           │
           └──► SIM card transitions to "enabling"
```

## Telnyx Products Used

- **IoT SIM** — provision and activate cellular SIM cards over the API

## API Endpoints

- **Activate SIM Card**: `POST /v2/sim_cards/{id}/actions/enable` -- [API reference](https://developers.telnyx.com/api-reference/sim-cards/enable-sim-card)

## Prerequisites

- Go 1.22+
- [Telnyx account](https://portal.telnyx.com/sign-up)
- [API key](https://portal.telnyx.com/api-keys)
- At least one SIM card in your Telnyx account in `ready` or `standby` status (IoT → SIM Cards)
- The SIM card ID (UUID), found in the [Telnyx Portal](https://portal.telnyx.com) under IoT → SIM Cards

## Step 1: Set Up the Project

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/activate-sim-card-go
cp .env.example .env
go mod download
```

Edit `.env` and set `TELNYX_API_KEY` to the key shown in the [Telnyx Portal](https://portal.telnyx.com/api-keys).

## Step 2: Understand the Code

Everything lives in `main.go`. Here's what each piece does.

### Client Initialization

`init()` loads `.env` with `godotenv.Load()`, reads `TELNYX_API_KEY`, panics if it is missing, and creates the SDK client:

```go
client = telnyx.NewClient(telnyx.WithAPIKey(apiKey))
```

### Helper Function

- **`activateSIM(simCardID string)`** — Validates the ID is non-empty, calls `client.SimCards.Activate(simCardID, nil)`, and unpacks the SDK response into a plain `map[string]interface{}` with `id`, `iccid`, `status`, and `sim_card_group_id`.

### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/sim/activate` | Activate a SIM card by ID |

The handler binds the JSON body (requiring `sim_card_id`), calls the helper, and maps SDK errors to HTTP statuses:

```go
router.POST("/sim/activate", func(c *gin.Context) {
    var request struct {
        SimCardID string `json:"sim_card_id" binding:"required"`
    }

    if err := c.ShouldBindJSON(&request); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{
            "error": "Missing required field: 'sim_card_id'",
        })
        return
    }

    result, err := activateSIM(request.SimCardID)
    // ... error switch on AuthenticationError, RateLimitError,
    //     APIStatusError, APIConnectionError ...
    c.JSON(http.StatusOK, result)
})
```

Authentication errors return `401`, rate limits `429`, connection errors `503`, and other API errors echo their upstream status code.

## Step 3: Run It

```bash
go run .
```

The server starts on `http://localhost:8080`.

## Step 4: Test It

Activate a SIM card (replace the ID with one from your account):

```bash
curl -X POST http://localhost:8080/sim/activate \
  -H "Content-Type: application/json" \
  -d '{
    "sim_card_id": "6b14e151-8493-4fa1-8664-1cc4e6d14158"
  }'
```

You should get back the SIM's `id`, `iccid`, `status` (e.g. `enabling`), and `sim_card_group_id`.

## Going to Production

- **Authentication** — add API key validation on your endpoints before exposing them.
- **Structured logging** — replace Gin's default logging with structured logs and request IDs.
- **Retries** — add bounded retries with backoff for `503`/`429` responses from Telnyx.
- **Monitoring** — alert on activation failures and track SIM status transitions via webhooks.

## Run

```bash
go mod download
go run .
```

## Resources

- [Source code and reference](./README.md)
- [Typed API reference](./API.md)
- [IoT SIM Get Started](https://developers.telnyx.com/docs/iot-sim/get-started)
- [Go SDK](https://developers.telnyx.com/development/sdk/go)
- [Telnyx Portal](https://portal.telnyx.com)
</content>
