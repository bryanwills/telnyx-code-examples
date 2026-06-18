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

**Try it:**

```bash
curl -X POST http://localhost:5000/assign \
  -H "Content-Type: application/json" \
  -d '{"error": "invalid request body"}'
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

**Try it:**

```bash
curl -X POST http://localhost:5000/lookup-and-assign \
  -H "Content-Type: application/json" \
  -d '{"error": "invalid request body"}'
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

**Try it:**

```bash
curl http://localhost:5000/inventory
```

---

## `GET /assignments`

List all assignments.

### Response `200`

```json
{"assignments": assignments[-50:]}
```

**Try it:**

```bash
curl http://localhost:5000/assignments
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
  "cached_numbers": "example-value"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
