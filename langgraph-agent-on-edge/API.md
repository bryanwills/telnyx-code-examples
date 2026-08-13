# API Reference

## Endpoints

### `GET /health`

Health check endpoint.

**Response:** `200 OK`

```json
{
  "ok": true,
  "demo": true,
  "smsTransport": "demo",
  "brand": "langgraph-agent-on-edge v0.1.0"
}
```

### `GET /version`

Version info.

**Response:** `200 OK`

```json
{ "brand": "langgraph-agent-on-edge v0.1.0" }
```

### `GET /`

Demo HTML UI (when `DEMO_MODE=true`). Shows a chat interface, turn state machine display, and process log.

**Response:** `200 OK` (HTML) or `404` (demo disabled)

### `HEAD /`

Demo UI availability check (when `DEMO_MODE=true`).

**Response:** `200` (with `x-brand-version` header) or `404`

### `POST /send`

Send a message from the demo UI. Creates a new actor instance for the sender and processes the message.

**Request:**

```json
{
  "text": "where is order ORD-10042?",
  "from": "+15551234567"
}
```

**Response:** `200 OK`

```json
{ "ok": true }
```

**Errors:**
- `400` — `text` is required or `from` is not E.164

### `GET /events`

Retrieve conversation events for the demo UI. Returns conversation history, process log, and turn state machine values.

**Query Parameters:**
- `from` — E.164 phone number (defaults to `DEMO_SENDER_NUMBER`)
- `limit` — max events to return (1-100, defaults to 50)

**Response:** `200 OK`

```json
{
  "conversation": [
    { "id": 1, "role": "user", "content": "where is my order?", "at": 1723480000000 },
    { "id": 2, "role": "assistant", "content": "Your order is shipped.", "at": 1723480001000 }
  ],
  "processLog": [
    { "id": 1, "turn": 1, "phase": "receive", "intent": "unknown", "note": "queued; text=\"where is my order?\"", "at": 1723480000000 },
    { "id": 2, "turn": 1, "phase": "process_start", "intent": "unknown", "note": "target=1; lastSent=0", "at": 1723480000100 },
    { "id": 3, "turn": 1, "phase": "graph_done", "intent": "order", "note": "reply=\"Your order is shipped.\"", "at": 1723480000500 },
    { "id": 4, "turn": 1, "phase": "sms_mocked", "intent": "order", "note": "clientRef=turn-1", "at": 1723480000600 },
    { "id": 5, "turn": 1, "phase": "commit", "intent": "order", "note": "lastSentTurn=1", "at": 1723480000700 }
  ],
  "turnState": {
    "turn": 1,
    "queuedTurn": 1,
    "processingTurn": 0,
    "lastSentTurn": 1,
    "pendingOutbound": null
  }
}
```

### `POST /` or `POST /webhooks/messaging`

Telnyx messaging webhook handler. Receives `message.received` events and routes them to the conversation actor.

**Signature Verification:**
- When `SMS_TRANSPORT=production`: verifies the `telnyx-signature-ed25519` header using `TELNYX_PUBLIC_KEY` via `telnyx.webhooks.unwrap()`.
- When `SMS_TRANSPORT=demo`: parses the body directly without verification.

**Request Body:** Telnyx `message.received` webhook payload

```json
{
  "data": {
    "id": "evt-12345",
    "event_type": "message.received",
    "payload": {
      "from": { "phone_number": "+15550001111" },
      "to": [{ "phone_number": "+15557654321" }],
      "text": "where is my order ORD-10042?"
    }
  }
}
```

**Response:**
- `200 OK` — `{"ok": true}` (event processed)
- `200 OK` — `{"ignored": true, "event_type": "..."}` (non-`message.received` event)
- `401` — signature verification failed
- `400` — invalid payload

## Types

### `Conversation` (Agent)

```typescript
class Conversation extends Agent<Env, ConvState> {
  receive(input: ReceiveMessageInput): Promise<void>;
  process(): Promise<void>;
  nudge(): Promise<void>;
  getEvents(limit?: number): Promise<EventsResponse>;
}
```

### `TelnyxBoundChatModel` (LangChain chat model)

```typescript
class TelnyxBoundChatModel extends SimpleChatModel {
  constructor(opts: { env: Env; model: string });
  _call(messages: BaseMessage[]): Promise<string>;
  _llmType(): string;  // "telnyx-bound"
}
```

### `ConvState` (durable state)

```typescript
interface ConvState {
  from: string;           // customer E.164
  to: string;             // agent E.164
  turn: number;           // monotonic inbound counter
  queuedTurn: number;     // turn process() should handle
  processingTurn: number; // turn currently processing
  lastSentTurn: number;   // highest sent turn
  pendingOutbound: PendingOutbound | null;
  lastIntent: Intent;     // "order" | "smalltalk" | "unknown"
  at: number;             // last process timestamp
}
```
