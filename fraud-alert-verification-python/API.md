## `POST /alerts/trigger`

Initiates a fraud verification call to the customer. If the call fails, automatically falls back to SMS.

### Request

```json
{
  "phone": "+12125559999",
  "transaction": "TXN-98234",
  "amount": 847.50,
  "merchant": "Electronics Store",
  "risk_score": 92
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `phone` | `string` | **yes** | Customer phone number (E.164) |
| `transaction` | `string` | no | Transaction ID for tracking |
| `amount` | `number` | no | Transaction amount in dollars |
| `merchant` | `string` | no | Merchant name |
| `risk_score` | `number` | no | Risk score (0-100) |

### Response `200`

```json
{
  "alert": {
    "id": 0,
    "customer_phone": "+12125559999",
    "transaction": "TXN-98234",
    "amount": 847.50,
    "merchant": "Electronics Store",
    "risk_score": 92,
    "status": "calling",
    "created_at": "2026-06-18T20:30:00Z"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `alert.id` | `integer` | Auto-incrementing alert ID |
| `alert.status` | `string` | One of: `calling`, `call_failed`, `verified_legitimate`, `blocked`, `escalated` |
| `alert.created_at` | `string` | ISO 8601 timestamp |

### Status Transitions

```
calling ──► verified_legitimate    (customer pressed 1 or replied YES)
        ──► blocked                (customer pressed 2 or replied NO)
        ──► escalated              (customer pressed 3)
        ──► call_failed            (call couldn't connect → SMS fallback sent)
```

**Try it:**

```bash
curl -X POST http://localhost:5000/alerts/trigger \
  -H "Content-Type: application/json" \
  -d '{"phone": "+12125559999", "transaction": "TXN-98234", "amount": 847.5, "merchant": "Electronics Store", "risk_score": 92}'
```

---

## `GET /alerts`

Returns all alerts with aggregate statistics.

### Response `200`

```json
{
  "alerts": [
    {
      "id": 0,
      "customer_phone": "+12125559999",
      "transaction": "TXN-98234",
      "amount": 847.50,
      "merchant": "Electronics Store",
      "risk_score": 92,
      "status": "blocked",
      "created_at": "2026-06-18T20:30:00Z"
    }
  ],
  "stats": {
    "total": 1,
    "blocked": 1,
    "verified": 0,
    "escalated": 0
  }
}
```

**Try it:**

```bash
curl http://localhost:5000/alerts
```

---

## `POST /webhooks/voice`

Receives Telnyx Call Control webhook events. Do not call directly.

### Events Handled

| Event | Action |
|-------|--------|
| `call.answered` | Speaks the fraud alert message with TTS |
| `call.speak.ended` | Gathers DTMF input (1/2/3) |
| `call.gather.ended` | Processes customer choice |
| `call.hangup` | Cleans up call tracking state |

### DTMF Options

| Key | Action | Notifications |
|-----|--------|---------------|
| `1` | Approve transaction | TTS confirmation |
| `2` | Block transaction, freeze card | TTS + SMS + Slack alert |
| `3` | Escalate to fraud specialist | TTS + Slack alert |

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/voice
```

## `POST /webhooks/sms`

Receives inbound SMS replies. Do not call directly.

### SMS Commands

| Reply | Action |
|-------|--------|
| `YES` | Approve the transaction |
| `NO` | Block + freeze card + Slack alert |

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/sms
```

## `GET /health`

### Response `200`

```json
{
  "status": "ok",
  "active": 2
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

| Field | Type | Description |
|-------|------|-------------|
| `status` | `string` | Always `"ok"` |
| `active` | `integer` | Alerts currently in `calling` state |

---

## Error Handling

All endpoints return JSON. HTTP status is always `200` for successful requests.

```json
{ "error": "description of what went wrong" }
```
