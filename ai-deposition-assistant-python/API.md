# API Reference — AI Deposition Assistant

Base URL: `http://localhost:5000`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/depositions/start` | Start deposition. |
| `POST` | `/webhooks/voice` | Receives Telnyx Call Control webhook events. Called automatically by Telnyx during calls — do not call directly. |
| `GET` | `/depositions/<did>` | Get deposition. |
| `GET` | `/depositions/<did>/transcript` | Get dep transcript. |
| `GET` | `/depositions` | List depositions. |
| `GET` | `/health` | Health check and service status. |

---

## `POST /depositions/start`

Start deposition.

### Request

```json
{
  "error": "invalid request body"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `case_name` | `string` | no | Case name |
| `deponent` | `string` | no | Deponent |
| `participants` | `array` | no | List of participant phone numbers |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

---

## `POST /webhooks/voice`

Receives Telnyx Call Control webhook events. Called automatically by Telnyx during calls — do not call directly.

### Events Handled

| Event | Action |
|-------|--------|
| `call.answered` | Begins interaction (TTS greeting or gather) |
| `call.speak.ended` | TTS finished — transitions to gather or next step |
| `call.gather.ended` | Input received — processes customer response |
| `call.hangup` | Call ended — cleans up session state |

---

## `GET /depositions/<did>`

Get a specific deposition by ID.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

---

## `GET /depositions/<did>/transcript`

Get dep transcript.

### Response `200`

```json
{
  "error": "not found"
}
```

---

## `GET /depositions`

List all depositions.

### Response `200`

```json
{"depositions": [{
        "id": d["id"], "case": d["case"], "status": d["status"],
        "lines": "<string>",
    }
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "error": "not found"
}
```

---

## Status Values

Records use these status values: `completed`, `dialing`, `joined`, `left`, `listening`, `no_deposition`, `ok`, `on_record`, `starting`, `transcribed`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "status": "ok",
  "active_depositions": "example-value",
  "total": 3
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
