# API Reference -- Edge Webhook Aggregator

Base URL: `http://localhost:5000`

## All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/webhooks/ingest` | Ingest |
| `POST` | `/tenants` | Tenants |
| `GET` | `/tenants` | Tenants |
| `GET` | `/stats` | Stats |
| `GET` | `/health` | Health |

---

## `POST /webhooks/ingest`

Telnyx webhook handler.

### Events Handled

| Event | Description |
|-------|-------------|

### Response `200`

```json
{"status": "ok"}
```

---

## `POST /tenants`

Tenants.

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
curl -X POST http://localhost:5000/tenants \
  -H "Content-Type: application/json" \
  -d '{"example": "value"}'
```

---

## `GET /tenants`

Tenants.

### Response `200`

```json
{"status": "ok"}
```

### Try it

```bash
curl http://localhost:5000/tenants
```

---

## `GET /stats`

Stats.

### Response `200`

```json
{"status": "ok"}
```

### Try it

```bash
curl http://localhost:5000/stats
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
