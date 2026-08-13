# Guide

## Flow

1. User sends `start`.
2. `src/index.ts` routes the message to one actor per sender phone number.
3. `QuizAgent.receive()` deduplicates the event id, resets state, appends the
   user message, and queues `process()`.
4. `QuizAgent.process()` generates a question with Telnyx Inference.
5. User answers with `a`, `b`, `c`, or short free text.
6. The next `process()` call grades the answer, updates score and difficulty,
   then queues itself to generate the next question.
7. After `MAX_QUESTIONS`, the actor writes a final event and sends the final
   score in production mode.

## State

`this.setState()` stores:

- `phase`: `idle`, `asking`, `answering`, or `done`
- `score`
- `difficulty`: `easy`, `medium`, or `hard`
- `turn`
- `currentQuestion`
- `currentAnswer`
- `from` and `to`
- timestamps

The sender and recipient are stored in state so queued background work can send
the next SMS without depending on the original webhook request object.

## SQL

The actor creates two local tables:

- `webhook_events(event_id TEXT PRIMARY KEY, at INTEGER)` for idempotency
- `quiz_log(...)` for the demo UI and audit trail

SQLite booleans are stored as `0` or `1`.

## Compliance workaround

This sample defaults to demo mode because US A2P/toll-free compliance can block
real SMS during development. Demo mode only swaps the transport layer:

- inbound SMS becomes `POST /send`
- outbound SMS becomes SQL events read by `/events`

The production code path remains in place. Once the number and messaging profile
are approved, set `SMS_TRANSPORT = "production"` and ship again.
