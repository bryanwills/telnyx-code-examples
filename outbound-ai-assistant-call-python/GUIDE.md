# Build an Outbound AI Assistant Call

This example shows the smallest useful outbound AI phone call pattern.

## Flow

1. Your app receives `POST /calls/outbound`.
2. Your app calls `POST /v2/calls`.
3. Telnyx dials the destination number.
4. Telnyx sends `call.answered` to `/webhooks/telnyx`.
5. Your app starts the configured AI Assistant on the active call.
6. Telnyx sends `call.hangup` when the call ends.

## Production Notes

- Verify Telnyx webhook signatures before trusting events.
- Persist call state outside process memory.
- Add an allowlist for outbound destinations.
- Add authentication to `POST /calls/outbound`.
