# API Reference — Warm Transfer with AI Briefing

Base URL: `http://localhost:5000`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/webhooks/voice` | Receives Telnyx Call Control webhook events. Called automatically by Telnyx during calls — do not call directly. |
| `POST` | `/transfers/initiate` | Initiate transfer. |
| `GET` | `/transfers` | List transfers. |
| `GET` | `/calls` | List calls. |
| `GET` | `/health` | Health check and service status. |

---

## `POST /webhooks/voice`

Receives Telnyx Call Control webhook events. Called automatically by Telnyx during calls — do not call directly.

### Events Handled

| Event | Action |
|-------|--------|
| `call.initiated` | Call setup started |
| `call.answered` | Begins interaction (TTS greeting or gather) |
| `call.gather.ended` | Input received — processes customer response |
| `call.hangup` | Call ended — cleans up session state |

### DTMF Options

| Key | Action |
|-----|--------|
| `1` | Connected |
| `2` | Transfer declined. The caller will be returned to the queue. |

---

## `POST /transfers/initiate`

Initiate transfer.

### Request

```json
{
  "error": "invalid request body"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `call_id` | `string` | **yes** | Call id |
| `next_agent` | `string` | **yes** | Next agent |
| `reason` | `string` | no | Reason |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

---

## `GET /transfers`

List all transfers.

### Response `200`

```json
{"transfers": [{
        "id": null, "status": t["status"], "briefing": t["briefing"],
    }
```

---

## `GET /calls`

List all calls.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "active_calls": "example-value",
  "pending_transfers": "example-value"
}
```

---

## Status Values

Records use these status values: `active`, `answered`, `answering`, `briefing_agent`, `connected`, `declined`, `dialing`, `ended`, `gathered`, `hangup`, `ok`, `transfer_decision`

## Error Handling

All endpoints return JSON. On error:

```json
{"error": "Description of what went wrong"}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
