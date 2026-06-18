# Cloud Storage Call Archive

Cloud Storage Call Archive — archive call recordings to Telnyx Cloud Storage with searchable metadata.

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
docker build -t cloud-storage-call-archive .
docker run --env-file .env -p 5000:5000 cloud-storage-call-archive
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TELNYX_API_KEY` | Your Telnyx API key from [portal.telnyx.com](https://portal.telnyx.com) | Yes |
| `BUCKET_NAME` | Bucket Name | No |

## Webhook Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/webhooks/recording` | External webhook handler |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/buckets` | Create new record |
| `GET` | `/buckets` | List all buckets |
| `POST` | `/archive` | `POST` /archive |
| `GET` | `/archive` | List all archive |
| `GET` | `/archive/search` | `GET` /archive/search |
| `GET` | `/health` | Health check and service status |

## Testing

**List records:**

```bash
curl http://localhost:5000/buckets
```

**Trigger action:**

```bash
curl -X POST http://localhost:5000/buckets \
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
