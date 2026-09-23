// ─────────────────────────────────────────────────────────────────────────
// Decision model client — Telnyx hosted decision model (BETA endpoint).
//
// WHY this endpoint instead of an LLM completion: during a real outage the
// report firehose is exactly when you need classification to be fast and
// cheap. This endpoint returns typed, scored answers (choice/score/noul) in
// a single request — 3 questions in ~400 input tokens, 4 output tokens.
//
// Gotchas encoded below, verified against the live endpoint (not assumed):
//   - The response has NO wrapper: `model`, `answers`, `usage` are top-level.
//   - `score` is FRACTIONAL (sum of index × probability, e.g. 2.55), not a
//     clean integer. Callers round to a bucket; we keep the raw float too.
//   - `noul` (yes/no) returns ONLY a 0–1 float. There is NO confidence field
//     on it — any code expecting one is wrong by construction.
//   - `confidence` (on choice/score) is NORMALIZED ENTROPY (1 − H(p)/ln N).
//     The docs explicitly say this is NOT a calibrated probability that the
//     answer is correct. We do not gate any logic on "high confidence =
//     right"; the dashboard's eval panel measures what it actually predicts.
//   - Every question requires `instructions`; unknown request fields are
//     rejected, so this request sends exactly `state` and `questions`.
//   - No SDK needed — plain fetch with a Bearer token.
// ─────────────────────────────────────────────────────────────────────────

import type { HotlineConfigDoc } from "./hotlineConfig";

export const DECISION_MODEL_URL = "https://api.telnyx.com/v2/ai/typesafe/v1/systemone";

export interface DecisionAnswers {
  issue_type: { choice: string; confidence: number };
  severity: { score: number; confidence: number; legend: Record<string, string> };
  is_duplicate: { noul: number };
}

export interface DecisionUsage {
  input_tokens: number;
  output_tokens: number;
}

// The three question TYPES are fixed by the application's needs (a category
// choice, an ordered severity score, and an independent duplicate noul —
// per the docs' guidance on separate noul questions). The OPTIONS are not:
// they are built from the versioned HotlineConfig taxonomy, so categories
// and rubric are data, editable without a redeploy.
export function buildQuestions(config: HotlineConfigDoc): {
  issue_type: { type: "choice"; instructions: string; criteria: Record<string, string> };
  severity: { type: "score"; instructions: string; criteria: string[] };
  is_duplicate: { type: "noul"; instructions: string };
} {
  const criteria: Record<string, string> = {};
  for (const t of config.issue_types) criteria[t.key] = t.model_description;
  return {
    issue_type: {
      type: "choice",
      instructions: "Classify the type of outage being reported.",
      criteria,
    },
    severity: {
      type: "score",
      instructions: "Rate the operational severity of this report.",
      criteria: config.severity_rubric,
    },
    is_duplicate: {
      type: "noul",
      instructions:
        "Given the region's current known active issue (if any), does this report describe the SAME already-known outage rather than a new distinct issue?",
    },
  };
}

/**
 * One classification pass for one report. Throws on transport or shape
 * failure — the caller (RegionAgent) decides how to surface it. Shape
 * validation is deliberately strict here: this is a beta endpoint, and a
 * silent schema drift should fail loudly, not quietly corrupt the dataset.
 */
export async function runDecisionModel(
  state: string,
  questions: ReturnType<typeof buildQuestions>,
  apiKey: string,
): Promise<{ answers: DecisionAnswers; usage: DecisionUsage | null }> {
  const resp = await fetch(DECISION_MODEL_URL, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ state, questions }),
  });

  if (!resp.ok) {
    const detail = await resp.text().catch(() => "");
    throw new Error(`decision model HTTP ${resp.status} ${detail.slice(0, 200)}`);
  }

  const data = (await resp.json()) as {
    answers?: {
      issue_type?: { choice?: string; confidence?: number };
      severity?: { score?: number; confidence?: number; legend?: Record<string, string> };
      is_duplicate?: { noul?: number };
    };
    usage?: DecisionUsage;
  };

  // Shape assertions — see the header note. If the endpoint drifts, we want
  // a 5xx with a server-side log, not a silent null in the SQL history.
  const it = data.answers?.issue_type;
  const sv = data.answers?.severity;
  const dp = data.answers?.is_duplicate;
  if (
    !it?.choice ||
    typeof it.confidence !== "number" ||
    typeof sv?.score !== "number" ||
    typeof sv.confidence !== "number" ||
    typeof dp?.noul !== "number"
  ) {
    throw new Error("decision model response shape drifted");
  }

  return {
    answers: {
      issue_type: { choice: it.choice, confidence: it.confidence },
      severity: { score: sv.score, confidence: sv.confidence, legend: sv.legend ?? {} },
      is_duplicate: { noul: dp.noul },
    },
    usage: data.usage ?? null,
  };
}

/**
 * Build the `state` string for the model: the raw report plus the region's
 * known active issue (from Durable KV) as context. This context is what makes
 * is_duplicate meaningful — measured directly by our ablation probe: the same
 "still out" report scored 0.75 without context vs 0.997 with it.
 */
export function buildModelState(
  text: string,
  region: string,
  active: { issue_type: string | null; first_seen: number; last_seen: number } | null,
): string {
  const known =
    active && active.issue_type
      ? `Known active issue in this region: ${active.issue_type}, first seen ${new Date(active.first_seen).toISOString()}, still active.`
      : "Known active issue in this region: none.";
  return `Caller report from region ${region}: "${text}" ${known}`;
}
