# Smart Number Geo Assignment

Smart Number Geo-Assignment — automatically purchase and assign local numbers based on caller geography to maximize answer rates.

## Human-in-the-Loop

This example includes human oversight at key decision points:

- **Manual assignment**

## How It Works

1. **API call** triggers the workflow
2. Telnyx **webhook** delivers the event to your app
3. App **takes action** (creates record, dispatches, notifies)
4. **Human reviews** via dashboard, Slack, or SMS reply
5. **Customer notified** of outcome via SMS

```
API Trigger ──────────────────────────► Your App
                                          │
                                          │
                                          ▼
                                     Human Review
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
docker build -t smart-number-geo-assignment .
docker run --env-file .env -p 5000:5000 smart-number-geo-assignment
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TELNYX_API_KEY` | Your Telnyx API key from [portal.telnyx.com](https://portal.telnyx.com) | Yes |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/assign` | Assign to a team member (triggers notifications) |
| `POST` | `/lookup-and-assign` | Assign to a team member (triggers notifications) |
| `GET` | `/inventory` | `GET` /inventory |
| `GET` | `/assignments` | List all assignments |
| `GET` | `/health` | Health check and service status |

## Testing

**List records:**

```bash
curl http://localhost:5000/inventory
```

**Trigger action:**

```bash
curl -X POST http://localhost:5000/assign \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Health check:**

```bash
curl http://localhost:5000/health
```

## Learn More

- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Telnyx Portal](https://portal.telnyx.com)
