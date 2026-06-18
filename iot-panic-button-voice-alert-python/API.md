## `POST /alert`

Trigger a new alert.

### Request

```json
{
  "error": "invalid request body"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `device_id` | `string` | **yes** | Device identifier |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/alert \
  -H "Content-Type: application/json" \
  -d '{"error": "invalid request body"}'
```

---

## `POST /webhooks/voice`

Receives Telnyx Call Control webhook events. Called automatically by Telnyx during calls — do not call directly.

### DTMF Options

| Key | Action |
|-----|--------|
| `1` | Alert acknowledged. Dispatch team notified. Stay safe. |
| `2` | Escalating to emergency services. Please stay on the line. |

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/voice
```

## `POST /devices`

Register device.

### Request

```json
{
  "error": "invalid request body"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `device_id` | `string` | no | Device identifier |
| `name` | `string` | **yes** | Display name or label |
| `location` | `string` | **yes** | Location |
| `contacts` | `array` | no | Contacts |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/devices \
  -H "Content-Type: application/json" \
  -d '{"error": "invalid request body"}'
```

---

## `GET /alerts`

List all alerts.

### Response `200`

```json
{"alerts": alerts[-50:]}
```

**Try it:**

```bash
curl http://localhost:5000/alerts
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `acknowledged`, `active`, `alerting`, `calling`, `ended`, `failed`, `listening`, `ok`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "alerts": "example-value"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
