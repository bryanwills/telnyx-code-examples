#!/usr/bin/env node
// ─────────────────────────────────────────────────────────────────────────
// loadgen.mjs — scripted outage "attack" for the Regional Outage Hotline.
//
// WHY a scripted load at all: we can't wait for a real outage on camera, and
// a flat stream of identical reports is a boring demo. This script fires a
// ~13-report scenario that exercises every behavior the dashboard is supposed
// to show: a burst of pile-on reports of one outage, two billing calls that
// should NOT count as outages, a genuinely new degraded-service issue, and a
// distinct critical incident.
//
// Each report carries demo-only ground truth (expected_* fields) that the
// intake endpoint stores alongside the model's answer — that's what powers
// the accuracy/calibration report card later. Labels are judged RELATIVE TO
// THE KV SLOT AT ARRIVAL TIME (the model only ever sees that slot), which is
// why reports fire sequentially with small gaps instead of in parallel.
//
// Usage:
//   node loadgen.mjs --url https://<func>-<org>.telnyxcompute.com \
//        --region 415 [--reset] [--gap 400]
// ─────────────────────────────────────────────────────────────────────────

const args = process.argv.slice(2);
function argValue(name, fallback) {
  const i = args.indexOf(`--${name}`);
  return i >= 0 && args[i + 1] ? args[i + 1] : fallback;
}
function hasFlag(name) {
  return args.includes(`--${name}`);
}

const BASE = argValue("url", "");
const REGION = argValue("region", "415");
const GAP_MS = Number(argValue("gap", "400"));
const DO_RESET = hasFlag("reset");

if (!BASE) {
  console.error("usage: node loadgen.mjs --url https://<func>-<org>.telnyxcompute.com [--region 415] [--reset]");
  process.exit(1);
}

// ── The scenario ──────────────────────────────────────────────────────────
// Ordered so that the KV "known active issue" slot evolves the way a real
// regional incident does: one outage gathers pile-ons, billing noise arrives
// (and must not hijack the slot), a new service-degradation issue takes over,
// then a critical infrastructure incident.
//
// `expected_duplicate: 1` means: judged against the KV slot as it stands
// when this report arrives, this is the SAME already-known outage.
const SCENARIO = [
  // The seed: a major total-outage report.
  { reporter: "sim-a", text: "Our internet has been completely out since this morning. No dial tone, no lights on the modem.", expected_issue_type: "no_service", expected_severity: "Critical", expected_duplicate: 0 },
  // Pile-on burst: same outage from different callers.
  { reporter: "sim-b", text: "Still nothing here either. Third neighbor says the same thing.", expected_issue_type: "no_service", expected_severity: "High", expected_duplicate: 1 },
  { reporter: "sim-c", text: "My service is still out. This has been all day now.", expected_issue_type: "no_service", expected_severity: "High", expected_duplicate: 1 },
  { reporter: "sim-d", text: "Phone and internet both dead in my building since 7am.", expected_issue_type: "no_service", expected_severity: "High", expected_duplicate: 1 },
  // Billing confusion: NOT an outage. Must not become the known active issue.
  { reporter: "sim-e", text: "Why was I charged twice this month? I never asked for this service.", expected_issue_type: "billing", expected_severity: "Low", expected_duplicate: 0 },
  { reporter: "sim-f", text: "My bill doubled and nobody told me. What is going on with my account?", expected_issue_type: "billing", expected_severity: "Low", expected_duplicate: 0 },
  // More pile-ons while the outage is still the known issue.
  { reporter: "sim-g", text: "Is there an outage? Everyone on my street has no service.", expected_issue_type: "no_service", expected_severity: "High", expected_duplicate: 1 },
  { reporter: "sim-h", text: "Called twice already. Still no internet. I work from home and I am losing pay.", expected_issue_type: "no_service", expected_severity: "High", expected_duplicate: 1 },
  // A genuinely NEW, milder issue: intermittent service.
  { reporter: "sim-i", text: "WiFi keeps dropping every few minutes and speeds are terrible tonight.", expected_issue_type: "degraded", expected_severity: "Normal", expected_duplicate: 0 },
  { reporter: "sim-j", text: "Same thing here, WiFi has been cutting out since dinner time.", expected_issue_type: "degraded", expected_severity: "Normal", expected_duplicate: 1 },
  // A distinct critical incident: downed lines. Not the same as the outage.
  { reporter: "sim-k", text: "A utility pole came down on our block and the wires are sparking on the ground.", expected_issue_type: "other", expected_severity: "Critical", expected_duplicate: 0 },
  // The original outage resurfaces — but the KV slot now holds the pole
  // report, so the honest ground truth is "not the same as the known issue".
  // This beat demonstrates the one-slot limitation (full history lives in SQL).
  { reporter: "sim-l", text: "My internet just went out completely a few minutes ago in this area.", expected_issue_type: "no_service", expected_severity: "High", expected_duplicate: 0 },
  // And the slot is back on no_service — a true pile-on once more.
  { reporter: "sim-m", text: "Ours is out too since the pole came down. Really bad out here.", expected_issue_type: "no_service", expected_severity: "High", expected_duplicate: 1 },
];

const BUCKET_LABELS = ["Low", "Normal", "High", "Critical"];

function labelForBucket(n) {
  return BUCKET_LABELS[n] ?? `bucket-${n}`;
}

function short(s, n = 46) {
  return s.length > n ? s.slice(0, n - 1) + "…" : s;
}

async function post(path, body) {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body ?? {}),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(`HTTP ${res.status} ${JSON.stringify(data).slice(0, 160)}`);
  return data;
}

async function main() {
  if (DO_RESET) {
    process.stdout.write("resetting region… ");
    const r = await post(`/debug/reset?region=${REGION}`);
    console.log(`wiped ${r.deleted_reports} report(s)`);
  }

  console.log(`firing ${SCENARIO.length} reports at region ${REGION} (${BASE})`);
  console.log("─".repeat(100));

  for (let i = 0; i < SCENARIO.length; i++) {
    const r = SCENARIO[i];
    try {
      const d = await post(`/intake?region=${REGION}`, r);
      const m = d.model;
      const esc = d.escalated ? " ⚠ ESCALATED" : "";
      const expected = r.expected_duplicate === 1 ? "dup?" : "new?";
      const dupOk = r.expected_duplicate === 1 ? m.is_duplicate >= 0.5 : m.is_duplicate < 0.5;
      const flag = dupOk ? "✓" : "✗";
      console.log(
        `[${String(i + 1).padStart(2)}/${SCENARIO.length}] ${m.issue_type.padEnd(11)} sev=${m.severity_bucket}(${labelForBucket(m.severity_bucket).padEnd(8)}) dup=${m.is_duplicate.toFixed(3)} [${expected}→${flag}] conf=${m.issue_type_confidence.toFixed(3)} tok=${d.usage?.input_tokens}/${d.usage?.output_tokens}${esc}`
      );
      console.log(`        ${short(r.text)}`);
    } catch (e) {
      console.error(`[${i + 1}/${SCENARIO.length}] FAILED: ${e.message}`);
    }
    await new Promise((res) => setTimeout(res, GAP_MS));
  }

  console.log("─".repeat(100));
  const res = await fetch(`${BASE}/debug/state?region=${REGION}`);
  const s = await res.json();
  console.log(`region ${REGION}: ${s.report_count} total, ${s.last_hour_count} in last hour`);
  console.log(`severity: ${s.severity_breakdown.map((b) => `${BUCKET_LABELS[b.severity_bucket]}=${b.count}`).join("  ")}`);
  console.log(`distinct issues: ${s.distinct_issues.map((d) => `${d.issue_type}×${d.count}`).join("  ")}`);
  console.log(`escalations: ${s.escalations.length}`);
  console.log(`active issue (KV): ${s.active_issue ? `${s.active_issue.issue_type} since ${new Date(s.active_issue.first_seen).toISOString()}` : "none"}`);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
