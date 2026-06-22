# Build a Cloud Storage Call Archive

Cloud Storage Call Archive — archive call recordings to Telnyx Cloud Storage with searchable metadata.

## How It Works

Telnyx Cloud Storage is **S3-compatible**, so this app talks to it with the AWS SDK (`boto3`) instead of a bespoke REST client. Recordings are downloaded from their Telnyx URL over HTTPS, then uploaded to a bucket with their metadata attached to the object.

```
  call.recording.saved          POST /archive
        │                              │
        ▼                              ▼
  ┌──────────────────┐        ┌──────────────────┐
  │ Webhook handler  │        │ Download recording│
  │ (queue metadata) │        │ from Telnyx (HTTPS)│
  └──────────────────┘        └────────┬─────────┘
                                        │ boto3 put_object
                                        ▼
                          Telnyx Cloud Storage (S3-compatible)
                       https://{region}.telnyxcloudstorage.com
```

## Telnyx Products Used

- **Cloud Storage** — S3-compatible object storage for recordings and media
- **Voice / Call Recording** — call recordings delivered via the `call.recording.saved` webhook

## How Telnyx Cloud Storage Authenticates

Cloud Storage uses the S3 API. The client points at `https://{region}.telnyxcloudstorage.com` and passes your **Telnyx API key as both the access key and the secret key**:

```python
s3 = boto3.client(
    "s3",
    endpoint_url=f"https://{REGION}.telnyxcloudstorage.com",
    aws_access_key_id=TELNYX_API_KEY,
    aws_secret_access_key=TELNYX_API_KEY,
    region_name=REGION,
    config=Config(signature_version="s3v4"),
)
```

Valid regions: `us-central-1`, `us-east-1`, `us-west-1`, `eu-central-1`.

## Webhook Events

Telnyx uses webhooks for call control — you don't poll for state. This app handles ([Call Control docs](https://developers.telnyx.com/docs/api/v2/call-control)):

- `call.recording.saved` — Call recording saved; the app reads `data.payload.recording_urls.mp3` and queues it for archival.

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)
- [Cloud Storage](https://portal.telnyx.com/storage) enabled on your account
- [Phone number](https://portal.telnyx.com/numbers/my-numbers) with voice enabled (to produce recordings)
- [Call Control Application](https://portal.telnyx.com/call-control/applications) configured with your webhook URL
- [ngrok](https://ngrok.com) for exposing your local server to Telnyx webhooks

## Step 1: Set Up the Project

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/cloud-storage-call-archive-python
cp .env.example .env
pip install -r requirements.txt
```

Edit `.env` with your Telnyx credentials:

- `TELNYX_API_KEY` — used for both recording download and S3 auth
- `BUCKET_NAME` — defaults to `call-archive`
- `TELNYX_STORAGE_REGION` — defaults to `us-central-1`

## Step 2: Understand the Code

Everything lives in `app.py`. Dependencies are `flask`, `boto3` (S3 client), `requests` (recording download), and `python-dotenv`. Here's what each piece does.

### S3 Client and the Telnyx-URL Guard

The `boto3` S3 client is created once at startup against the Telnyx endpoint (see above). The `is_telnyx_url()` helper enforces that recordings are only fetched from `https` Telnyx hosts — this prevents SSRF and stops the bearer token from leaking to an attacker-supplied URL.

### Creating and Listing Buckets

**`create_bucket()`** — Idempotently creates the bucket via `s3.create_bucket`. `BucketAlreadyOwnedByYou` / `BucketAlreadyExists` are treated as success.

**`list_buckets()`** — Calls `s3.list_buckets` and returns the bucket names.

### Archiving a Recording

**`archive_recording()`** — The core flow. Validates `recording_url` is an https Telnyx URL, downloads the audio from Telnyx with the API key as a bearer token, then `s3.put_object` stores it at `{YYYY}/{MM}/{DD}/{call_id}.mp3` with `ContentType="audio/mpeg"` and the supplied `metadata` (string-coerced) attached. The entry is appended to the in-memory index.

### Handling Webhooks

**`handle_recording_webhook()`** — On `call.recording.saved`, reads `data.payload.recording_urls.mp3` and queues an entry with the `call_control_id`, recording URL, and `recording_duration_millis`.

### Listing and Searching

- **`list_archive()`** — Returns the most recent 50 entries, optionally filtered by `date` (`YYYY/MM/DD`) matched against the object key.
- **`search_archive()`** — Case-insensitive full-text search across the JSON of each index entry; returns up to 20 results.

### All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/buckets` | Create the archive bucket |
| `GET` | `/buckets` | List buckets |
| `POST` | `/archive` | Download + store a recording |
| `POST` | `/webhooks/recording` | Telnyx webhook handler |
| `GET` | `/archive` | List archived recordings |
| `GET` | `/archive/search` | Search the metadata index |
| `GET` | `/health` | Health check |

## Step 3: Run It

```bash
python app.py
```

Server starts on `http://localhost:5000`. Create the bucket once:

```bash
curl -X POST http://localhost:5000/buckets
```

In a separate terminal, expose your server for webhooks:

```bash
ngrok http 5000
```

Copy the HTTPS URL and set it in the [Telnyx Portal](https://portal.telnyx.com):

- **Call Control Application** → Webhook URL → `https://<id>.ngrok.io/webhooks/recording`

## Step 4: Test It

**Health check:**

```bash
curl http://localhost:5000/health
```

**Archive a recording:**

```bash
curl -X POST http://localhost:5000/archive \
  -H "Content-Type: application/json" \
  -d '{
    "recording_url": "https://api.telnyx.com/v2/recordings/abc123/download.mp3",
    "call_id": "call-abc123",
    "metadata": {"agent": "alice"}
  }'
```

Or place a call on your Telnyx number with recording enabled — the `call.recording.saved` webhook will queue it.

**Search results:**

```bash
curl "http://localhost:5000/archive/search?q=alice" | python3 -m json.tool
```

## Going to Production

This example uses an in-memory list for the metadata index. For production:

- **Database** — replace the in-memory `archive_index` with PostgreSQL or Redis
- **Auto-archive** — have the webhook handler call the archive flow directly instead of only queueing
- **Authentication** — add API key validation on your endpoints
- **Webhook verification** — validate Telnyx webhook signatures ([docs](https://developers.telnyx.com/docs/api/v2/overview#webhook-signing))
- **Error recovery** — retry failed downloads/uploads with backoff
- **Monitoring** — add structured logging and health check alerts
- **Rate limiting** — protect your endpoints from abuse

## Run

```bash
pip install -r requirements.txt
python app.py
```

## Resources

- [Source code and reference](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/cloud-storage-call-archive-python/README.md)
- [Cloud Storage quick start](https://developers.telnyx.com/docs/cloud-storage/quick-start)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Telnyx Portal](https://portal.telnyx.com)
