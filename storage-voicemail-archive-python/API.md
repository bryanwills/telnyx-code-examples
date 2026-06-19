## Cloud Storage

Recordings are archived to Telnyx Cloud Storage via its S3-compatible API. The app uses `boto3` against the region endpoint `https://{region}.telnyxcloudstorage.com`, passing the Telnyx API key as both the access key and the secret key. The region is set with the `TELNYX_STORAGE_REGION` env var (default `us-central-1`). On `call.recording.saved`, the MP3 is uploaded with `s3.put_object(...)`. See the [Cloud Storage quick start](https://developers.telnyx.com/docs/cloud-storage/quick-start).

## `POST /webhooks/voice`

Receives Telnyx Call Control webhook events. Called automatically by Telnyx during calls — do not call directly.

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/voice
```

## `GET /voicemails`

List all voicemails.

### Response `200`

Returns the 50 most recent voicemails. Each entry includes the caller, the Cloud Storage object key (`filename`), duration, and timestamp.

```json
{
  "voicemails": [
    {
      "caller": "+12125551234",
      "filename": "voicemail-1718712000-12125551234.mp3",
      "duration": 18,
      "timestamp": "2026-06-18T14:30:00Z"
    }
  ]
}
```

**Try it:**

```bash
curl http://localhost:5000/voicemails
```

---

## `GET /voicemails/search`

Search voicemails.

### Response `200`

Filters stored voicemails by the `caller` query parameter (substring match) and returns the matches.

```json
{
  "results": [
    {
      "caller": "+12125551234",
      "filename": "voicemail-1718712000-12125551234.mp3",
      "duration": 18,
      "timestamp": "2026-06-18T14:30:00Z"
    }
  ]
}
```

**Try it:**

```bash
curl "http://localhost:5000/voicemails/search?caller=2125551234"
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "voicemails": "<string>"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `answering`, `archived`, `ended`, `greeting`, `ok`, `recording`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "error": "invalid request body"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
