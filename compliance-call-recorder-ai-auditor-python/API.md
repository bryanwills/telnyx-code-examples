## `POST /webhooks/voice`

Receives Telnyx Call Control webhook events. Called automatically by Telnyx during calls — do not call directly.

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/voice
```

## `GET /audit/results`

Get audit results.

### Response `200`

```json
{
  "error": "No payload"
}
```

**Try it:**

```bash
curl http://localhost:5000/audit/results
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "total_audited": "example-value",
  "compliance_rate": "example-value",
  "violations": "example-value",
  "avg_risk_score": "example-value",
  "recent_results": "example-value",
  "recent_violations": "example-value"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Recording Storage (Telnyx Cloud Storage)

When a `call.recording.saved` event arrives, the app downloads the recording from Telnyx and archives it in Telnyx Cloud Storage. Storage is **not** a REST call — it uses the S3-compatible API via the AWS S3 SDK (`boto3`):

- **Endpoint**: `https://{region}.telnyxcloudstorage.com`, where `{region}` comes from the `TELNYX_STORAGE_REGION` env var (`us-central-1`, `us-east-1`, `us-west-1`, `eu-central-1`; defaults to `us-central-1`).
- **Authentication**: S3 SigV4 with your Telnyx API key supplied as **both** the access key and the secret key.
- **Operation**: `s3.put_object(Bucket=STORAGE_BUCKET, Key=..., Body=..., ContentType="audio/mpeg")`. Objects are keyed as `recordings/YYYY/MM/DD/{call_control_id}.mp3`.

Uploads are skipped when `STORAGE_BUCKET` is unset. See the [Cloud Storage quickstart](https://developers.telnyx.com/docs/cloud-storage/quick-start).

## Status Values

Records use these status values: `call_ended`, `event_received`, `ok`, `recording`, `recording_saved`, `tracking`, `transcribing`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "status": "ok",
  "calls_tracking": "example-value",
  "total_audited": "example-value"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
