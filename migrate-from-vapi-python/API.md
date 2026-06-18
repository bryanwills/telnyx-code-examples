## `GET /audit/vapi`

Audit vapi.

### Response `200`

```json
{
  "error": "VAPI_API_KEY not configured. Set it to audit your Vapi agents."
}
```

**Try it:**

```bash
curl http://localhost:5000/audit/vapi
```

---

## `POST /migrate/agent`

Migrate agent.

### Request

```json
{
  "vapi_agent": {}
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `vapi_agent` | `object` | no | Vapi agent |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/migrate/agent \
  -H "Content-Type: application/json" \
  -d '{"vapi_agent": {}}'
```

---

## `GET /mapping/voices`

Voice mapping.

### Response `200`

```json
{
  "vapi_to_telnyx": "example-value",
  "note": "Telnyx also supports ElevenLabs voices via voice.provider='elevenlabs"
}
```

**Try it:**

```bash
curl http://localhost:5000/mapping/voices
```

---

## `GET /mapping/models`

Model mapping.

### Response `200`

```json
{"recommendations": {
        "gpt-4o": "meta-llama/Llama-3.3-70B-Instruct (or moonshotai/Kimi-K2.6)",
        "gpt-3.5-turbo": "meta-llama/Llama-3.1-8B-Instruct",
        "claude-3": "anthropic/claude-sonnet-4-20250514"}
```

**Try it:**

```bash
curl http://localhost:5000/mapping/models
```

---

## `GET /migration-log`

Get a specific log by ID.

### Response `200`

```json
{
  "log": "example-value"
}
```

**Try it:**

```bash
curl http://localhost:5000/migration-log
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "migrations": "<string>"
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
  "status": "ok",
  "migrations": "example-value"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
