# Click To Call Webrtc With Ai Assist

Click-to-Call WebRTC with AI Assist — browser-based calling with real-time AI coaching sidebar.

## Telnyx Products Used

- AI Inference

## How It Works

1. **API call** triggers the workflow
2. Telnyx **webhook** delivers the event to your app
3. **AI processes** the request using Telnyx Inference
4. App **takes action** (creates record, dispatches, notifies)
5. **Customer notified** of outcome via SMS

```
API Trigger ──────────────────────────► Your App
                                          │
                                          ├──► Telnyx AI Inference
                                          │
                                          ▼
                                  Customer Notification
                                      (SMS/Voice)
```

## Quick Start

### Prerequisites

- Python 3.8+
- A [Telnyx account](https://portal.telnyx.com/sign-up) with API key

### Install & Run

```bash
# Configure
cp .env.example .env
# Edit .env with your real credentials

# Install
pip install -r requirements.txt

# Run
python app.py
```

### Docker

```bash
docker build -t click-to-call-webrtc-with-ai-assist .
docker run --env-file .env -p 5000:5000 click-to-call-webrtc-with-ai-assist
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TELNYX_API_KEY` | Your Telnyx API key from [portal.telnyx.com](https://portal.telnyx.com) | Yes |
| `AI_MODEL` | AI model for inference (default: `moonshotai/Kimi-K2.6`) | No |
| `WEBRTC_CREDENTIAL_ID` | Webrtc Credential Id | Yes |
| `CONNECTION_ID` | Telnyx Call Control connection ID | Yes |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | `GET` / |
| `POST` | `/webrtc/token` | List all token |
| `POST` | `/coaching` | List all coaching |
| `GET` | `/health` | Health check and service status |

## Testing

**List records:**

```bash
curl http://localhost:5000/
```

**Trigger action:**

```bash
curl -X POST http://localhost:5000/webrtc/token \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Health check:**

```bash
curl http://localhost:5000/health
```

## Learn More

- [Telnyx Developer Docs](https://developers.telnyx.com)
- [AI Inference Guide](https://developers.telnyx.com/docs/inference)
- [Telnyx Portal](https://portal.telnyx.com)
