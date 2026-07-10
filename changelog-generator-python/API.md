## `POST /generate`

Generate a changelog from a list of commit messages.

### Request

```json
{
  "version": "v1.4.0",
  "repo_name": "billing-service",
  "commits": [
    "feat: add Stripe webhook retry",
    "fix: correct EU VAT calculation"
  ]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `commits` | `array[string]` | **yes** | List of git commit messages |
| `version` | `string` | no | Release version to tag the changelog |
| `repo_name` | `string` | no | Project / repository name |

### Response `200`

```json
{
  "id": "cl-1750280400",
  "version": "v1.4.0",
  "date": "2026-07-15T14:30:00Z",
  "sections": [
    {"heading": "Features", "items": ["Add Stripe webhook retry"]},
    {"heading": "Bug Fixes", "items": ["Correct EU VAT calculation"]}
  ],
  "summary": "Adds resilient Stripe webhook handling and fixes EU VAT.",
  "generated_at": "2026-07-15T14:30:15Z",
  "commit_count": 2
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/generate \
  -H "Content-Type: application/json" \
  -d '{"version":"v1.4.0","commits":["feat: add retry","fix: VAT bug"]}'
```

---

## `POST /generate/from-diff`

Generate a changelog from a git diff.

### Request

```json
{
  "version": "v1.4.1",
  "diff": "diff --git a/app.py b/app.py\n+def retry_send():"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `diff` | `string` | **yes** | Git diff contents (truncated to 8000 chars) |
| `version` | `string` | no | Release version to tag the changelog |

### Response `200`

```json
{
  "id": "cl-1750280401",
  "version": "v1.4.1",
  "sections": [
    {"heading": "Features", "items": ["Add retry_send helper"]}
  ],
  "summary": "Introduces a retry helper for sending messages.",
  "generated_at": "2026-07-15T14:31:00Z"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/generate/from-diff \
  -H "Content-Type: application/json" \
  -d '{"version":"v1.4.1","diff":"+def retry_send():"}'
```

---

## `GET /changelogs`

List all generated changelogs (most recent 50).

### Response `200`

```json
{
  "changelogs": [
    {
      "id": "cl-1750280400",
      "version": "v1.4.0",
      "summary": "Adds resilient Stripe webhook handling."
    }
  ]
}
```

**Try it:**

```bash
curl http://localhost:5000/changelogs
```

---

## `GET /changelogs/<id>`

Get a specific changelog by ID.

### Response `200`

```json
{
  "id": "cl-1750280400",
  "version": "v1.4.0",
  "sections": [
    {"heading": "Features", "items": ["Add Stripe webhook retry"]}
  ],
  "summary": "Adds resilient Stripe webhook handling."
}
```

### Response `404`

```json
{"error": "changelog not found"}
```

**Try it:**

```bash
curl http://localhost:5000/changelogs/cl-1750280400
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "changelogs": 3,
  "version": "1.0.0"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

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
| `404` | Changelog not found |
| `500` | Server error |
