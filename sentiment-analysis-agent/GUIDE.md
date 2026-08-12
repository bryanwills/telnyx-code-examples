# Implementation Guide

This sample is built around one actor per sender phone number.

## 1. Route inbound messages to an actor

`src/index.ts` accepts a Telnyx `message.received` webhook in production or a browser `/send` request in demo mode. Both paths call the same actor method:

```ts
await env.SENTIMENT.idFromName(actorNameForPhone(from)).receive({ text, from, to, eventId });
```

The actor key is derived from the sender phone number, so each sender gets isolated message history and SQL rows. Raw E.164 values include `+`, which is not valid in the actor reminder name used by the runtime, so the router converts `+15551234567` to `phone-15551234567`.

## 2. Ack fast and queue LLM work

`SentimentAgent.receive()` does only the synchronous work needed before acknowledging the webhook:

1. Create tables if needed.
2. Insert the webhook `eventId` into `webhook_events`.
3. Store sender state.
4. Add the user message.
5. Queue `process()`.

The LLM call does not run inside the webhook handler. Telnyx webhooks must be acknowledged quickly, and queued actor work is the durable path for longer processing.

## 3. Classify sentiment

`SentimentAgent.process()` sends a compact prompt to Telnyx Inference:

```ts
await this.env.TELNYX.ai.openai.chat.createCompletion({
  model: this.env.MODEL || "zai-org/GLM-5.2",
  messages: [
    { role: "system", content: SENTIMENT_SYSTEM_PROMPT },
    { role: "user", content: last.content },
  ],
});
```

The model must return JSON with:

```json
{
  "label": "positive",
  "score": 0.94,
  "reply": "Thanks for the kind note. We're here if you need anything."
}
```

The parser is defensive: it extracts the first JSON object, clamps score to `0..1`, validates the label, and falls back to a neutral reply if parsing fails.

## 4. Log to actor-local SQL

Every processed message writes one row:

```sql
INSERT INTO sentiment(sender, message, label, score, escalated, reply, at)
VALUES (?, ?, ?, ?, ?, ?, ?)
```

`escalated` is stored as `0` or `1` because SQL bindings support primitive values, not booleans.

## 5. Escalate negative sentiment

If `label === "negative"`, the row is marked escalated. In production mode, the agent sends a real SMS alert:

```ts
await this.env.TELNYX.messages.send({
  from: to,
  to: this.env.OPS_ALERT_PHONE,
  text: `Negative sentiment (${score}) from ${from}: "${message}"`,
});
```

In demo mode, this send is skipped and the browser UI shows the escalation badge from the SQL row.

## 6. Auto-reply

In production mode, every message gets a short SMS reply:

```ts
await this.env.TELNYX.messages.send({ from: to, to: from, text: reply });
```

In demo mode, the same reply text is written to SQL and message history, then surfaced through `/events`.

## 7. Move from demo to production

Set `PRODUCTION_MODE` explicitly to production:

```toml
[env_vars]
PRODUCTION_MODE = "true"
```

Then:

1. Store `TELNYX_PUBLIC_KEY`.
2. Ship the function.
3. Point the messaging profile webhook to `/webhooks/messaging`.
4. Ensure the number has toll-free verification or 10DLC approval for off-net US delivery.

The code path for production SMS already exists; compliance approval is the external gate.
