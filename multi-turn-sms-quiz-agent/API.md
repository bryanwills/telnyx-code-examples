# API

## Demo routes

### `GET /`

Serves the browser SMS simulator unless `DEMO_MODE` is `"false"`.

### `POST /send`

Simulates inbound SMS in demo mode.

```json
{
  "from": "+15551234567",
  "text": "start"
}
```

The handler routes to `env.QUIZ.idFromName(phone).receive(...)` with a synthetic
event id.

### `GET /events?from=+15551234567&limit=50`

Returns the actor-local SQL quiz log.

```json
{
  "events": [
    {
      "id": 1,
      "sender": "+15551234567",
      "turn": 1,
      "role": "question",
      "text": "Q1/5 ...",
      "score": 0,
      "difficulty": "easy",
      "correct": false,
      "at": 1786489200000
    }
  ]
}
```

### `GET /status?from=+15551234567`

Returns durable actor state: `phase`, `score`, `difficulty`, `turn`, current
question metadata, sender, recipient, and timestamps.

## Production webhook

### `POST /webhooks/messaging`

Accepts Telnyx `message.received` webhooks.

Production mode verifies the raw request body with:

```ts
telnyxClient.webhooks.unwrap(body, { headers, key: publicKey })
```

The handler extracts `data.id` for idempotency, routes by sender phone number,
queues the actor process, and returns `2xx` quickly.

## Telnyx binding calls

Inference:

```ts
await this.env.TELNYX.ai.openai.chat.createCompletion({
  model: "zai-org/GLM-5.2",
  messages,
});
```

SMS send in production:

```ts
await this.env.TELNYX.messages.send({
  from: telnyxNumber,
  to: userNumber,
  text,
});
```
