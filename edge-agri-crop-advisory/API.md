## `POST /advisory`

Classify a crop issue and return a structured advisory with treatment recommendation.

### Request

```json
{
  "description": "My corn has yellow streaks with dark brown spots. About 30% of plants affected."
}
```

Or with a URL:

```json
{
  "url": "https://extension.umn.edu/news/something-about-aphids"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `description` | `string` | conditional | Farmer's description of the issue (min 20 chars) |
| `url` | `string` | conditional | URL to fetch and analyze instead |

**Provide at least one of `description` or `url`.**

### Response `201`

```json
{
  "id": "adv-msf1zxyc-0",
  "farmer_description": "My corn has yellow streaks...",
  "source": "text",
  "crop_type": "corn",
  "issue_type": "disease",
  "severity": "medium",
  "confidence": 0.7,
  "recommendation": "Apply a foliar fungicide and scout weekly.",
  "escalate": false,
  "generated_at": "2026-08-04T19:31:04Z"
}
```

With escalation (critical severity):

```json
{
  "issue_type": "locust swarm",
  "severity": "critical",
  "escalate": true,
  "escalated_to": "agronomist-on-call"
}
```

**Try it:**

```bash
curl -X POST https://edge-agri-crop-advisory-<id>.telnyxcompute.com/advisory \
  -H "Content-Type: application/json" \
  -d '{"description":"Tomato leaves have holes all over them. I can see green caterpillars."}'
```

---

## `GET /advisories`

List recent advisories (most recent first).

### Query Parameters

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `limit` | `integer` | `20` | Max results (1-50) |

### Response `200`

```json
{
  "advisories": [
    {
      "id": "adv-msf1zxyc-0",
      "crop_type": "corn",
      "issue_type": "disease",
      "severity": "medium",
      "escalate": false,
      "generated_at": "..."
    }
  ]
}
```

**Try it:**

```bash
curl https://edge-agri-crop-advisory-<id>.telnyxcompute.com/advisories
```

---

## `GET /advisories/<id>`

Get a specific advisory by ID.

### Response `200`

```json
{
  "id": "adv-msf1zxyc-0",
  "crop_type": "corn",
  "issue_type": "disease",
  "severity": "medium",
  "farmer_description": "...",
  "recommendation": "..."
}
```

### Response `404`

```json
{"error": "advisory not found"}
```

**Try it:**

```bash
curl https://edge-agri-crop-advisory-<id>.telnyxcompute.com/advisories/adv-msf1zxyc-0
```

---

## `GET /stats`

Cumulative advisory statistics.

### Response `200`

```json
{
  "total_advisories": 8,
  "by_issue_type": {
    "disease": 3,
    "pest": 2,
    "water": 2,
    "nutrient": 1
  },
  "by_severity": {
    "low": 1,
    "medium": 3,
    "high": 2,
    "critical": 2
  },
  "escalations": 2,
  "recent_crop_types": ["corn", "soybean", "wheat"]
}
```

**Try it:**

```bash
curl https://edge-agri-crop-advisory-<id>.telnyxcompute.com/stats
```

---

## `GET /health/{liveness,readiness}`

Health check endpoints.

### Response `200`

```
ok
```

**Try it:**

```bash
curl https://edge-agri-crop-advisory-<id>.telnyxcompute.com/health/liveness
curl https://edge-agri-crop-advisory-<id>.telnyxcompute.com/health/readiness
```

---

## Error Handling

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `201` | Advisory created |
| `400` | Bad request — missing description/url, description too short |
| `404` | Advisory not found |
| `500` | Server error (fetch or inference failed) |
