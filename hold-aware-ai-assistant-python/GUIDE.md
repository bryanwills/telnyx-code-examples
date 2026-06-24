# Build a Hold-Aware AI Assistant

This example demonstrates the core cookbook pattern: keep the phone call connected while reducing AI Assistant runtime during hold.

## Hold Detection Sources

The app can enter hold monitoring from:

- Telnyx `call.hold`
- the assistant tool endpoint `/tools/hold-detected`
- transcript phrases such as `please hold`, `next available representative`, or `estimated wait time`

## Representative Detection Sources

The app resumes the representative assistant from:

- Telnyx `call.unhold`
- transcript phrases such as `thanks for holding`, `how can I help`, or `this is`

## Production Notes

- Tune phrase detectors for your vertical.
- Persist call sessions in Redis or Postgres.
- Verify Telnyx webhook signatures before trusting call lifecycle and transcription events.
- Add alerting for calls stuck in hold monitoring.
- Review disclosure, recording, and transcription requirements before production use.
