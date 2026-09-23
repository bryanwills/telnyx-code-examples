import { StatefulActor } from "@telnyx/edge-runtime";

// ─────────────────────────────────────────────────────────────────────────
// HotlineConfig — one shared actor ("global") holding the VERSIONED
// classification taxonomy that drives everything downstream.
//
// WHY config, not code: the issue categories carry POLICY (can a category
// escalate? may it own the region's known-issue slot?), and policy belongs
// in data, editable without a redeploy. The code below encodes only the
// mechanics: validate, store, serve.
//
// Seeding guarantees zero behavior change: DEFAULT_CONFIG is exactly what
// was previously hardcoded (4 categories, 4-bucket rubric, 0.35 threshold).
// ─────────────────────────────────────────────────────────────────────────

export interface IssueTypeConfig {
  key: string; // stable identifier stored on report rows (never rename, use aliases)
  label: string; // human display name (dashboard, voice confirmations)
  model_description: string; // the `criteria` value sent to the decision model
  is_outage: boolean; // false = not actually a service outage (e.g. billing)
  may_own_kv_slot: boolean; // may this category become the region's "known active issue"
  escalatable: boolean; // may reports of this category ever trigger escalation
}

export interface HotlineConfigDoc {
  version: number;
  issue_types: IssueTypeConfig[];
  severity_rubric: string[];
  escalation: {
    min_severity_bucket: number;
    max_duplicate_noul: number;
  };
  /**
   * Per-token rates used to estimate spend. WHY config: there is no pricing
   * API for the managed decision model (verified — /v2/prices 404s, and the
   * published inference rate list has no managed-model entry while it's in
   * beta), so the rate lives here and stays clearly labeled as an estimate
   * until billing reveals the real one.
   */
  pricing: {
    currency: string;
    input_per_mtok: number;
    output_per_mtok: number;
    source: string;
  };
}

// Seeded with today's behavior so the refactor is a no-op on deploy.
export const DEFAULT_CONFIG: HotlineConfigDoc = {
  version: 1,
  issue_types: [
    {
      key: "no_service",
      label: "No service",
      model_description: "Complete loss of service",
      is_outage: true,
      may_own_kv_slot: true,
      escalatable: true,
    },
    {
      key: "degraded",
      label: "Degraded",
      model_description: "Slow or intermittent service",
      is_outage: true,
      may_own_kv_slot: true,
      escalatable: true,
    },
    {
      key: "billing",
      label: "Billing",
      model_description: "Not actually an outage - billing/account confusion",
      is_outage: false,
      may_own_kv_slot: false,
      escalatable: false,
    },
    {
      key: "other",
      label: "Other",
      model_description: "Doesn't fit the above",
      is_outage: true,
      may_own_kv_slot: true,
      escalatable: true,
    },
  ],
  severity_rubric: ["Low", "Normal", "High", "Critical"],
  escalation: { min_severity_bucket: 2, max_duplicate_noul: 0.35 },
  pricing: {
    currency: "USD",
    // MEASURED from actual billing (not estimated): the managed decision
    // model bills under its own cost code `classifier-latest`, visible in
    // GET /v2/usage_reports?product=inference&dimensions=record_type,model.
    // Sep 22: 42 calls, 19,516 in / 168 out tokens, $0.0118 billed
    // Sep 23: 2 calls, 922 in / 8 out tokens, $0.0006 billed
    // => ~$0.605/1M input tokens (output contribution <1%, unmeasurable at
    // this sample size — kept at the underlying model's published rate).
    // NOTE: ~4.5× the published glm-5.3-flash rate ($0.135/M) — that managed
    // premium is worth flagging to the endpoint team.
    input_per_mtok: 0.605,
    output_per_mtok: 0.45,
    source:
      "Measured from actual billing via the usage-reports API (cost code classifier-latest): $0.0118/42 calls + $0.0006/2 calls ⇒ ~$0.605/1M input tokens. Output rate unmeasurable at this sample size.",
  },
};

/** Validate a candidate config against the decision-model endpoint's limits
 * (1-64 questions, 2-64 options per choice/score) and internal invariants. */
export function validateConfig(doc: unknown): { ok: boolean; errors: string[]; value?: HotlineConfigDoc } {
  const errors: string[] = [];
  if (typeof doc !== "object" || doc === null) return { ok: false, errors: ["config must be an object"] };
  const d = doc as Partial<HotlineConfigDoc>;

  if (!Array.isArray(d.issue_types) || d.issue_types.length < 2 || d.issue_types.length > 64) {
    errors.push("issue_types must have 2-64 entries (decision-model choice limit)");
  }
  const seen = new Set<string>();
  for (const t of d.issue_types ?? []) {
    if (!t || typeof t.key !== "string" || !/^[a-z0-9_]{1,64}$/.test(t.key)) {
      errors.push(`invalid issue_types key: ${JSON.stringify(t?.key)}`);
    } else if (seen.has(t.key)) {
      errors.push(`duplicate issue_types key: ${t.key}`);
    }
    seen.add(t?.key ?? "");
    if (!t || typeof t.label !== "string" || !t.label.trim()) errors.push(`issue_types[${t?.key}] needs a label`);
    if (!t || typeof t.model_description !== "string" || !t.model_description.trim())
      errors.push(`issue_types[${t?.key}] needs model_description`);
    for (const flag of ["is_outage", "may_own_kv_slot", "escalatable"] as const) {
      if (!t || typeof t[flag] !== "boolean") errors.push(`issue_types[${t?.key}].${flag} must be a boolean`);
    }
  }

  if (!Array.isArray(d.severity_rubric) || d.severity_rubric.length < 2 || d.severity_rubric.length > 64) {
    errors.push("severity_rubric must have 2-64 entries");
  } else if (d.severity_rubric.some((s) => typeof s !== "string" || !s.trim())) {
    errors.push("severity_rubric entries must be non-empty strings");
  }

  const esc = d.escalation;
  if (!esc || typeof esc !== "object") {
    errors.push("escalation object is required");
  } else {
    const rubricLen = d.severity_rubric?.length ?? 4;
    if (!Number.isInteger(esc.min_severity_bucket) || esc.min_severity_bucket < 0 || esc.min_severity_bucket >= rubricLen) {
      errors.push(`escalation.min_severity_bucket must be an integer in [0, ${rubricLen - 1}]`);
    }
    if (typeof esc.max_duplicate_noul !== "number" || esc.max_duplicate_noul < 0 || esc.max_duplicate_noul > 1) {
      errors.push("escalation.max_duplicate_noul must be a number in [0, 1]");
    }
  }

  // pricing is optional — if absent, get() falls back to DEFAULT pricing.
  if (d.pricing !== undefined && d.pricing !== null) {
    const p = d.pricing as Partial<HotlineConfigDoc["pricing"]>;
    if (typeof p.currency !== "string" || !p.currency.trim()) errors.push("pricing.currency must be a string");
    for (const field of ["input_per_mtok", "output_per_mtok"] as const) {
      if (typeof p[field] !== "number" || (p[field] as number) < 0) {
        errors.push(`pricing.${field} must be a non-negative number`);
      }
    }
    if (typeof p.source !== "string" || !p.source.trim()) errors.push("pricing.source must describe where the rate came from");
  }

  if (errors.length) return { ok: false, errors };
  const value: HotlineConfigDoc = {
    version: typeof d.version === "number" && Number.isInteger(d.version) && d.version > 0 ? d.version : 1,
    issue_types: d.issue_types as IssueTypeConfig[],
    severity_rubric: d.severity_rubric as string[],
    escalation: esc as HotlineConfigDoc["escalation"],
    pricing: d.pricing ?? DEFAULT_CONFIG.pricing,
  };
  return { ok: true, errors, value };
}

export class HotlineConfig extends StatefulActor {
  async get(): Promise<HotlineConfigDoc> {
    const doc = await this.ctx.storage.get<HotlineConfigDoc>("config");
    if (!doc) return DEFAULT_CONFIG;
    // Backward-compat merge: docs stored before pricing existed get the
    // default pricing block so cost math never breaks on an old config.
    return { ...doc, pricing: doc.pricing ?? DEFAULT_CONFIG.pricing };
  }

  async put(doc: HotlineConfigDoc): Promise<HotlineConfigDoc> {
    await this.ctx.storage.put("config", doc);
    return doc;
  }
}
