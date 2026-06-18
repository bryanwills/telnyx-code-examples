## `POST /missions`

Create a new mission.

### Request

```json
{
  "name": "Jane Smith",
  "description": "description-value",
  "status": "status-value",
  "tasks": []
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `string` | **yes** | Display name or label |
| `description` | `string` | **yes** | Description |
| `status` | `string` | no | Current status value |
| `tasks` | `array` | no | List of task objects |

### Response `200`

```json
{
  "error": "Error description"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/missions \
  -H "Content-Type: application/json" \
  -d '{"name": "Jane Smith", "description": "description-value", "status": "status-value", "tasks": []}'
```

---

## `GET /missions`

List all missions.

### Response `200`

```json
{
  "error": "Error description",
  "local": []
}
```

**Try it:**

```bash
curl http://localhost:5000/missions
```

---

## `GET /missions/<mission_id>`

Get a specific mission by ID.

### Response `200`

```json
{
  "error": "Error description"
}
```

**Try it:**

```bash
curl http://localhost:5000/missions/example-id
```

---

## `POST /missions/<mission_id>/tasks`

Add task.

### Request

```json
{
  "name": "Jane Smith",
  "type": "type-value",
  "config": {},
  "depends_on": []
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `string` | **yes** | Display name or label |
| `type` | `string` | no | Type |
| `config` | `object` | no | Config |
| `depends_on` | `array` | no | Depends on |

### Response `200`

```json
{
  "error": "Error description"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/missions/example-id/tasks \
  -H "Content-Type: application/json" \
  -d '{"name": "Jane Smith", "type": "type-value", "config": {}, "depends_on": []}'
```

---

## `POST /missions/<mission_id>/run`

Run mission.

### Response `200`

```json
{
  "error": "Error description"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/missions/example-id/run \
  -H "Content-Type: application/json" \
  -d '{"error": "Error description"}'
```

---

## `GET /missions/<mission_id>/runs`

List all runs.

### Response `200`

```json
{
  "error": "Error description"
}
```

**Try it:**

```bash
curl http://localhost:5000/missions/example-id/runs
```

---

## `GET /templates`

Mission templates.

### Response `200`

```json
{
  "templatess": [
    {
      "id": "abc-123",
      "status": "active",
      "created_at": "2026-06-18T21:00:00Z"
    }
  ],
  "total": 1
}
```

**Try it:**

```bash
curl http://localhost:5000/templates
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "missions": "<string>"
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
  "missions": "example-value"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
