# API Reference — Regional Outage-Reporting Hotline

All routes are served by the deployed Edge Compute function at
`https://edge-outage-hotline-typescript-<id>.telnyxcompute.com`.

## `POST /intake?region=<r>`

Classify one report with the decision model, persist it in the region actor's SQL, apply the KV dedupe policy, and set the escalation flag. The whole KV-read → classify → SQL-write → KV-write sequence runs inside one actor method, so it is serialized per region.

**Query params**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `region` | string | yes | 2–8 URL-safe chars (e.g. `415`) — keys the actor instance |
| `debug` | `"1"` | no | Include error `detail` in the response (demo affordance) |

**Request body**

```json
{
  "reporter": "sim-a",
  "text": "Our internet has been completely out since this morning.",
  "expected_issue_type": "no_service",
  "expected_severity": "Critical",
  "expected_duplicate": 0
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | yes | The caller's report |
| `reporter` | string | no | Display name (defaults to `anonymous`) |
| `expected_issue_type` | `"no_service" \| "degraded" \| "billing" \| "other"` | no | Demo-only ground truth, stored for eval |
| `expected_severity` | `"Low" \| "Normal" \| "High" \| "Critical"` | no | Demo-only ground truth |
| `expected_duplicate` | `0 \| 1` | no | Demo-only ground truth, judged against the KV slot at arrival time |

**Response `200`**

```json
{
  "region": "415",
  "id": 4,
  "report_count": 13,
  "schema_version": 1,
  "category": { "key": "no_service", "label": "No service", "is_outage": true },
  "judged_duplicate": false,
  "active_issue": {
    "issue_type": "no_service",
    "first_seen": 1790107956527,
    "last_seen": 1790107964170
  },
  "model": {
    "issue_type": "no_service",
    "issue_type_confidence": 0.9918,
    "severity_raw": 2.5534,
    "severity_bucket": 3,
    "severity_confidence": 0.4870,
    "is_duplicate": 0.0032,
    "confidence": 0.9918
  },
  "escalated": true,
  "kv_updated": true,
  "usage": { "input_tokens": 413, "output_tokens": 4, "cached_input_tokens": 0 }
}
```

| Field | Description |
|-------|-------------|
| `model.severity_raw` | The model's fractional score (Σ index × probability). Kept raw in SQL for eval. |
| `model.severity_bucket` | `round(severity_raw)` clamped to the active rubric's range (0–N-1) |
| `model.is_duplicate` | `noul` — a plain 0–1 float. **No confidence field exists on this answer.** |
| `model.confidence` | Normalized entropy (1 − H(p)/ln N) — explicitly NOT a calibrated probability of correctness |
| `category` | The config taxonomy entry matched to the model's `choice` |
| `judged_duplicate` | True when `is_duplicate ≥ escalation.max_duplicate_noul` from the active config |
| `schema_version` | Version of the taxonomy this report was classified under |
| `escalated` | True when the category is `escalatable` AND `is_outage` AND `severity_bucket ≥ escalation.min_severity_bucket` AND not `judged_duplicate` |
| `kv_updated` | False when the category lacks `may_own_kv_slot` |

**Errors**: `400` (bad region/body) · `502` (decision-model or storage failure; `?debug=1` adds `detail`).

## `GET /api/summary?regions=415,212`

Fan-out across region actors (per-actor SQL is private, so aggregation is per-actor).

**Response `200`**

```json
{
  "regions": [
    {
      "region": "415",
      "summary": {
        "report_count": 13,
        "last_hour_count": 13,
        "severity_breakdown": [ { "severity_bucket": 2, "count": 10 }, { "severity_bucket": 3, "count": 1 } ],
        "distinct_issues": [
          { "issue_type": "no_service", "count": 8, "first_seen": "2026-09-22T20:29:38Z", "last_seen": "2026-09-22T20:30:05Z" }
        ],
        "escalations": [ { "id": 1, "reporter": "sim-a", "raw_report": "...", "issue_type": "no_service", "severity_bucket": 2 } ],
        "recent_reports": [ { "id": 13, "received_at": "...", "reporter": "...", "raw_report": "...", "issue_type": "no_service", "severity_bucket": 2, "is_duplicate_flag": 1, "escalated": 0 } ],
        "active_issue": { "issue_type": "no_service", "first_seen": 1790107956527, "last_seen": 1790107964170 }
      }
    }
  ]
}
```

## `GET /api/eval?region=<r>`

The model's measured report card for one region, computed only over rows carrying ground truth (`expected_*`).

**Response `200`**

```json
{
  "region": "415",
  "eval": {
    "labeled_issue_type": 13,
    "issue_type_correct": 13,
    "issue_type_confusion": [ { "expected": "no_service", "actual": "no_service", "count": 8 } ],
    "labeled_severity": 13,
    "severity_exact": 9,
    "severity_within_one": 12,
    "severity_mae": 0.3846,
    "labeled_duplicate": 13,
    "duplicate_accuracy": [ { "threshold": 0.2, "correct": 9 }, { "threshold": 0.35, "correct": 9 }, { "threshold": 0.5, "correct": 9 }, { "threshold": 0.7, "correct": 10 } ],
    "confidence_bins": [ { "range": "0.0–0.5", "total": 0, "correct": 0 }, { "range": "0.5–0.8", "total": 1, "correct": 1 }, { "range": "0.8–0.95", "total": 4, "correct": 4 }, { "range": "0.95–1.0", "total": 8, "correct": 8 } ]
  }
}
```

Duplicate accuracy at threshold `t`: prediction is "duplicate" when `noul ≥ t`; correct counts where that prediction matches `expected_duplicate`.

## `GET /` · `GET /index.html`

The incident dashboard (HTML). Client-side JS polls `/api/summary` and `/api/eval` every 4s when **live** is on.

## `GET /api/config` · `GET /admin/config`

The active classification taxonomy (version, issue categories with policy flags, severity rubric, escalation thresholds).

```json
{
  "config": {
    "version": 3,
    "issue_types": [
      { "key": "no_service", "label": "No service", "model_description": "Complete loss of service",
        "is_outage": true, "may_own_kv_slot": true, "escalatable": true }
    ],
    "severity_rubric": ["Low", "Normal", "High", "Critical"],
    "escalation": { "min_severity_bucket": 2, "max_duplicate_noul": 0.35 }
  }
}
```

## `PUT /admin/config`

Replace the taxonomy — takes effect on the **next** report, no redeploy. Body: a full config doc. Validated against the decision-model endpoint's limits (2–64 categories, 2–64 rubric entries) before storing; `version` is bumped if it matches the current one. Historical rows keep their `schema_version`; categories absent from the new config but present in history display as "(retired)" on the dashboard.

**Response `200`**: `{ "config": { ...stored doc... } }` · **Errors**: `400` with `{"error": "invalid config", "errors": [...]}`.

## `GET /debug/envcheck`

`{ "has_key": true, "key_len": 58 }` — reports secret presence/length only, never the value.

## `POST /debug/ingest?region=<r>`

Store a raw report **without** classification (model columns NULL). Body: `{"reporter": "...", "text": "..."}`. Response: `{ region, id, report_count, active_issue }`.

## `POST /debug/reset?region=<r>`

Wipe the region's demo state (SQL rows + KV). Response: `{ "region": "415", "deleted_reports": 13 }`.

## `GET /health/liveness` · `GET /health/readiness`

Plain `ok` for load balancers.

## Upstream: decision model endpoint

`POST https://api.telnyx.com/v2/ai/typesafe/v1/systemone` — Bearer auth. Request sends exactly `{"state": string, "questions": {...}}` (unknown fields are rejected; every question requires `instructions`; 1–64 questions; 2–64 options per choice/score). Response has no wrapper: `{ "model": "...", "answers": {...}, "usage": {...} }`. See `src/decisionModel.ts` for the encoded gotchas (fractional `score`, `noul` with no confidence, entropy-based `confidence`).
