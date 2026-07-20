## `POST /index`

Build the embedding index from the bundled sample tickets (or a provided list).

### Request (optional)

```json
{
  "tickets": [
    {"id": "TKT-1", "subject": "...", "body": "...", "category": "...", "priority": "..."}
  ]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `tickets` | `array[object]` | no | Custom ticket list. If omitted, uses bundled `sample_tickets.json` |

### Response `200`

```json
{
  "status": "indexed",
  "ticket_count": 15,
  "dimensions": 1024,
  "model": "thenlper/gte-large",
  "indexed_at": "2026-07-20T12:53:41Z"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/index
```

---

## `POST /search`

Search for tickets by meaning. Returns the top-k most similar tickets with cosine similarity scores.

### Request

```json
{
  "query": "I cannot send text messages to international phone numbers",
  "top_k": 3
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | `string` | **yes** | Natural-language search query |
| `top_k` | `integer` | no | Number of results to return (default 5, max 50) |

### Response `200`

```json
{
  "query": "I cannot send text messages to international phone numbers",
  "model": "thenlper/gte-large",
  "total_indexed": 15,
  "results": [
    {
      "ticket_id": "TKT-1002",
      "subject": "International SMS routing issue",
      "body": "Messages to Germany and France are not being delivered...",
      "category": "messaging",
      "priority": "high",
      "score": 0.9077
    }
  ]
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/search \
  -H "Content-Type: application/json" \
  -d '{"query":"audio quality problems on calls","top_k":3}'
```

---

## `POST /tickets`

Add a new ticket to the existing index.

### Request

```json
{
  "subject": "New billing question",
  "body": "Customer is asking about prorated charges after plan change.",
  "category": "billing",
  "priority": "low"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `subject` | `string` | **yes** | Ticket subject |
| `body` | `string` | **yes** | Ticket body |
| `category` | `string` | no | Ticket category |
| `priority` | `string` | no | Ticket priority |
| `id` | `string` | no | Custom ticket ID (auto-generated if omitted) |

### Response `201`

```json
{
  "status": "added",
  "ticket_id": "TKT-1783718627"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/tickets \
  -H "Content-Type: application/json" \
  -d '{"subject":"New issue","body":"Cannot receive faxes.","category":"fax","priority":"medium"}'
```

---

## `GET /tickets/<id>`

Fetch a ticket by ID.

### Response `200`

```json
{
  "id": "TKT-1001",
  "subject": "SMS delivery failure to UK numbers",
  "body": "...",
  "category": "messaging",
  "priority": "high",
  "created_at": "2025-06-01T10:00:00Z"
}
```

### Response `404`

```json
{"error": "ticket not found"}
```

**Try it:**

```bash
curl http://localhost:5000/tickets/TKT-1001
```

---

## `GET /stats`

Index statistics.

### Response `200`

```json
{
  "ticket_count": 15,
  "dimensions": 1024,
  "model": "thenlper/gte-large",
  "indexed_at": "2026-07-20T12:53:41Z",
  "indexed": true
}
```

**Try it:**

```bash
curl http://localhost:5000/stats
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "tickets": 15,
  "indexed": true,
  "version": "1.0.0"
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
  "error": "invalid request body"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `201` | Created |
| `400` | Bad request — missing or invalid fields, or index is empty |
| `404` | Ticket not found |
| `500` | Server error |
