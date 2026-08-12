## `POST /webhooks/sms`

Receives Telnyx `message.received` webhooks. Routes inbound SMS to the triage agent.

### Request (Telnyx webhook payload)

```json
{
  "data": {
    "event_type": "message.received",
    "payload": {
      "from": {"phone_number": "+17177247292"},
      "to": [{"phone_number": "+16282564655"}],
      "text": "Why was I charged $50?"
    }
  }
}
```

### Response `200`

```json
{
  "action": "triaged",
  "from": "+17177247292",
  "to": "+16282564655",
  "topic": "billing",
  "route": "billing-queue",
  "confidence": 0.95
}
```

---

## `POST /routes`

Update a route in the route table.

### Request

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `topic` | `string` | **yes** | Topic name (`billing`, `support`, `sales`, `general`) |
| `queue` | `string` | **yes** | Queue name to route to |
| `number` | `string` | no | Inbound number (default: `+16282564655`) |

**Try it:**

```bash
curl -X POST https://agent-sms-triage-bot-<id>.telnyxcompute.com/routes \
  -H "Content-Type: application/json" \
  -d '{"topic":"billing","queue":"priority-billing-queue"}'
```

### Response `200`

```json
{
  "topic": "billing",
  "queue": "priority-billing-queue",
  "number": "+16282564655"
}
```

---

## `GET /routes`

List the current route table.

### Query Parameters

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `number` | `string` | no | Inbound number (default: `+16282564655`) |

**Try it:**

```bash
curl "https://agent-sms-triage-bot-<id>.telnyxcompute.com/routes?number=+16282564655"
```

### Response `200`

```json
{
  "number": "+16282564655",
  "routes": {
    "billing": "billing-queue",
    "support": "support-queue",
    "sales": "sales-queue",
    "general": "general-queue"
  }
}
```

---

## `GET /history`

Get triage history — recent classifications with topic, route, and confidence.

### Query Parameters

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `number` | `string` | no | Inbound number (default: `+16282564655`) |
| `limit` | `number` | no | Max entries to return (default: `20`) |

**Try it:**

```bash
curl "https://agent-sms-triage-bot-<id>.telnyxcompute.com/history?number=+16282564655&limit=10"
```

### Response `200`

```json
{
  "number": "+16282564655",
  "entries": [
    {
      "at": 1786494000000,
      "from": "+17177247292",
      "text": "Why was I charged $50?",
      "topic": "billing",
      "route": "billing-queue",
      "confidence": 0.95
    }
  ],
  "total": 1,
  "topicCounts": {
    "billing": 1,
    "support": 0,
    "sales": 0,
    "general": 0
  }
}
```

---

## `POST /debug/triage`

Simulate an inbound SMS for testing without a real messaging profile.

### Request

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `from` | `string` | no | `+17177247292` | Sender number |
| `to` | `string` | no | `+16282564655` | Inbound number |
| `text` | `string` | no | `I need help with my bill` | Message text |

**Try it:**

```bash
curl -X POST https://agent-sms-triage-bot-<id>.telnyxcompute.com/debug/triage \
  -H "Content-Type: application/json" \
  -d '{"from":"+17177247292","text":"I want to upgrade my plan"}'
```

### Response `200`

```json
{
  "action": "triaged",
  "from": "+17177247292",
  "to": "+16282564655",
  "text": "I want to upgrade my plan",
  "topic": "sales",
  "route": "sales-queue",
  "confidence": 0.9
}
```

---

## `GET /debug/state`

Inspect the actor's durable state — route table, triage history, topic counts.

### Query Parameters

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `number` | `string` | no | Inbound number (default: `+16282564655`) |

**Try it:**

```bash
curl "https://agent-sms-triage-bot-<id>.telnyxcompute.com/debug/state?number=+16282564655"
```

---

## `GET /health/{liveness,readiness}`

Health check endpoints.

### Response `200`

```
ok
```

---

## Error Handling

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing fields or unexpected event |
| `404` | Unknown route |
| `500` | Server error |
