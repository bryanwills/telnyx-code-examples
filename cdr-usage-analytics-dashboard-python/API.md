## `GET /cdrs`

Get a specific cdrs by ID.

### Response `200`

```json
{"data": "<string>", "period": {"start": null, "end": null}
```

**Try it:**

```bash
curl http://localhost:5000/cdrs
```

---

## `GET /analytics/summary`

Usage summary.

### Response `200`

```json
{"period": {"start": null, "end": null}
```

**Try it:**

```bash
curl http://localhost:5000/analytics/summary
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

**Try it:**

```bash
curl http://localhost:5000/analytics/peak-hours
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

**Try it:**

```bash
curl http://localhost:5000/analytics/top-routes
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

**Try it:**

```bash
curl http://localhost:5000/analytics/ai-insights
```

---

## `GET /analytics/daily`

Daily breakdown.

### Response `200`

```json
{"daily": null}
```

**Try it:**

```bash
curl http://localhost:5000/analytics/daily
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

**Try it:**

```bash
curl http://localhost:5000/health
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
