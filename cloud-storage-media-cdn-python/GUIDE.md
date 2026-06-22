# Build a Cloud Storage Media CDN

Cloud Storage Media CDN — use Telnyx Cloud Storage as a CDN for IVR prompts, hold music, announcements, and voicemail greetings. Telnyx Cloud Storage is S3-compatible, so this example uses the AWS SDK (boto3) to upload media and hand back presigned playback URLs for your voice flows.

## How It Works

```
  Client (multipart upload)
        │
        ▼
  ┌──────────────────────┐        boto3 (S3 protocol)        ┌─────────────────────────┐
  │ Flask app (app.py)    │ ────────────────────────────────► │ Telnyx Cloud Storage     │
  │  /setup /upload        │                                   │ {region}.telnyx          │
  │  /media /ivr-config    │ ◄──── presigned GET URL ───────── │  cloudstorage.com        │
  └──────────┬───────────┘                                    └─────────────────────────┘
             │ presigned URL
             ▼
  TeXML <Play> / Call Control playback_audio
```

## Telnyx Products Used

- **Cloud Storage** — S3-compatible object storage for IVR prompts, hold music, and other voice media
- **Voice** — consume presigned URLs in a TeXML `<Play>` verb or a Call Control `playback_audio` command

## How Telnyx Cloud Storage Auth Works

Telnyx Cloud Storage speaks the S3 protocol, so you connect with boto3 — not a REST API. Two Telnyx-specific details:

1. **Region-scoped endpoint** — `https://{region}.telnyxcloudstorage.com`, where region is one of `us-central-1`, `us-east-1`, `us-west-1`, `eu-central-1`.
2. **Auth** — your Telnyx API key is used as **both** the AWS access key and the secret key.

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

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)
- (Optional, to play media on calls) A [Voice / Call Control Application](https://portal.telnyx.com/call-control/applications) or TeXML application

## Step 1: Set Up the Project

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/cloud-storage-media-cdn-python
cp .env.example .env
pip install -r requirements.txt
```

Edit `.env` with your Telnyx API key. Set `TELNYX_STORAGE_REGION` to the region your bucket lives in, and (optionally) override `BUCKET_NAME` and `PRESIGN_TTL_SECONDS`.

## Step 2: Understand the Code

Everything lives in `app.py`. Here's what each piece does.

### Categories

Media is organized by object-key prefix:

| Category | Purpose |
|----------|---------|
| `ivr_prompts` | IVR greeting and menu prompts |
| `hold_music` | Hold music tracks |
| `announcements` | System announcements |
| `voicemail_greetings` | Voicemail greeting templates |

### Business Logic

- **`presign(key)`** — returns a time-limited GET URL (`PRESIGN_TTL_SECONDS`) for an object, safe to hand to a call flow.
- **`setup_bucket()`** — creates the bucket via `s3.create_bucket`; ignores "already exists" errors so it is idempotent.
- **`upload_media()`** — reads the `file`, `name`, and `category` multipart fields and streams the bytes to Cloud Storage with `s3.upload_fileobj`.
- **`list_media()`** — lists objects with `s3.list_objects_v2`, optionally filtered by category prefix.
- **`get_media_url()`** — `head_object` to confirm the object exists, then returns a presigned URL.
- **`ivr_config()`** — returns presigned URLs for every object in `ivr_prompts` and `hold_music`.

### All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/setup` | Create the bucket |
| `POST` | `/upload` | Upload a media file (multipart) |
| `GET` | `/media` | List media (optional `?category=`) |
| `GET` | `/media/<category>/<name>` | Presigned playback URL for one object |
| `GET` | `/ivr-config` | Presigned URLs for IVR prompts + hold music |
| `GET` | `/health` | Health check |

The upload endpoint streams the client's bytes straight to Cloud Storage:

```python
@app.route("/upload", methods=["POST"])
def upload_media():
    category = request.form.get("category", "ivr_prompts")
    name = request.form.get("name")
    file = request.files.get("file")
    if not name or file is None:
        return jsonify({"error": "multipart fields 'file' and 'name' are required"}), 400
    if category not in CATEGORIES:
        return jsonify({"error": f"category must be one of {list(CATEGORIES)}"}), 400
    key = f"{category}/{name}"
    s3.upload_fileobj(
        file, BUCKET_NAME, key,
        ExtraArgs={"ContentType": file.mimetype or "application/octet-stream"},
    )
    return jsonify({"status": "uploaded", "key": key, "category": category, "url": presign(key)}), 200
```

## Step 3: Run It

```bash
python app.py
```

Server starts on `http://localhost:5000`.

## Step 4: Test It

**Health check:**

```bash
curl http://localhost:5000/health
```

**Create the bucket:**

```bash
curl -X POST http://localhost:5000/setup
```

**Upload a prompt:**

```bash
curl -X POST http://localhost:5000/upload \
  -F file=@welcome-prompt.mp3 \
  -F name=welcome-prompt.mp3 \
  -F category=ivr_prompts
```

**List media:**

```bash
curl "http://localhost:5000/media?category=ivr_prompts" | python3 -m json.tool
```

**Get presigned URLs for a call flow:**

```bash
curl http://localhost:5000/ivr-config | python3 -m json.tool
```

## Step 5: Play Media on a Call

Take a presigned URL from `/ivr-config` or `/media/<category>/<name>` and drop it into your voice flow.

**TeXML:**

```xml
<Response>
  <Play>https://us-central-1.telnyxcloudstorage.com/media-cdn/ivr_prompts/welcome-prompt.mp3?X-Amz-...</Play>
</Response>
```

**Call Control:**

```bash
curl -X POST "https://api.telnyx.com/v2/calls/{call_control_id}/actions/playback_start" \
  -H "Authorization: Bearer $TELNYX_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"audio_url": "https://us-central-1.telnyxcloudstorage.com/media-cdn/ivr_prompts/welcome-prompt.mp3?X-Amz-..."}'
```

## Going to Production

- **Presigned URL lifetime** — tune `PRESIGN_TTL_SECONDS`. URLs must stay valid long enough for the call platform to fetch the audio, but short enough to limit sharing.
- **Authentication** — add API key validation on the `/upload` and `/setup` endpoints.
- **Content validation** — validate file type and size before upload.
- **Monitoring** — add structured logging and health check alerts.
- **Rate limiting** — protect your endpoints from abuse.

## Run

```bash
pip install -r requirements.txt
python app.py
```

## Resources

- [Source code and reference](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/cloud-storage-media-cdn-python/README.md)
- [Cloud Storage quick start](https://developers.telnyx.com/docs/cloud-storage/quick-start)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Telnyx Portal](https://portal.telnyx.com)
