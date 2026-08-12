## `POST /remind`

Schedule a new SMS reminder.

### Request

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `to` | `string` | **yes** | — | Recipient phone number (E.164) |
| `message` | `string` | **yes** | — | Reminder message text |
| `delay_minutes` | `number` | no | `5` | Minutes from now to send the reminder |
| `from` | `string` | no | `+16282564655` | Sender phone number (E.164) |

**Try it:**

```bash
curl -X POST https://scheduled-reminder-agent-<id>.telnyxcompute.com/remind \
  -H "Content-Type: application/json" \
  -d '{"to":"+17177247292","message":"Time to take your medication","delay_minutes":5}'
```

### Response `201`

```json
{
  "id": "reminder-1723372800000",
  "to": "+17177247292",
  "message": "Time to take your medication",
  "delay_minutes": 5
}
```

---

## `POST /webhooks/sms`

Receives Telnyx `message.received` webhooks. Routes inbound SMS replies to the per-phone-number actor for snooze detection.

### Request (Telnyx webhook payload)

```json
{
  "data": {
    "event_type": "message.received",
    "payload": {
      "from": {"phone_number": "+17177247292"},
      "to": [{"phone_number": "+16282564655"}],
      "text": "snooze for an hour"
    }
  }
}
```

### Response `200`

```json
{
  "action": "snoozed",
  "from": "+17177247292",
  "text": "snooze for an hour"
}
```

| `action` | Description |
|----------|-------------|
| `snoozed` | LLM detected snooze intent — reminder rescheduled with adaptive delay |
| `acknowledged` | User acknowledged — reminder marked done |
| `no_active_reminder` | No reminder awaiting a reply for this number |

---

## `POST /cancel`

Cancel a pending reminder.

### Request

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `to` | `string` | **yes** | Recipient phone number |
| `id` | `string` | **yes** | Reminder ID (from `POST /remind` response) |

**Try it:**

```bash
curl -X POST https://scheduled-reminder-agent-<id>.telnyxcompute.com/cancel \
  -H "Content-Type: application/json" \
  -d '{"to":"+17177247292","id":"reminder-1723372800000"}'
```

### Response `200`

```json
{
  "cancelled": true,
  "id": "reminder-1723372800000"
}
```

---

## `POST /debug/remind`

Schedule a reminder with a short delay for testing (no real SMS needed if you trigger `sendReminder` manually via `/debug/send`).

### Request

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `to` | `string` | no | `+17177247292` | Recipient phone number |
| `message` | `string` | no | `Test reminder` | Reminder text |
| `delay_minutes` | `number` | no | `0.1` (6 seconds) | Delay in minutes |
| `from` | `string` | no | `+16282564655` | Sender number |

**Try it:**

```bash
curl -X POST https://scheduled-reminder-agent-<id>.telnyxcompute.com/debug/remind \
  -H "Content-Type: application/json" \
  -d '{"to":"+17177247292","message":"Test reminder","delay_minutes":0.1}'
```

---

## `POST /debug/reply`

Simulate an inbound SMS reply for testing snooze detection without a real messaging profile.

### Request

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `from` | `string` | no | `+17177247292` | Sender phone number |
| `text` | `string` | no | `snooze` | Reply text |

**Try it:**

```bash
curl -X POST https://scheduled-reminder-agent-<id>.telnyxcompute.com/debug/reply \
  -H "Content-Type: application/json" \
  -d '{"from":"+17177247292","text":"snooze for 2 hours"}'
```

### Response `200`

```json
{
  "action": "snoozed",
  "snoozed": true,
  "from": "+17177247292",
  "text": "snooze for 2 hours"
}
```

---

## `POST /debug/send`

Manually trigger `sendReminder` for a scheduled reminder — useful for testing SMS delivery without waiting for the scheduler.

### Request

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `to` | `string` | no | Recipient phone number (default: `+17177247292`) |
| `id` | `string` | **yes** | Reminder ID |

---

## `GET /debug/state`

Inspect the actor's durable state for a phone number — all reminders, snooze history, adaptive timing config.

### Query Parameters

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `from` | `string` | no | Phone number to inspect (default: `+17177247292`) |

**Try it:**

```bash
curl "https://scheduled-reminder-agent-<id>.telnyxcompute.com/debug/state?from=+17177247292"
```

### Response `200`

```json
{
  "phoneNumber": "+17177247292",
  "fromNumber": "+16282564655",
  "reminders": [
    {
      "id": "reminder-1723372800000",
      "message": "Time to take your medication",
      "remindAt": 1786489200000,
      "status": "snoozed",
      "sentAt": 1786488000000,
      "snoozeCount": 2
    }
  ],
  "currentReminderId": "reminder-1723372800000",
  "awaitingReply": false,
  "totalSnoozes": 2,
  "totalReminders": 1,
  "adaptiveBaseSeconds": 1800
}
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
| `201` | Reminder created |
| `400` | Bad request — missing fields or unexpected event |
| `404` | Unknown route |
| `500` | Server error |
