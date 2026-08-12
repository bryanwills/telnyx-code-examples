# Multi-Turn SMS Quiz Agent

An adaptive SMS quiz agent on Telnyx Edge Compute. Each sender gets a durable
`QuizAgent` StatefulActor that tracks score, difficulty, current question, and
quiz history across turns.

The default mode works around messaging compliance delays by replacing only the
carrier SMS transport with a browser simulator. Edge Compute, the Agent SDK,
StatefulActor state, SQL, and Telnyx Inference still run live.

## What it uses

- `QuizAgent extends Agent` from `@telnyx/edge-runtime`
- `[telnyx]` binding for zero-credential Telnyx Inference and Messaging
- `this.setState()` for durable quiz state
- actor-local SQL for quiz events and webhook idempotency
- `this.queue("process")` so webhooks ack quickly and LLM work runs async

## Run

```bash
npm install
npm run typecheck
npm run types
npm run ship
```

Open the deployed function URL in a browser. In demo mode, type `start`, then
reply with `a`, `b`, or `c`. The live panel shows phase, score, difficulty, and
turn while `/events` reads the actor SQL log.

## Demo vs production SMS

The browser simulator is controlled by `DEMO_MODE`; it is available unless
`DEMO_MODE = "false"` is set.
Real SMS transport is controlled by `SMS_TRANSPORT`; any value other than
`"demo"` enables signed webhooks and outbound `messages.send()`.

In demo mode:

- `POST /send` simulates inbound SMS.
- `GET /events` and `GET /status` power the browser UI.
- No outbound SMS is sent, so carrier compliance does not block the demo.

For production SMS:

1. Set `SMS_TRANSPORT = "production"`.
2. Store the Telnyx webhook public key:

   ```bash
   telnyx-edge secrets add TELNYX_PUBLIC_KEY "<public key>"
   ```

3. Point the messaging profile webhook to:

   ```text
   https://<function-url>/webhooks/messaging
   ```

4. Use an SMS-capable number with approved 10DLC/toll-free compliance.

When SMS transport is enabled, the same actor sends quiz questions, grades,
and final scores through `this.env.TELNYX.messages.send()`.
