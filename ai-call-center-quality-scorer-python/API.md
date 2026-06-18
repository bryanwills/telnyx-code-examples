# API Reference — AI Call Center Quality Scorer

Base URL: `http://localhost:5000`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/score` | Score call. |
| `POST` | `/score/batch` | Batch score. |
| `GET` | `/scorecards` | List scorecards. |
| `GET` | `/scorecards/summary` | Summary. |
| `GET` | `/health` | Health check and service status. |

---

## `POST /score`

Score call.

### Request

```json
{
  "error": "invalid request body"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `transcript` | `string` | no | Transcript |
| `call_id` | `string` | no | Call id |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

---

## `POST /score/batch`

Batch score.

### Request

```json
{
  "transcripts": []
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `transcripts` | `array` | no | Transcripts |

### Response `200`

```json
{"results": null}
```

---

## `GET /scorecards`

List all scorecards.

### Response `200`

```json
{"scorecards": scorecards[-50:]}
```

---

## `GET /scorecards/summary`

Summary.

### Response `200`

```json
{
  "message": "No scorecards yet"
}
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "scorecards": "<string>"
}
```

---

## Error Handling

All endpoints return JSON. On error:

```json
{
  "error": "invalid request body"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
