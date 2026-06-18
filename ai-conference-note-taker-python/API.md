# API Reference — AI Conference Note-Taker

Base URL: `http://localhost:5000`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/join` | Join meeting. |
| `POST` | `/webhooks/voice` | Receives Telnyx Call Control webhook events. Called automatically by Telnyx during calls — do not call directly. |
| `GET` | `/meetings` | List meetings. |
| `GET` | `/health` | Health check and service status. |

---

## `POST /join`

Join meeting.

### Request

```json
{
  "error": "invalid request body"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `dial_number` | `string` | **yes** | Dial number |
| `participants` | `array` | no | List of participant phone numbers |
| `call_control_id` | `string` | **yes** | Call control id |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

---

## `POST /webhooks/voice`

Receives Telnyx Call Control webhook events. Called automatically by Telnyx during calls — do not call directly.

---

## `GET /meetings`

List all meetings.

### Response `200`

```json
{
  "error": "No payload"
}
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "active_meetings": "example-value",
  "completed": "example-value"
}
```

---

## Status Values

Records use these status values: `event_received`, `joining`, `meeting_ended`, `ok`, `recording`, `transcribing`

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
