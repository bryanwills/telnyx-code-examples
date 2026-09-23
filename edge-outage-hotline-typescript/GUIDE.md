# Guide — Regional Outage-Reporting Hotline

This guide walks through the demo end to end: what it is, how it works, how to run it, and — most importantly — what the decision model actually did when we measured it.

## The idea

Callers phone in (or, in this version, scripts simulate) reports of a service outage. Instead of keying state by **caller**, the demo keys a Stateful Actor by **region** — e.g. one actor per area code. That one design choice makes every Telnyx Edge Compute primitive earn its place:

- Many different callers' reports land in the **same actor**, so there is something to aggregate.
- **SQLDB** is needed for real relational queries: report counts, "how many in the last hour", severity breakdowns, deduplicated issue lists.
- **Durable KV** holds the region's "current known active issue" — the hot context fed into the classifier so you never hit SQL just to ask "have we seen this before?".
- The **decision model** endpoint classifies each report in one cheap request (3 questions, ~400 input tokens, 4 output tokens) — exactly what you want during a call-volume spike, instead of an LLM call per report.

## The two storage layers (and why both exist)

| Layer | Content | Question it answers |
|-------|---------|--------------------|
| SQL (`ctx.storage.sql`) | Every report, with the model's raw + rounded answers, escalation flag, and demo ground truth | "How many reports in the last hour?" "What's the severity mix?" "Which issues are distinct?" |
| KV (`ctx.storage.get/put`) | One `active_issue` blob: `{issue_type, first_seen, last_seen}` | "What's the currently known issue in this region?" — read on EVERY incoming report |

KV write policy (application logic, not the model):

1. Same `issue_type` as the known issue → bump `last_seen` (the pile-on window grows).
2. New `issue_type` → overwrite the slot.
3. `billing` → never touches the slot. A billing complaint is not an outage; letting it own the slot would poison dedupe context for every later real outage report.

## Run it

```bash
# 1. Secrets (never committed)
telnyx-edge secrets add TELNYX_API_KEY "KEY0123..."

# 2. Deploy (first time: create the function, copy the [edge_compute] block into telnyx.toml)
npm install
telnyx-edge ship
# → https://edge-outage-hotline-typescript-<id>.telnyxcompute.com

# 3. Fire the labeled load and watch the dashboard
node loadgen.mjs --url https://edge-outage-hotline-typescript-<id>.telnyxcompute.com --region 415 --reset
```

Open the URL in a browser. The dashboard auto-refreshes every 4 seconds; fire the load script while it's on screen and watch it move.

## The 13-report scenario

`loadgen.mjs` fires a scripted incident arc at one region, each report labeled with ground truth:

1. **Seed**: total outage (`no_service`, Critical) → escalates
2. **Pile-on burst ×3**: neighbors confirm → duplicate (≥ 0.98), no escalation
3. **Billing noise ×2**: complaints about double charges → classified `billing`, do NOT own the KV slot, do not escalate
4. **More pile-ons ×2**
5. **New mild issue**: intermittent WiFi (`degraded`) → takes over the KV slot
6. **Its own pile-on ×1** → duplicate of `degraded`
7. **Distinct critical incident**: downed utility pole (`other`, Critical) → the honest edge case
8. **The original outage resurfaces** — but the slot now holds the pole report, so it's judged against the wrong context (see findings below)
9. **A true pile-on to close** → duplicate of the resurfaced `no_service`

Labels are judged **relative to the KV slot at arrival time** — the model only ever sees that slot — which is why the script fires sequentially with ~350ms gaps instead of in parallel.

## What the decision model actually did (measured)

Run the scenario and `GET /api/eval?region=415` (or read the report card on the dashboard). From a real run:

- **Issue type: 13/13.** The confusion matrix was entirely diagonal — including `billing` vs `other`, the pair most classifiers smear together.
- **Severity: MAE 0.38** on the 0–3 scale; exact-bucket 69%, within-one-bucket 92%.
- **Duplicate: the threshold matters.** Accuracy was 69% at thresholds 0.2–0.5 and 77% at 0.7. `noul` has no confidence field, so the sweep IS the honest way to pick the operating point.
- **Confidence calibration:** the entropy-based `confidence` was monotone with correctness at n=13 — but that's a small sample. The endpoint's docs explicitly say this confidence is *not* a calibrated probability of correctness; the demo measures it rather than assuming it.

### Findings worth telling on camera

1. **Severity anchors on context.** With a known `no_service` issue in the KV context, even billing reports scored ~High. Without context (the raw-curl probe in this guide), the same billing text scored 0.89 → Low/Normal. The severity question keys off the state string, not just the report.
2. **A billing complaint escalated on the first run.** High severity + near-zero `is_duplicate` tripped the naive rule. The model classified it correctly as `billing`; the *application logic* was the bug. This demo now gates escalation on the model's own issue type. This is the demo's core lesson: the model makes judgments, your code makes decisions.
3. **Related-but-distinct issues get merged by dedupe.** "WiFi keeps dropping" during a known outage scored `is_duplicate` 0.93 — arguably correct (it's plausibly the same root cause), arguably wrong (different symptom). The report card makes that debate visible instead of hiding it.
4. **The one-slot design forgets older issues.** When the original outage resurfaced after the pole report took the slot, the model judged it against the wrong context (`is_duplicate` 0.915 for a report that was NOT about the pole). SQL retains full history; KV only knows the newest issue. That trade-off is deliberate and stated, not hidden.

### The ablation probe (2 curl calls, big payoff)

Send the identical "still out" report twice — once with, once without the KV context in the `state`:

- **Without** context: `is_duplicate` = **0.7549**
- **With** context (`no_service`, still active): `is_duplicate` = **0.9975**

The KV blob measurably sharpens duplicate detection — that's the evidence that Durable KV is doing real work here, not decorating the architecture.

## State durability proof (on-camera moment)

1. `POST /debug/ingest?region=415` twice → the second response returns the same `active_issue.first_seen` (KV survived across calls) with a bumped `last_seen`.
2. `telnyx-edge ship` (redeploy) → `GET /debug/state?region=415` → same `first_seen`, same rows. State survives deploys.
3. `GET /debug/state?region=212` → empty. Different actor, fully isolated SQL + KV.

## Wire up a real phone (stretch)

The same intake endpoint accepts reports from anywhere — including a Telnyx AI Assistant. Point an assistant's webhook tool at `POST /intake?region=415` with the caller's transcribed report, and callers can literally phone in outage reports. In Telnyx's "brain vs hands" framing: the AI Assistant is the *hands* (talks to the human caller), and the Edge Compute actor is the *brain* (classifies, aggregates, escalates). See the main README for the recommended path.

## How the docs map to the code

The [Decision Models (beta)](https://developers.telnyx.com/docs/inference/decision-models) page has two "how to use this" sections; this demo implements both:

**"Choose question types"** → `QUESTION_PAYLOAD` in `src/decisionModel.ts`:

- `issue_type` is a **`choice`** question (criteria `{no_service, degraded, billing, other}`) — the doc's "selects one option" type.
- `is_duplicate` is a **`noul`** question — the doc says to use separate `noul` questions for independent conditions; "is this the same already-known outage?" is exactly that, so it's its own question rather than a fifth choice option. It returns a bare 0–1 float with no confidence field.
- `severity` is a **`score`** question (ordered `["Low","Normal","High","Critical"]`).
- The whole payload mirrors the docs' support-incident example (`team`/`production_incident`/`urgency`) with different labels.

**"Use scores in application logic"** → `intakeReport` in `src/regionAgent.ts`:

- The fractional `score` (Σ index × probability) is **never used as an array index directly** — the doc's explicit warning. The application-specific rule here: store the raw float for eval, and round+clamp only for the alerting bucket.
- Option scores are "not calibrated probabilities that a decision is correct" — so **no code path trusts `confidence`**. Escalation keys on the chosen `issue_type`, the rounded bucket, and the `noul` threshold. Confidence is only measured (against ground truth) in `/api/eval`.
- The doc's "choose review thresholds using representative examples" is embodied by the threshold sweep and the escalation-rule evolution: the first load run exposed a billing complaint escalating; the rule now requires the model's own `issue_type ≠ billing`.

## The taxonomy is data, not code

The categories the model classifies into — and the policy attached to them — live in a versioned config (`HotlineConfig` actor), editable at runtime via `PUT /admin/config`:

- Each category carries `is_outage`, `may_own_kv_slot`, and `escalatable` flags. The escalation rule and the KV dedupe policy read these flags — there is no hardcoded category name anywhere in application logic.
- Every report row is stamped with the `schema_version` it was classified under, so history stays interpretable when the taxonomy changes.
- The dashboard's region-wise table derives its columns from the active config; categories that only exist in history render as "(retired)".
- Seeded config reproduces the original behavior exactly — the refactor was verified as a behavioral no-op before the flags were exercised.

The payoff was a real fix: the downed-pole report that classified as `other` (0.62 confidence, failed to escalate) became a new `power_outage` category (0.99 confidence, escalated) after a single `PUT` — no redeploy. When a classifier underperforms, the first question is now "is the taxonomy missing an option?" rather than "how do we tune the model?"

## Design notes for reuse

- **Actor keying**: `env.REGIONS.idFromName("region-<sanitized>")` — actor names are Dapr-safe (letters, digits, dots, dashes), so sanitize region input.
- **Serialization**: actor method calls serialize per instance — the KV read-modify-write inside `intakeReport` cannot interleave across concurrent reports.
- **Private SQL**: per-actor SQL is private by design; cross-region aggregation is a fan-out (`/api/summary`), and per-region evaluation is per-actor (`/api/eval`).
- **Beta endpoint discipline**: the decision-model client validates the response shape on every call — a silent schema drift should fail loudly, not corrupt the dataset.

## Troubleshooting

See the main README's table. Quick pointers: 401 from the model → secret not set; 409 on ship → previous ship still running; empty report card → run the load script.
