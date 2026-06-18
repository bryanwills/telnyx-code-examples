# API Reference — Missions Workflow Orchestrator

Base URL: `http://localhost:5000`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/missions` | Create a new mission. |
| `GET` | `/missions` | List missions. |
| `GET` | `/missions/<mission_id>` | Get mission. |
| `POST` | `/missions/<mission_id>/tasks` | Add task. |
| `POST` | `/missions/<mission_id>/run` | Run mission. |
| `GET` | `/missions/<mission_id>/runs` | List runs. |
| `GET` | `/templates` | Mission templates. |
| `GET` | `/health` | Health check and service status. |

---

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

---

## `GET /missions/<mission_id>`

Get a specific mission by ID.

### Response `200`

```json
{
  "error": "Error description"
}
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

---

## `POST /missions/<mission_id>/run`

Run mission.

### Response `200`

```json
{
  "error": "Error description"
}
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
