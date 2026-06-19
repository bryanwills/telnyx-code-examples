---
description: Orchestrate multi-step Telnyx Missions workflows with task dependencies,
  error handling, and status tracking.
framework: flask
language: python
name: missions-workflow-orchestrator
telnyx_products:
- SMS/MMS
- Verify
- Number Porting
title: Missions Workflow Orchestrator
---



# Missions Workflow Orchestrator

Missions Workflow Orchestrator — create and manage multi-step mission workflows using the Telnyx Missions API.

## Telnyx API Endpoints Used

- **Create Number Order**: `POST /v2/number_orders` — [API reference](https://developers.telnyx.com/api/numbers/create-number-order)
- **Send Message**: `POST /v2/messages` — [API reference](https://developers.telnyx.com/api/messaging/send-message)
- **Create Call**: `POST /v2/calls` — [API reference](https://developers.telnyx.com/api/call-control/create-call)
- **Create Porting Order**: `POST /v2/porting_orders` — [API reference](https://developers.telnyx.com/api/porting/create-porting-order)

## Architecture

```
  API Request
        │
        ▼
  ┌──────────────────┐
  │ Call Control      │
  └────────┬─────────┘
           │
           ├──► Messaging
           ├──► Number Porting
           ├──► Number Management
           │
           ▼
     JSON response
```

## Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Type | Example | Required | Description | Where to get it |
|----------|------|---------|----------|-------------|-----------------|
| `TELNYX_API_KEY` | `string` | `KEY0123456789ABCDEF` | **yes** | Telnyx API v2 key | [Portal](https://portal.telnyx.com/api-keys) |
| `PORT` | `integer` | `5000` | no | HTTP server port | — |

## Setup

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/missions-workflow-orchestrator-python
cp .env.example .env    # ← fill in your credentials
pip install -r requirements.txt
python app.py           # starts on http://localhost:5000
```

## API Reference

### `POST /missions`

Triggers missions

```bash
curl -X POST http://localhost:5000/missions \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Response:**

```json
{
  "id": "item-1750280400",
  "status": "created",
  "created_at": "2026-07-15T14:30:00Z"
}
```

### `GET /missions`

Returns missions

```bash
curl http://localhost:5000/missions
```

**Response:**

```json
{
  "items": [
    {
      "id": "item-001",
      "status": "active",
      "created_at": "2026-07-15T14:30:00Z"
    }
  ]
}
```

### `GET /missions/<mission_id>`

Returns mission id

```bash
curl http://localhost:5000/missions/example-id
```

**Response:**

```json
{
  "items": [
    {
      "id": "item-001",
      "status": "active",
      "created_at": "2026-07-15T14:30:00Z"
    }
  ]
}
```

### `POST /missions/<mission_id>/tasks`

Triggers tasks

```bash
curl -X POST http://localhost:5000/missions/example-id/tasks \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Response:**

```json
{
  "id": "item-1750280400",
  "status": "created",
  "created_at": "2026-07-15T14:30:00Z"
}
```

### `POST /missions/<mission_id>/run`

Triggers run

```bash
curl -X POST http://localhost:5000/missions/example-id/run \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Response:**

```json
{
  "id": "item-1750280400",
  "status": "created",
  "created_at": "2026-07-15T14:30:00Z"
}
```

### `GET /missions/<mission_id>/runs`

Returns runs

```bash
curl http://localhost:5000/missions/example-id/runs
```

**Response:**

```json
{
  "items": [
    {
      "id": "item-001",
      "status": "active",
      "created_at": "2026-07-15T14:30:00Z"
    }
  ]
}
```

### `GET /templates`

Returns templates

```bash
curl http://localhost:5000/templates
```

**Response:**

```json
{
  "items": [
    {
      "id": "item-001",
      "status": "active",
      "created_at": "2026-07-15T14:30:00Z"
    }
  ]
}
```

### `GET /health`

Returns health

```bash
curl http://localhost:5000/health
```

**Response:**

```json
{
  "status": "ok",
  "uptime_seconds": 3842,
  "active_sessions": 2,
  "version": "1.0.0"
}
```

## Resources

- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Telnyx Portal](https://portal.telnyx.com)
