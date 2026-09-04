# API Reference — Conference Agent Mediator

Typed reference for the Edge function's HTTP surface. All routes are served from the deployed function URL: `https://conference-agent-mediator-<id>.telnyxcompute.com`.

## Health

### `GET /health/liveness`

Returns `200` with body `ok`.

### `GET /health/readiness`

Returns `200`:

```json
{ "status": "ok", "demoMode": true }
```

## Voice Webhook

### `POST /webhooks/voice`

Receiver for Telnyx Call Control voice/conference events. Body is the standard Telnyx webhook envelope:

```json
{
  "data": {
    "event_type": "conference.created",
    "payload": { "conference_id": "...", "call_control_id": "...", "name": "..." }
  }
}
```

| `event_type` | Agent action |
|--------------|--------------|
| `conference.created`, `conference.start` | Spawns `ConferenceAgent`, arms the 30s mediation timer |
| `conference.participant.joined` | Tracks the participant (silence clock starts) |
| `conference.participant.left` | Removes the participant |
| `call.transcription` (`is_final=true`) | Appends the utterance, refreshes the speaker's last-spoken time |
| `conference.ended`, `conference.end` | Stops the timer; runs summarize → store → SMS pipeline |

Responses: `200` with `{ "action": "..." }`, `400` for malformed payloads (`no event_type in payload`, `no conference_id in payload`).

## Demo Simulator

Drives the same agent pipeline as live webhooks with `demo=true` — no live Call Control or SMS side effects.

### `POST /demo/conference`

```json
{ "name": "Sprint Planning" }
```

→ `200`:

```json
{ "conference_id": "demo-abc123", "demo": true, "next": "POST /demo/conference/{id}/join" }
```

### `POST /demo/conference/{id}/join`

```json
{ "name": "alice" }
```

→ `200` `{ "joined": "alice", "conference_id": "..." }` · `400` if `name` missing.

### `POST /demo/conference/{id}/say`

```json
{ "speaker": "alice", "text": "We need to ship the billing fix by Friday." }
```

→ `200` `{ "recorded": true, "conference_id": "..." }` · `400` if `speaker`/`text` missing.

### `POST /demo/conference/{id}/end`

→ `200`:

```json
{ "ending": true, "conference_id": "...", "next": "GET /conferences/{id}" }
```

Ends the conference: cancels the mediation timer and runs `summarize → store → notify` asynchronously (LLM summary via the `[telnyx]` binding; SMS skipped in demo mode).

## Conference Queries

### `GET /conferences?limit=50`

Lists finished conferences from the shared registry actor:

```json
{
  "conferences": [
    {
      "conference_id": "demo-abc123",
      "friendly_name": "Sprint Planning",
      "participants": 2,
      "turn_count": 4,
      "summary": "...",
      "started_at": 1725400000000,
      "ended_at": 1725400200000,
      "status": "stored"
    }
  ]
}
```

### `GET /conferences/{id}`

Full agent state snapshot:

```json
{
  "conferenceId": "demo-abc123",
  "friendlyName": "Sprint Planning",
  "demo": true,
  "phase": "done",
  "participants": { "alice": 1725400060000, "bob": 1725400090000 },
  "turns": [{ "speaker": "mediator", "text": "bob, ...", "at": 1725400120000 }],
  "transcriptText": "[alice]: ...\n[mediator]: ...",
  "promptsSent": ["bob:1725400120000"],
  "summary": "...",
  "startedAt": 1725400000000,
  "endedAt": 1725400200000,
  "model": "zai-org/GLM-5.2",
  "smsSent": false,
  "error": ""
}
```

`404` if the conference id is unknown (`conference not found`).

### `GET /conferences/{id}/transcript?since=0`

Polling transcript feed — turn records with `at > since` (epoch ms):

```json
{
  "conference_id": "demo-abc123",
  "turns": [{ "speaker": "alice", "text": "...", "at": 1725400050000 }],
  "phase": "active",
  "summary": ""
}
```

### `GET /conferences/{id}/events?afterSeq=0`

Replay of the agent's durable progress-event stream (seq-ordered, exclusive cursor):

```json
{
  "conference_id": "demo-abc123",
  "events": [
    { "seq": 1, "type": "conference_started", "payload": { "conferenceId": "...", "demo": true }, "at": "2026-09-04T00:30:00.000Z" },
    { "seq": 6, "type": "prompt_sent", "payload": { "participant": "bob", "prompt": "..." }, "at": "..." }
  ]
}
```

Event types: `conference_started`, `participant_joined`, `participant_left`, `mediate_tick`, `mediate_skipped`, `prompt_sent`, `prompt_failed`, `prompt_spoken`, `prompt_speak_failed`, `sms_skipped_demo`, `sms_skipped_no_routing`, `sms_sent`.

## Dashboard

### `GET /`

Single-page HTML dashboard: start/join/say/end demo controls, live transcript polling every 2s, and the rendered post-conference summary.

## Status Codes

| Code | Meaning |
|------|---------|
| `200` | Success |
| `400` | Malformed body or missing required field |
| `404` | Unknown route or conference id |
| `500` | Actor/registry failure (message included in `error`) |
