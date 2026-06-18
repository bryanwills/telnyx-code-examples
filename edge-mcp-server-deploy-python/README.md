# Edge Mcp Server Deploy

Edge MCP Server Deploy — deploy an MCP (Model Context Protocol) server to Telnyx edge for AI tool hosting.

## Telnyx Products Used

- SMS/MMS Messaging

## How It Works

1. **API call** triggers the workflow
2. Telnyx **webhook** delivers the event to your app
3. App **takes action** (creates record, dispatches, notifies)
4. **Customer notified** of outcome via SMS

```
API Trigger ──────────────────────────► Your App
                                          │
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
docker build -t edge-mcp-server-deploy .
docker run --env-file .env -p 5000:5000 edge-mcp-server-deploy
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TELNYX_API_KEY` | Your Telnyx API key from [portal.telnyx.com](https://portal.telnyx.com) | Yes |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/mcp/tools` | List all tools |
| `POST` | `/mcp/tools/register` | `POST` /mcp/tools/register |
| `POST` | `/mcp/call` | `POST` /mcp/call |
| `GET` | `/mcp/deploy-info` | `GET` /mcp/deploy-info |
| `GET` | `/calls` | List all calls |
| `GET` | `/health` | Health check and service status |

## Testing

**List records:**

```bash
curl http://localhost:5000/mcp/tools
```

**Trigger action:**

```bash
curl -X POST http://localhost:5000/mcp/tools/register \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Health check:**

```bash
curl http://localhost:5000/health
```

## Learn More

- [Telnyx Developer Docs](https://developers.telnyx.com)
- [SMS & MMS Guide](https://developers.telnyx.com/docs/messaging)
- [Telnyx Portal](https://portal.telnyx.com)
