## `POST /experiments`

Create an A/B experiment — run both prompt variants against the same task, return both responses.

### Request

```json
{
  "task": "Write a one-sentence tagline for an edge compute platform.",
  "variant_a": "You are a concise marketing copywriter. Return just the tagline.",
  "variant_b": "You are a technical explainer. Return just the tagline, focus on latency."
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `task` | `string` | **yes** | The task to run against both variants |
| `variant_a` | `string` | **yes** | Prompt A (system prompt) |
| `variant_b` | `string` | **yes** | Prompt B (system prompt) |

### Response `201`

```json
{
  "id": "exp-msf712rs-0",
  "task": "Write a one-sentence tagline for an edge compute platform.",
  "variant_a": {
    "prompt": "You are a concise marketing copywriter. Return just the tagline.",
    "response": "Real-time compute, right where your data lives."
  },
  "variant_b": {
    "prompt": "You are a technical explainer. Return just the tagline, focus on latency.",
    "response": "Execute code milliseconds from your users to eliminate network latency."
  },
  "votes_a": 0,
  "votes_b": 0,
  "status": "open",
  "created_at": "2026-08-04T21:51:55Z"
}
```

**Try it:**

```bash
curl -X POST https://edge-prompt-ab-tester-<id>.telnyxcompute.com/experiments \
  -H "Content-Type: application/json" \
  -d '{"task":"Your task here","variant_a":"Prompt A","variant_b":"Prompt B"}'
```

---

## `POST /experiments/<id>/vote`

Vote for a variant. Votes accumulate until the experiment is closed.

### Request

```json
{
  "variant": "a"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `variant` | `string` | **yes** | `"a"` or `"b"` |

### Response `200`

```json
{
  "id": "exp-msf712rs-0",
  "votes_a": 1,
  "votes_b": 0,
  "status": "open"
}
```

**Try it:**

```bash
curl -X POST https://edge-prompt-ab-tester-<id>.telnyxcompute.com/experiments/exp-msf712rs-0/vote \
  -H "Content-Type: application/json" \
  -d '{"variant":"b"}'
```

---

## `POST /experiments/<id>/close`

Close the experiment — no more votes accepted.

### Response `200`

```json
{
  "id": "exp-msf712rs-0",
  "status": "closed",
  "votes_a": 2,
  "votes_b": 1
}
```

**Try it:**

```bash
curl -X POST https://edge-prompt-ab-tester-<id>.telnyxcompute.com/experiments/exp-msf712rs-0/close
```

---

## `GET /experiments`

List experiments (most recent first).

### Query Parameters

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `limit` | `integer` | `20` | Max results (1-50) |

### Response `200`

```json
{
  "experiments": [
    {
      "id": "exp-msf712rs-0",
      "task": "Write a tagline",
      "votes_a": 2,
      "votes_b": 1,
      "status": "open",
      "created_at": "..."
    }
  ]
}
```

**Try it:**

```bash
curl https://edge-prompt-ab-tester-<id>.telnyxcompute.com/experiments
```

---

## `GET /experiments/<id>`

Get a specific experiment with its variants and vote counts.

### Response `200`

```json
{
  "id": "exp-msf712rs-0",
  "task": "Write a tagline",
  "variant_a": {"prompt": "...", "response": "..."},
  "variant_b": {"prompt": "...", "response": "..."},
  "votes_a": 2,
  "votes_b": 1,
  "status": "open"
}
```

### Response `404`

```json
{"error": "experiment not found"}
```

**Try it:**

```bash
curl https://edge-prompt-ab-tester-<id>.telnyxcompute.com/experiments/exp-msf712rs-0
```

---

## `GET /stats`

Cumulative stats across all experiments.

### Response `200`

```json
{
  "total_experiments": 3,
  "open_experiments": 2,
  "closed_experiments": 1,
  "total_votes": 15,
  "leader": "variant_a",
  "leader_votes": 9
}
```

**Try it:**

```bash
curl https://edge-prompt-ab-tester-<id>.telnyxcompute.com/stats
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
curl https://edge-prompt-ab-tester-<id>.telnyxcompute.com/health/liveness
```

---

## Error Handling

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `201` | Experiment created |
| `400` | Bad request — missing fields |
| `404` | Experiment not found or closed |
| `500` | Server error (inference failed) |
