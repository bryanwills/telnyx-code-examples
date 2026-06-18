---
name: deepfake-voice-detector
title: "Deepfake Voice Detector"
description: "Real-time synthetic speech detection on live phone calls. Captures audio via media streaming, extracts acoustic features, scores deepfake probability with AI Inference, alerts security team via Slack."
language: python
framework: flask
telnyx_products: [Voice, AI Inference, Media Streaming]
integrations: [Slack]
channel: [voice]
---

# Deepfake Voice Detector

Real-time synthetic speech detection on live phone calls. Captures audio via Telnyx media streaming, extracts acoustic features (pitch regularity, breathing patterns, spectral distribution, crest factor), and uses AI Inference to score deepfake probability. Alerts security team via Slack when synthetic speech is detected.

## Telnyx API Endpoints Used

- **Call Control: Answer**: `POST /v2/calls/{id}/actions/answer` -- [API reference](https://developers.telnyx.com/api/call-control/answer-call)
- **Call Control: Speak (TTS)**: `POST /v2/calls/{id}/actions/speak` -- [API reference](https://developers.telnyx.com/api/call-control/speak)
- **Call Control: Start Streaming**: `POST /v2/calls/{id}/actions/streaming_start` -- [API reference](https://developers.telnyx.com/api/call-control/start-streaming)
- **AI Inference**: `POST /v2/ai/chat/completions` -- [API reference](https://developers.telnyx.com/api/inference/chat-completions)

## Telnyx Webhook Events

- `call.initiated` -- incoming call detected, app answers
- `call.answered` -- starts media streaming + greeting
- `call.streaming.started` -- audio capture begins
- `call.streaming.stopped` -- triggers deepfake analysis
- `call.hangup` -- session finalized

## External Service Integrations

- **Slack** -- Security team alerts via incoming webhooks

## Architecture

```text
Phone Call --> Telnyx Cloud --> /webhooks/voice (call lifecycle)
                   |
              Media Stream --> /webhooks/media (raw 8kHz PCM)
                                       |
                              Feature Extraction
                              (ZCR, crest, energy, pitch, silence)
                                       |
                              Telnyx AI Inference (scoring)
                                       |
                          < threshold        >= threshold
                          [Cleared]           [ALERT -> Slack]
```

## Environment Variables

| Variable | Type | Example | Required | Description | Where to get it |
|----------|------|---------|----------|-------------|-----------------|
| `TELNYX_API_KEY` | `string` | `KEY...` | **yes** | Telnyx API v2 key | [link](https://portal.telnyx.com/api-keys) |
| `MAIN_NUMBER` | `string` | `+18005551234` | **yes** | Telnyx phone number | [link](https://portal.telnyx.com/numbers/my-numbers) |
| `CONNECTION_ID` | `string` | `1234567890` | **yes** | Call Control connection ID | [link](https://portal.telnyx.com/call-control/applications) |
| `AI_MODEL` | `string` | `moonshotai/Kimi-K2.6` | no | Inference model | [link](https://developers.telnyx.com/docs/inference/models) |
| `DETECTION_THRESHOLD` | `float` | `0.75` | no | Deepfake score threshold | -- |
| `ALERT_WEBHOOK` | `string` | `https://hooks.slack.com/...` | no | Slack webhook for alerts | [link](https://api.slack.com/messaging/webhooks) |
| `MEDIA_STREAM_URL` | `string` | `wss://your-server/media` | no | WebSocket URL for streaming | -- |

## Setup

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/deepfake-voice-detector-python
cp .env.example .env
pip install -r requirements.txt
python app.py
```

### Docker

```bash
docker build -t deepfake-voice-detector .
docker run --env-file .env -p 5000:5000 deepfake-voice-detector
```

## API Reference

### `POST /calls/<call_id>/analyze`

Force deepfake analysis on collected audio.

```bash
curl -X POST http://localhost:5000/calls/v3_abc123/analyze
```

```json
{
  "call_id": "v3_abc123",
  "analysis": {
    "score": 0.82,
    "assessment": "likely_synthetic",
    "indicators": ["low_crest_factor", "absent_breathing_pauses"]
  },
  "flagged": true
}
```

### `GET /calls`

List all analyzed calls sorted by risk.

```bash
curl http://localhost:5000/calls
```

```json
{
  "total": 47,
  "flagged": 3,
  "calls": [{"call_id": "v3_abc123", "score": 0.82, "assessment": "likely_synthetic"}]
}
```

### `GET /health`

```bash
curl http://localhost:5000/health
```

```json
{"status": "ok", "active_calls": 2, "deepfakes_detected": 3, "detection_threshold": 0.75}
```

## Webhook Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/webhooks/voice` | Call Control events |
| `POST` | `/webhooks/media` | Raw audio chunks from media streaming |

## How Detection Works

1. **Audio capture** -- Media streaming delivers raw 8kHz PCM chunks
2. **Feature extraction** -- Zero-crossing rate, crest factor, energy CV, silence ratio, pitch regularity
3. **AI scoring** -- Features sent to Telnyx AI Inference for forensic assessment
4. **Alerting** -- Calls above threshold trigger Slack alerts

## Resources

- [Media Streaming Guide](https://developers.telnyx.com/docs/voice/media-streaming)
- [Call Control: Start Streaming](https://developers.telnyx.com/api/call-control/start-streaming)
- [AI Inference](https://developers.telnyx.com/api/inference/chat-completions)
- [Telnyx Developer Docs](https://developers.telnyx.com)
