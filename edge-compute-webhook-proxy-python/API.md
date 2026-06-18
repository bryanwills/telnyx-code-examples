# API Reference — Edge Compute Webhook Proxy

This is a serverless edge function deployed via `telnyx-edge`. It does not expose traditional HTTP endpoints — Telnyx routes webhook events directly to the function.

## Function Interface

| Input | Output |
|-------|--------|
| Telnyx webhook event (JSON) | Processed event with routing metadata |

### Input

```json
{
  "data": {
    "event_type": "call.initiated",
    "payload": { }
  }
}
```

### Output

```json
{
  "status": "processed",
  "event_type": "call.initiated",
  "routed_to": "voice_handler"
}
```

## Supported Event Types

| Event Pattern | Handler |
|---------------|---------|
| `call.*` | Voice handler |
| `message.*` | SMS handler |
| `sim_card.*` | IoT handler |
| Other | Default handler (log + return) |

**Deploy:**

```bash
telnyx-edge deploy --name my-webhook-proxy
```

**Test locally:**

```bash
curl -X POST http://localhost:8080/webhook \
  -H "Content-Type: application/json" \
  -d '{"event_type": "call.initiated", "data": {"call_control_id": "abc-123"}}'
```
