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

**Try it:**

```bash
curl -X POST http://localhost:5000/score \
  -H "Content-Type: application/json" \
  -d '{"error": "invalid request body"}'
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

**Try it:**

```bash
curl -X POST http://localhost:5000/score/batch \
  -H "Content-Type: application/json" \
  -d '{"transcripts": []}'
```

---

## `GET /scorecards`

List all scorecards.

### Response `200`

```json
{"scorecards": scorecards[-50:]}
```

**Try it:**

```bash
curl http://localhost:5000/scorecards
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

**Try it:**

```bash
curl http://localhost:5000/scorecards/summary
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

**Try it:**

```bash
curl http://localhost:5000/health
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
