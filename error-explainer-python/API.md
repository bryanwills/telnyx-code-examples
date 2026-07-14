## `POST /explain`

Submit a stack trace and get a structured root-cause diagnosis.

### Request

```json
{
  "stack_trace": "Traceback (most recent call last):\n  File \"app.py\", line 42...",
  "language": "python",
  "context": "Flask production server with gunicorn"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `stack_trace` | `string` | **yes** | The error text / stack trace (truncated to 6000 chars) |
| `language` | `string` | no | Programming language (helps tailor the fix) |
| `context` | `string` | no | Additional environment context |

### Response `200`

```json
{
  "id": "ex-1750280400",
  "root_cause": "The requests.post() call has no timeout...",
  "severity": "high",
  "confidence": 0.94,
  "likely_culprit": "app.py:42 — requests.post() call",
  "suggested_fix": "Add an explicit timeout parameter...",
  "fix_snippet": "resp = requests.post(url, timeout=15)",
  "related_errors": ["requests.exceptions.Timeout"],
  "prevention": "Always set explicit timeouts on outbound HTTP calls.",
  "generated_at": "2026-07-15T14:30:00Z",
  "language": "python"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/explain \
  -H "Content-Type: application/json" \
  -d '{"stack_trace":"KeyError: user_id","language":"python"}'
```

---

## `GET /analyses`

List all recent error analyses (most recent 50).

### Response `200`

```json
{
  "analyses": [
    {
      "id": "ex-1750280400",
      "root_cause": "Missing key in dict...",
      "severity": "medium",
      "confidence": 0.88
    }
  ]
}
```

**Try it:**

```bash
curl http://localhost:5000/analyses
```

---

## `GET /analyses/<id>`

Get a specific analysis by ID.

### Response `200`

```json
{
  "id": "ex-1750280400",
  "root_cause": "Missing key in dict...",
  "severity": "medium",
  "confidence": 0.88,
  "likely_culprit": "app.py:15 — data['user_id']",
  "suggested_fix": "Use data.get('user_id') with a default value."
}
```

### Response `404`

```json
{"error": "analysis not found"}
```

**Try it:**

```bash
curl http://localhost:5000/analyses/ex-1750280400
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "analyses": 0,
  "version": "1.0.0"
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
| `404` | Analysis not found |
| `500` | Server error |
