## `POST /appointments`

Add appointment.

### Request

```json
{
  "phone": "+12125559999",
  "datetime": "datetime-value"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `phone` | `string` | **yes** | Phone number in E.164 format (e.g., `+12125551234`) |
| `datetime` | `string` | no | Datetime |

### Response `200`

```json
{
  "status": "scheduled"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/appointments \
  -H "Content-Type: application/json" \
  -d '{"phone": "+12125559999", "datetime": "datetime-value"}'
```

---

## `POST /predict`

Run predictions.

### Response `200`

```json
{"predictions": null}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{"predictions": null}'
```

---

## `POST /webhooks/messaging`

Receives Telnyx Messaging webhook events. Called automatically by Telnyx for inbound messages — do not call directly.

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/messaging
```

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "patients": "<string>"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `confirmed`, `handled`, `ignored`, `ok`, `scheduled`, `unknown_patient`

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
