import { StatefulActor } from "@telnyx/edge-runtime";
import type { SqlBindValue, SqlValue } from "@telnyx/edge-runtime";
import { runDecisionModel, buildModelState, buildQuestions } from "./decisionModel";
import type { HotlineConfigDoc } from "./hotlineConfig";

// ─────────────────────────────────────────────────────────────────────────
// RegionAgent — one Stateful Actor instance per reportable region.
//
// WHY keyed by region, not by caller: during an outage, dozens of callers
// report the same problem. Keying the actor by region means all of those
// reports converge into ONE actor's storage, which is what makes aggregation
// (counts, dedupe, escalation) possible at all. A per-caller actor would
// leave every report isolated — there would be nothing to aggregate.
//
// WHY two storage layers instead of one:
//   - SQL (this.ctx.storage.sql) is the HISTORY + AGGREGATE layer. We need
//     GROUP BY counts, "reports in the last hour", severity breakdowns —
//     relational queries a KV cannot answer without reading everything.
//   - KV (this.ctx.storage.get/put) is the WORKING-SET layer: a tiny
//     "current known issue" blob read on every new report to give the
//     decision model dedupe context. One KV read is cheaper than a SQL
//     round-trip for a question we ask on every single report.
// ─────────────────────────────────────────────────────────────────────────

export interface RegionEnv {
  TELNYX_API_KEY: string;
  // Shared registry namespace: region actors register themselves on first
  // report so /api/summary can discover dynamic regions (e.g. new area codes
  // arriving via voice calls). Calls into it are best-effort.
  HOTLINE_INDEX: { idFromName(name: string): { register(region: string): Promise<void> } };
  // Shared config namespace: the versioned classification taxonomy. Read per
  // ingest (one KV read) so category/rubric/threshold changes apply without
  // a redeploy.
  HOTLINE_CONFIG: { idFromName(name: string): { get(): Promise<HotlineConfigDoc> } };
}

// The "have we seen this before?" context, kept in KV because it is read on
// EVERY incoming report. `issue_type` stays null until the decision model
// lands (step 2) — the blob's shape is designed now so step 2 only fills it.
export interface ActiveIssue {
  issue_type: string | null;
  first_seen: number;
  last_seen: number;
}

export interface IngestInput {
  reporter?: string;
  text: string;
  // Region the report is about (used only to build the model's state string).
  region?: string;
  // WHY passed in from the worker: in this runtime version the secrets
  // binding does not reach the actor env, so the worker injects the API key
  // at call time. It stays in-process — never logged, never persisted.
  api_key?: string;
  // Demo-only ground truth from the load script. Stored alongside the model's
  // answer so we can MEASURE the model's accuracy later instead of assuming it.
  expected_issue_type?: string | null;
  expected_severity?: string | null;
  expected_duplicate?: number | null;
}

export interface RegionSummary {
  report_count: number;
  last_hour_count: number;
  severity_breakdown: { severity_bucket: number; count: number }[];
  distinct_issues: { issue_type: string; count: number; first_seen: string; last_seen: string }[];
  escalations: Record<string, SqlValue>[];
  recent_reports: Record<string, SqlValue>[];
  active_issue: ActiveIssue | null;
  usage: { input_tokens: number; output_tokens: number };
  cost_estimate: {
    currency: string;
    total: number;
    per_report_avg: number;
    rate_source: string;
  };
}

// The measured report card for the decision model. WHY this exists: the
// endpoint's `confidence` is documented as normalized entropy — explicitly
// NOT a calibrated probability of correctness — so every accuracy claim in
// the demo comes from HERE, computed against stored ground truth, never from
// trusting the model's own confidence field.
export interface EvalSummary {
  labeled_issue_type: number;
  issue_type_correct: number;
  issue_type_confusion: { expected: string; actual: string; count: number }[];
  labeled_severity: number;
  severity_exact: number;
  severity_within_one: number;
  severity_mae: number;
  labeled_duplicate: number;
  duplicate_accuracy: { threshold: number; correct: number }[];
  confidence_bins: { range: string; total: number; correct: number }[];
}

// Row shape mirrors the reports table. `extends Record<string, SqlValue>`
// satisfies the cursor's row-type constraint (all columns must be SQL-typed).
export interface ReportRow extends Record<string, SqlValue> {
  id: number;
  received_at: string;
  reporter: string;
  raw_report: string;
  issue_type: string | null;
  severity_raw: number | null;
  severity_bucket: number | null;
  is_duplicate_raw: number | null;
  is_duplicate_flag: number | null;
  confidence: number | null;
  escalated: number;
  expected_issue_type: string | null;
  expected_severity: string | null;
  expected_duplicate: number | null;
}

export class RegionAgent extends StatefulActor<RegionEnv> {
  // ── Internal helpers (underscore-prefixed = not RPC-exposed) ───────────

  // Idempotent schema creation: any actor instance (cold or warm) can be
  // handed a report at any time, so we make table setup cheap and repeatable
  // rather than sequencing it behind activation.
  private _ensureTables(): void {
    this.ctx.storage.sql.exec(`
      CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        received_at TEXT NOT NULL,
        reporter TEXT,
        raw_report TEXT NOT NULL,
        issue_type TEXT,
        severity_raw REAL,
        severity_bucket INTEGER,
        is_duplicate_raw REAL,
        is_duplicate_flag INTEGER,
        confidence REAL,
        escalated INTEGER NOT NULL DEFAULT 0,
        expected_issue_type TEXT,
        expected_severity TEXT,
        expected_duplicate INTEGER,
        schema_version INTEGER,
        input_tokens INTEGER,
        output_tokens INTEGER
      )
    `);
    this.ctx.storage.sql.exec(
      `CREATE INDEX IF NOT EXISTS idx_reports_received_at ON reports(received_at)`,
    );
    this._ensureUsageColumns();
  }

  private _fetchOne<T extends Record<string, SqlValue>>(
    query: string,
    ...bindings: SqlBindValue[]
  ): T | null {
    const cursor = this.ctx.storage.sql.exec<T>(query, ...bindings);
    for (const row of cursor) return row;
    return null;
  }

  /**
   * Schema migration for post-launch columns. Existing actor databases get
   * them via ALTER TABLE; new ones get them in CREATE TABLE.
   *  - schema_version: the taxonomy version the row was classified under.
   *  - input_tokens / output_tokens: decision-model usage per report — the
   *    raw material for cost tracking. WHY persisted here: the usage-reports
   *    API aggregates per model per DAY across the whole account, so it can
   *    attribute cost to a specific application only approximately; storing
   *    usage at write time gives exact per-report attribution.
   */
  private _ensureUsageColumns(): void {
    let cols: { name: string }[] = [];
    try {
      cols = this._fetchAll<{ name: string }>(`PRAGMA table_info(reports)`);
    } catch {
      cols = [];
    }
    const have = (c: string) => cols.some((x) => x.name === c);
    if (!have("schema_version")) {
      try {
        this.ctx.storage.sql.exec(`ALTER TABLE reports ADD COLUMN schema_version INTEGER`);
      } catch {
        // already exists — fine
      }
    }
    if (!have("input_tokens")) {
      try {
        this.ctx.storage.sql.exec(`ALTER TABLE reports ADD COLUMN input_tokens INTEGER`);
      } catch {
        // already exists — fine
      }
    }
    if (!have("output_tokens")) {
      try {
        this.ctx.storage.sql.exec(`ALTER TABLE reports ADD COLUMN output_tokens INTEGER`);
      } catch {
        // already exists — fine
      }
    }
  }

  private _fetchAll<T extends Record<string, SqlValue>>(
    query: string,
    ...bindings: SqlBindValue[]
  ): T[] {
    return this.ctx.storage.sql.exec<T>(query, ...bindings).toArray();
  }

  // ── Public RPC surface ─────────────────────────────────────────────────

  // Best-effort registration into the shared index so the dashboard can
  // discover dynamic regions (per-actor SQL is private — the index is the
  // only cross-actor surface). Never fails an ingest.
  private _registerRegion(region: string | undefined): void {
    if (!region) return;
    this.env.HOTLINE_INDEX.idFromName("global").register(region).catch(() => {
      // index registration is best-effort; summary falls back to known regions
    });
  }

  /**
   * Log one outage report for THIS region.
   *
   * Step 1 stores the raw report with classification columns NULL. Step 2
   * fills them from the decision model. The KV read-modify-write below is
   * safe: actor method calls serialize per instance, so two concurrent
   * reports cannot interleave their KV updates.
   */
  async ingestReport(input: IngestInput): Promise<{
    id: number;
    report_count: number;
    active_issue: ActiveIssue;
  }> {
    this._ensureTables();
    const now = Date.now();
    const receivedAt = new Date(now).toISOString();

    this.ctx.storage.sql.exec(
      `INSERT INTO reports
         (received_at, reporter, raw_report, escalated,
          expected_issue_type, expected_severity, expected_duplicate)
       VALUES (?, ?, ?, 0, ?, ?, ?)`,
      receivedAt,
      input.reporter ?? "anonymous",
      input.text,
      input.expected_issue_type ?? null,
      input.expected_severity ?? null,
      input.expected_duplicate ?? null,
    );
    this._registerRegion(input.region);

    const idRow = this._fetchOne<{ last: number }>(`SELECT last_insert_rowid() AS last`);
    const id = idRow?.last ?? 0;

    // KV write policy: step 1 just keeps the slot warm. Step 2 decides
    // "same known issue → bump last_seen" vs "new issue type → overwrite".
    let active = await this.ctx.storage.get<ActiveIssue>("active_issue");
    active = active
      ? { ...active, last_seen: now }
      : { issue_type: null, first_seen: now, last_seen: now };
    await this.ctx.storage.put("active_issue", active);

    const count = this._fetchOne<{ c: number }>(`SELECT COUNT(*) AS c FROM reports`)?.c ?? 0;
    return { id, report_count: count, active_issue: active };
  }

  /**
   * The real intake path: classify the report with the decision model, then
   * persist. WHY the model call lives inside the actor method: the sequence
   * KV-read → classify → SQL-write → KV-write must be serialized per region,
   * and actor method invocation gives us exactly that guarantee. Two reports
   * for the same region cannot interleave their KV read-modify-writes.
   *
   * Application logic (this code, not the model) makes every decision:
   *   - escalation (genuinely new + severe, not a pile-on of a known issue)
   *   - KV write policy (see below)
   *   - severity bucket (the model's score is fractional by design; we round
   *     for alerting but store the raw float for the accuracy eval)
   */
  async intakeReport(input: IngestInput): Promise<{
    id: number;
    report_count: number;
    active_issue: ActiveIssue | null;
    schema_version: number;
    category: { key: string; label: string; is_outage: boolean };
    judged_duplicate: boolean;
    model: {
      issue_type: string;
      issue_type_confidence: number;
      severity_raw: number;
      severity_bucket: number;
      severity_confidence: number;
      is_duplicate: number;
      confidence: number;
    };
    usage: { input_tokens: number; output_tokens: number } | null;
    cost_estimate: {
      currency: string;
      amount: number;
      rate_source: string;
    };
    escalated: boolean;
    kv_updated: boolean;
  }> {
    this._ensureTables();
    const now = Date.now();
    const receivedAt = new Date(now).toISOString();

    // 0. The active taxonomy: categories, rubric, and thresholds are DATA.
    //    Everything below derives its decisions from this doc — no category
    //    literals in application logic.
    const config = await this.env.HOTLINE_CONFIG.idFromName("global").get();

    // 1. Hot context from Durable KV — the fast path that avoids a SQL query
    //    on every report just to ask "have we seen this before?".
    const active = (await this.ctx.storage.get<ActiveIssue>("active_issue")) ?? null;

    // 2. One decision-model call answers all three questions at once —
    //    one round-trip and ~400 input tokens per report, not three LLM calls.
    const { answers, usage } = await runDecisionModel(
      buildModelState(input.text, input.region ?? "unknown", active),
      buildQuestions(config),
      input.api_key ?? this.env.TELNYX_API_KEY,
    );

    const issueType = answers.issue_type.choice;
    // `score` is fractional (sum of index × probability). Keep the raw float
    // in SQL for the calibration eval; round only for the discrete bucket.
    // The rubric length comes from config — bucket max adapts to it.
    const severityBucket = Math.min(
      config.severity_rubric.length - 1,
      Math.max(0, Math.round(answers.severity.score)),
    );
    const isDuplicate = answers.is_duplicate.noul; // 0-1 float, NO confidence exists on this field

    // 3. Policy flags come from the taxonomy, not from literals. A category
    //    the model invents (shouldn't happen — the choice domain is the
    //    config keys) is treated conservatively: no escalation, no KV slot.
    const category =
      config.issue_types.find((t) => t.key === issueType) ?? {
        key: issueType,
        label: issueType,
        is_outage: false,
        may_own_kv_slot: false,
        escalatable: false,
      };
    const judgedDuplicate = isDuplicate >= config.escalation.max_duplicate_noul;
    // Escalation is application logic, and it gates on the model's OWN
    // classification. First load run taught us why: without this check, a
    // billing complaint arriving during a live outage scored High severity
    // (the model anchors severity on the outage context) and — because a
    // billing report is never a "duplicate" — tripped escalation. The model
    // classified it correctly; the naive rule was the bug.
    const escalated =
      category.escalatable &&
      category.is_outage &&
      severityBucket >= config.escalation.min_severity_bucket &&
      !judgedDuplicate
        ? 1
        : 0;

    // 4. Persist the report + the model's answers (raw values, not rounded),
    //    stamped with the taxonomy version they were classified under so
    //    historical rows stay interpretable as the config evolves.
    this.ctx.storage.sql.exec(
      `INSERT INTO reports
         (received_at, reporter, raw_report, issue_type, severity_raw, severity_bucket,
          is_duplicate_raw, is_duplicate_flag, confidence, escalated,
          expected_issue_type, expected_severity, expected_duplicate, schema_version,
          input_tokens, output_tokens)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
      receivedAt,
      input.reporter ?? "anonymous",
      input.text,
      issueType,
      answers.severity.score,
      severityBucket,
      isDuplicate,
      // Flag semantics: 1 = the model judged this report a DUPLICATE of the
      // known issue (noul >= threshold). noul is "yes, same outage" — so
      // new/genuinely-distinct reports get 0. (First voice test caught this
      // inverted: the flag had marked NEW reports, which mislabeled the
      // dashboard's "dupes flagged" stat.)
      judgedDuplicate ? 1 : 0,
      answers.issue_type.confidence,
      escalated,
      input.expected_issue_type ?? null,
      input.expected_severity ?? null,
      input.expected_duplicate ?? null,
      config.version,
      usage?.input_tokens ?? null,
      usage?.output_tokens ?? null,
    );
    const id = this._fetchOne<{ last: number }>(`SELECT last_insert_rowid() AS last`)?.last ?? 0;

    // 5. KV write policy, driven by `may_own_kv_slot`:
    //    - Non-slot categories (e.g. billing) never become the known active
    //      issue — letting them own the slot would poison dedupe context
    //      for every subsequent real outage report in this region.
    //    - Same issue_type as the known issue → bump last_seen (the pile-on
    //      window grows with each confirmed report).
    //    - A new issue_type → overwrite the slot (one slot keeps the demo
    //      legible; the full history lives in SQL).
    let kvUpdated = false;
    if (category.may_own_kv_slot) {
      const nextActive: ActiveIssue =
        active && active.issue_type === issueType
          ? { ...active, last_seen: now }
          : { issue_type: issueType, first_seen: now, last_seen: now };
      await this.ctx.storage.put("active_issue", nextActive);
      kvUpdated = true;
    }

    const count = this._fetchOne<{ c: number }>(`SELECT COUNT(*) AS c FROM reports`)?.c ?? 0;

    // Per-report cost estimate from the config's per-token rates. The real
    // rate is verified against the usage-reports API (the decision model
    // bills under the zai-org/GLM-5.3-Flash cost code); the config keeps it
    // editable so rate changes are a config edit, not a deploy.
    const costEstimate =
      ((usage?.input_tokens ?? 0) / 1_000_000) * config.pricing.input_per_mtok +
      ((usage?.output_tokens ?? 0) / 1_000_000) * config.pricing.output_per_mtok;

    return {
      id,
      report_count: count,
      active_issue: await this.ctx.storage.get<ActiveIssue>("active_issue").then((v) => v ?? null),
      schema_version: config.version,
      category: { key: category.key, label: category.label, is_outage: category.is_outage },
      judged_duplicate: judgedDuplicate,
      model: {
        issue_type: issueType,
        issue_type_confidence: answers.issue_type.confidence,
        severity_raw: answers.severity.score,
        severity_bucket: severityBucket,
        severity_confidence: answers.severity.confidence,
        is_duplicate: isDuplicate,
        confidence: answers.issue_type.confidence,
      },
      usage,
      cost_estimate: {
        currency: config.pricing.currency,
        amount: costEstimate,
        rate_source: config.pricing.source,
      },
      escalated: escalated === 1,
      kv_updated: kvUpdated,
    };
  }

  /**
   * Everything the dashboard needs for one region, computed with real
   * relational queries — this is the method that justifies SQLDB over a flat
   * KV dump: counts, time-windowed aggregates, GROUP BYs, filtered lists.
   */
  async getSummary(): Promise<RegionSummary> {
    this._ensureTables();
    const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000).toISOString();

    const reportCount = this._fetchOne<{ c: number }>(`SELECT COUNT(*) AS c FROM reports`)?.c ?? 0;
    const lastHour =
      this._fetchOne<{ c: number }>(
        `SELECT COUNT(*) AS c FROM reports WHERE received_at > ?`,
        oneHourAgo,
      )?.c ?? 0;

    const severityBreakdown = this._fetchAll<{ severity_bucket: number; c: number }>(
      `SELECT severity_bucket, COUNT(*) AS c
         FROM reports WHERE severity_bucket IS NOT NULL
        GROUP BY severity_bucket ORDER BY severity_bucket`,
    ).map((r) => ({ severity_bucket: r.severity_bucket, count: r.c }));

    const distinctIssues = this._fetchAll<{
      issue_type: string;
      c: number;
      first_seen: string;
      last_seen: string;
    }>(
      `SELECT issue_type, COUNT(*) AS c,
              MIN(received_at) AS first_seen, MAX(received_at) AS last_seen
         FROM reports WHERE issue_type IS NOT NULL
        GROUP BY issue_type ORDER BY c DESC`,
    ).map((r) => ({
      issue_type: r.issue_type,
      count: r.c,
      first_seen: r.first_seen,
      last_seen: r.last_seen,
    }));

    const escalations = this._fetchAll<ReportRow>(
      `SELECT * FROM reports WHERE escalated = 1 ORDER BY received_at DESC LIMIT 20`,
    );
    const recent = this._fetchAll<ReportRow>(
      `SELECT id, received_at, reporter, raw_report, issue_type, severity_bucket,
              is_duplicate_flag, escalated
         FROM reports ORDER BY received_at DESC LIMIT 20`,
    );

    const activeIssue = (await this.ctx.storage.get<ActiveIssue>("active_issue")) ?? null;

    // Cost rollup from persisted per-report usage. Rows logged before usage
    // tracking existed have NULL token columns — COALESCE keeps them at zero
    // rather than silently inflating the total.
    const tokens = this._fetchOne<{ i: number; o: number; n: number }>(
      `SELECT COALESCE(SUM(input_tokens), 0) AS i,
              COALESCE(SUM(output_tokens), 0) AS o,
              COUNT(input_tokens) AS n
         FROM reports`,
    );
    const config = await this.env.HOTLINE_CONFIG.idFromName("global").get();
    const totalTokensIn = tokens?.i ?? 0;
    const totalTokensOut = tokens?.o ?? 0;
    const totalCost =
      (totalTokensIn / 1_000_000) * config.pricing.input_per_mtok +
      (totalTokensOut / 1_000_000) * config.pricing.output_per_mtok;
    const measured = tokens?.n ?? 0;

    return {
      report_count: reportCount,
      last_hour_count: lastHour,
      severity_breakdown: severityBreakdown,
      distinct_issues: distinctIssues,
      escalations,
      recent_reports: recent,
      active_issue: activeIssue,
      usage: { input_tokens: totalTokensIn, output_tokens: totalTokensOut },
      cost_estimate: {
        currency: config.pricing.currency,
        total: totalCost,
        per_report_avg: measured > 0 ? totalCost / measured : 0,
        rate_source: config.pricing.source,
      },
    };
  }

  /**
   * Demo affordance: wipe this region's state (SQL + KV) so the scripted load
   * run starts from a clean slate on camera. Not for production use.
   */
  async resetAll(): Promise<{ deleted_reports: number }> {
    this._ensureTables();
    const count = this._fetchOne<{ c: number }>(`SELECT COUNT(*) AS c FROM reports`)?.c ?? 0;
    this.ctx.storage.sql.exec(`DELETE FROM reports;`);
    await this.ctx.storage.deleteAll();
    return { deleted_reports: count };
  }

  /**
   * Score the model against the ground truth the load script stored with
   * each report. Because per-actor SQL is private, each region evaluates
   * its OWN rows — the dashboard fans out per region.
   *
   * Metric notes:
   *  - issue_type: exact match + confusion pairs (the interesting edges are
   *    degraded↔no_service and billing↔other).
   *  - severity: MAE on the 0-3 scale, exact-bucket accuracy, and
   *    within-1-bucket accuracy (severity is fuzzy by nature).
   *  - is_duplicate has NO confidence to lean on, so accuracy is computed
   *    across a sweep of decision thresholds — that sweep IS the honest
   *    way to pick an operating point.
   *  - confidence bins: does the model's (entropy-based) confidence
   *    correlate with being right at all? Measured, never assumed.
   */
  async getEval(): Promise<EvalSummary> {
    this._ensureTables();
    // Rubric indices come from the active config, so eval stays correct if
    // the rubric ever grows beyond 4 buckets.
    const config = await this.env.HOTLINE_CONFIG.idFromName("global").get();
    const SEV_INDEX: Record<string, number> = {};
    config.severity_rubric.forEach((label, i) => {
      SEV_INDEX[String(label).toLowerCase()] = i;
    });
    const DUP_THRESHOLD = config.escalation.max_duplicate_noul;
    const rows = this._fetchAll<ReportRow>(
      `SELECT issue_type, severity_bucket, is_duplicate_raw, confidence,
              expected_issue_type, expected_severity, expected_duplicate
         FROM reports
        WHERE expected_issue_type IS NOT NULL
           OR expected_severity IS NOT NULL
           OR expected_duplicate IS NOT NULL`,
    );

    const DUP_THRESHOLDS = [0.2, DUP_THRESHOLD, 0.5, 0.7];
    const BINS: { range: string; lo: number; hi: number }[] = [
      { range: "0.0–0.5", lo: 0, hi: 0.5 },
      { range: "0.5–0.8", lo: 0.5, hi: 0.8 },
      { range: "0.8–0.95", lo: 0.8, hi: 0.95 },
      { range: "0.95–1.0", lo: 0.95, hi: 1.01 },
    ];

    // ── issue_type: exact match + confusion pairs ──
    const confusion = new Map<string, number>();
    let itTotal = 0;
    let itCorrect = 0;
    for (const r of rows) {
      if (r.expected_issue_type == null || r.issue_type == null) continue;
      itTotal++;
      const actual = r.expected_issue_type === r.issue_type;
      if (actual) itCorrect++;
      const key = `${r.expected_issue_type}→${r.issue_type}`;
      confusion.set(key, (confusion.get(key) ?? 0) + 1);
    }
    const issueTypeConfusion = [...confusion.entries()]
      .map(([k, count]) => {
        const [expected, actual] = k.split("→");
        return { expected, actual, count };
      })
      .sort((a, b) => (a.expected === a.actual ? 1 : 0) - (b.expected === b.actual ? 1 : 0) || b.count - a.count);

    // ── severity: MAE + exact/within-one accuracy ──
    let svTotal = 0;
    let svExact = 0;
    let svWithinOne = 0;
    let svAbsSum = 0;
    for (const r of rows) {
      if (r.expected_severity == null || r.severity_bucket == null) continue;
      const expected = SEV_INDEX[String(r.expected_severity).toLowerCase()];
      if (expected === undefined) continue;
      svTotal++;
      const diff = Math.abs(r.severity_bucket - expected);
      svAbsSum += diff;
      if (diff === 0) svExact++;
      if (diff <= 1) svWithinOne++;
    }

    // ── is_duplicate: threshold sweep (the only honest metric for a noul) ──
    const dupRows = rows.filter((r) => r.expected_duplicate != null && r.is_duplicate_raw != null);
    const duplicateAccuracy = DUP_THRESHOLDS.map((t) => ({
      threshold: t,
      correct: dupRows.filter(
        (r) => (r.is_duplicate_raw! >= t) === (r.expected_duplicate === 1),
      ).length,
    }));

    // ── confidence calibration: does high entropy-based confidence mean right? ──
    const confidenceBins = BINS.map((b) => {
      const inBin = rows.filter(
        (r) => r.confidence != null && r.expected_issue_type != null && r.confidence >= b.lo && r.confidence < b.hi,
      );
      return {
        range: b.range,
        total: inBin.length,
        correct: inBin.filter((r) => r.issue_type === r.expected_issue_type).length,
      };
    });

    return {
      labeled_issue_type: itTotal,
      issue_type_correct: itCorrect,
      issue_type_confusion: issueTypeConfusion,
      labeled_severity: svTotal,
      severity_exact: svExact,
      severity_within_one: svWithinOne,
      severity_mae: svTotal ? svAbsSum / svTotal : 0,
      labeled_duplicate: dupRows.length,
      duplicate_accuracy: duplicateAccuracy,
      confidence_bins: confidenceBins,
    };
  }
}
