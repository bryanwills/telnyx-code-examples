# Conversation Relay Voice Bot — API Reference

Endpoint shapes match the actual `app.py` implementation. This app is a
text-over-WebSocket bridge between a Telnyx phone call and an external
OpenAI-compatible chatbot. It exposes no public REST API beyond the
health and state endpoints — the interesting surface is the WebSocket
that Telnyx Conversation Relay connects to.

## TeXML

### `GET|POST /texml/inbound`

Returns the TeXML response that hands the inbound call to Conversation
Relay. Telnyx calls this when a caller dials your number; you don't call
it directly.

```xml
<Response>
  <Connect>
    <ConversationRelay url="wss://&lt;your-public-host&gt;/ws/conversation-relay"/>
  </Connect>
</Response>
```

## WebSocket

### `WS /ws/conversation-relay`

The Conversation Relay channel. Telnyx connects here, sends text frames
representing caller speech, and expects text frames back that get
spoken to the caller. The bridge forwards each prompt to the configured
chatbot via OpenAI-compatible `/v1/chat/completions`.

**Inbound frame types (Telnyx → bridge)**: `setup`, `prompt`, `dtmf`,
`interrupt`, `update`.

**Outbound frame types (bridge → Telnyx)**: `text` (streamed reply
tokens), `end` (turn complete).

## HTTP

### `GET|POST /callbacks/conversation-relay`

Conversation Relay action callback. Logged, returns `204 No Content`.

### `GET /health`

```bash
curl http://localhost:8000/health
```

```json
{
  "status": "ok",
  "active_sessions": 0
}
```

### `GET /api/state`

Returns the in-memory session map (call control id → chat history) for
debugging. Not for production use.

```bash
curl http://localhost:8000/api/state
```

### `GET /events`

Server-Sent Events stream of bridge lifecycle events (session start,
prompt received, bot reply, session end). Useful for live debugging.

### `GET /`

Landing page describing the bridge and linking to the GitHub source.

## Error Format

All HTTP errors return JSON:

```json
{"error": "message"}
```

| HTTP status | Meaning |
|-------------|---------|
| `200` | Success |
| `204` | No content (callback acknowledged) |
| `400` | Bad request — missing or invalid body |
| `500` | Internal error (chatbot upstream failure, unexpected exception) |
