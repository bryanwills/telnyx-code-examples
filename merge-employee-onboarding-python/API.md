# API Reference -- Merge Employee Onboarding

Base URL: `http://localhost:5000`

## All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/webhooks/hris` | Hris |
| `POST` | `/onboard` | Onboard |
| `GET` | `/onboardings` | Onboardings |
| `GET` | `/health` | Health |

---

## `POST /webhooks/hris`

Telnyx webhook handler.

### Events Handled

| Event | Description |
|-------|-------------|

### Response `200`

```json
{"status": "ok"}
```

---

## `POST /onboard`

Onboard.

### Request

```json
{"example": "value"}
```

### Response `200`

```json
{"status": "ok"}
```

### Try it

```bash
curl -X POST http://localhost:5000/onboard \
  -H "Content-Type: application/json" \
  -d '{"example": "value"}'
```

---

## `GET /onboardings`

Onboardings.

### Response `200`

```json
{"status": "ok"}
```

### Try it

```bash
curl http://localhost:5000/onboardings
```

---

## `GET /health`

Health.

### Response `200`

```json
{"status": "ok"}
```

### Try it

```bash
curl http://localhost:5000/health
```

---

## Error Handling

```json
{"error": "Description of what went wrong"}
```

| Status | Meaning |
|--------|--------|
| `200` | Success |
| `400` | Bad request |
| `404` | Not found |
| `500` | Server error |
