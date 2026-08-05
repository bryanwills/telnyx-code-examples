## `POST /assistant/create`

Create or reuse the multilingual Voice AI Assistant. If `TELNYX_ASSISTANT_ID` is set in `.env`, returns that assistant. Otherwise creates a new one with the code-switching instructions, Deepgram nova-3 multilingual transcription, and `voice ultra katie` TTS.

### Response `200`

```json
{
  "assistant_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "multilingual code-switching voice agent",
  "model": "moonshotai/Kimi-K2.6",
  "voice": "voice ultra katie",
  "transcription_model": "deepgram/nova-3",
  "transcription_language": "multi",
  "enabled_features": ["telephony"],
  "telephony_settings": {"default_texml_app_id": "..."}
}
```

**Try it:**

```bash
curl -X POST http://localhost:5050/assistant/create
```

---

## `POST /call/trigger`

Trigger an outbound demo call to a given number via `POST /v2/texml/ai_calls/<texml_app_id>`.

### Request

```json
{
  "to": "+13125550001"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `to` | `string` (E.164) | **yes** | Number to call. Must include `+` prefix and country code. |

### Response `200`

```json
{
  "call_control_id": "v3:...",
  "to": "+13125550001",
  "from": "+18005551234",
  "assistant_id": "550e8400-...",
  "status": "triggered"
}
```

### Response `400`

```json
{"error": "Missing required field: 'to'"}
```

```json
{"error": "Phone number must be in E.164 format (e.g., +15551234567)"}
```

### Response `500`

```json
{"error": "TELNYX_ASSISTANT_ID is not set. Run provision_assistant.py first."}
```

**Try it:**

```bash
curl -X POST http://localhost:5050/call/trigger \
  -H "Content-Type: application/json" \
  -d '{"to": "+13125550001"}'
```

---

## `POST /webhooks/call`

Telnyx webhook receiver. The conversation is handled by the Voice AI Assistant — Flask only logs events for observability. Verifies Ed25519 signature if `TELNYX_PUBLIC_KEY` is set.

### Response `200`

```json
{"status": "received"}
```

---

## `GET /health`

Liveness check.

### Response `200`

```json
{
  "status": "ok",
  "uptime_s": 3600,
  "assistant_configured": true,
  "phone_configured": true
}
```

---

## `GET /`

Browser UI with a "Call me" button. Enter a phone number, click Call me, and the app triggers an outbound call to that number using the multilingual assistant.

---

## `GET /telnyx-logo.svg`

Serve the Telnyx logo SVG for the browser UI.
