# API Reference — Smart Number Geo-Assignment

Base URL: `http://localhost:5000`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/assign` | Assign number. |
| `POST` | `/lookup-and-assign` | Lookup and assign. |
| `GET` | `/inventory` | Inventory. |
| `GET` | `/assignments` | List assignments. |
| `GET` | `/health` | Health check and service status. |

---

## `POST /assign`

Assign number.

### Request

```json
{
  "error": "invalid request body"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `area_code` | `string` | **yes** | Area code |
| `use_case` | `string` | no | Use case |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

---

## `POST /lookup-and-assign`

Lookup and assign.

### Request

```json
{
  "error": "invalid request body"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `target_number` | `string` | no | Target number |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

---

## `GET /inventory`

Inventory.

### Response `200`

```json
{
  "numbers": "example-value",
  "total": 3
}
```

---

## `GET /assignments`

List all assignments.

### Response `200`

```json
{"assignments": assignments[-50:]}
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "assignments": "example-value"
}
```

---

## Error Handling

All endpoints return JSON. On error:

```json
{
  "status": "ok",
  "cached_numbers": "example-value"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
