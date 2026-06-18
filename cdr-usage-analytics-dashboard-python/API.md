# API Reference — CDR Usage Analytics Dashboard

Base URL: `http://localhost:5000`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/cdrs` | Get cdrs. |
| `GET` | `/analytics/summary` | Usage summary. |
| `GET` | `/analytics/peak-hours` | Peak hours. |
| `GET` | `/analytics/top-routes` | Top routes. |
| `GET` | `/analytics/ai-insights` | Ai insights. |
| `GET` | `/analytics/daily` | Daily breakdown. |
| `GET` | `/health` | Health check and service status. |

---

## `GET /cdrs`

Get a specific cdrs by ID.

### Response `200`

```json
{"data": "<string>", "period": {"start": null, "end": null}
```

---

## `GET /analytics/summary`

Usage summary.

### Response `200`

```json
{"period": {"start": null, "end": null}
```

---

## `GET /analytics/peak-hours`

Peak hours.

### Response `200`

```json
{
  "id": "abc-123",
  "status": "active",
  "created_at": "2026-06-18T21:00:00Z"
}
```

---

## `GET /analytics/top-routes`

Top routes.

### Response `200`

```json
{
  "id": "abc-123",
  "status": "active",
  "created_at": "2026-06-18T21:00:00Z"
}
```

---

## `GET /analytics/ai-insights`

Ai insights.

### Response `200`

```json
{
  "insights": "No data for analysis"
}
```

---

## `GET /analytics/daily`

Daily breakdown.

### Response `200`

```json
{"daily": null}
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok"
}
```

---

## Error Handling

All endpoints return JSON. On error:

```json
{
  "insights": "No data for analysis"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
