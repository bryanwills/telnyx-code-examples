// Re-export actor classes from the entry point so they are bundled and shipped
// with the function — the runtime resolves the [[actors]] `type` by matching
// the exported class name.
export { RegionAgent } from "./regionAgent";
export { HotlineIndex } from "./hotlineIndex";
export { HotlineConfig, DEFAULT_CONFIG } from "./hotlineConfig";

import {
  type ActorNamespace,
  type ActorStub,
  type IdFromNameOptions,
} from "@telnyx/edge-runtime";
import type { IngestInput, RegionAgent, RegionSummary } from "./regionAgent";
import type { HotlineConfigDoc } from "./hotlineConfig";
import { validateConfig } from "./hotlineConfig";
import { DASHBOARD_HTML, DEMO_REGIONS } from "./dashboardHtml";

// Stub typing: only the public async methods of RegionAgent are RPC-exposed;
// this keeps the caller-side surface honest about what can be awaited.
type RegionAgentStub = ActorStub &
  Pick<RegionAgent, "ingestReport" | "intakeReport" | "getSummary" | "getEval" | "resetAll">;

interface RegionNamespace extends ActorNamespace {
  idFromName(name: string, options?: IdFromNameOptions): RegionAgentStub;
}

interface HotlineIndexStub extends ActorStub {
  register(region: string): Promise<void>;
  list(): Promise<string[]>;
}

interface HotlineIndexNamespace extends ActorNamespace {
  idFromName(name: string, options?: IdFromNameOptions): HotlineIndexStub;
}

interface HotlineConfigStub extends ActorStub {
  get(): Promise<HotlineConfigDoc>;
  put(doc: HotlineConfigDoc): Promise<HotlineConfigDoc>;
}

interface HotlineConfigNamespace extends ActorNamespace {
  idFromName(name: string, options?: IdFromNameOptions): HotlineConfigStub;
}

interface Env {
  REGIONS: RegionNamespace;
  HOTLINE_INDEX: HotlineIndexNamespace;
  HOTLINE_CONFIG: HotlineConfigNamespace;
  TELNYX_API_KEY: string;
  AI_ASSISTANT_ID?: string;
}

// Fallback for [env_vars] not reaching the worker scope in this runtime
// version (secrets DO reach it; the working intake tests prove the key).
// This is NOT a credential — an opaque resource identifier, same pattern as
// edge-call-transcription-agent's DEFAULT_MODEL constant.
const FALLBACK_ASSISTANT_ID = "assistant-f36f6e0a-c1bb-4964-8268-98ae2e30bcb9";

// Actor names must be Dapr-safe (RFC 1123): letters, digits, dots, dashes.
// The "region-" prefix makes every instance name unambiguous in the platform.
function actorNameFor(region: string): string {
  return `region-${region.replace(/[^0-9a-zA-Z.-]/g, "")}`;
}

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url);

    if (url.pathname === "/health/liveness") return new Response("ok");
    if (url.pathname === "/health/readiness") return new Response("ok");

    // Reports only PRESENCE and length — never the key itself.
    if (url.pathname === "/debug/envcheck") {
      const k = env.TELNYX_API_KEY ?? process.env.TELNYX_API_KEY ?? "";
      const a = env.AI_ASSISTANT_ID ?? process.env.AI_ASSISTANT_ID ?? FALLBACK_ASSISTANT_ID;
      return Response.json({
        has_key: k.length > 0,
        key_len: k.length,
        has_assistant: a.length > 0,
        assistant_source: env.AI_ASSISTANT_ID ? "env" : process.env.AI_ASSISTANT_ID ? "process.env" : "fallback",
      });
    }

    // ── POST /debug/ingest?region=415 ─────────────────────────────────────
    // Step 1 test surface: writes a report WITHOUT calling the decision model
    // (classification lands in step 2). Lets us prove state durability in
    // isolation before model logic could ever muddy the picture.
    if (url.pathname === "/debug/ingest" && req.method === "POST") {
      const region = (url.searchParams.get("region") ?? "").trim();
      if (!/^[0-9a-zA-Z.-]{2,8}$/.test(region)) {
        return Response.json({ error: "region must be 2-8 safe characters (e.g. 415)" }, { status: 400 });
      }
      let body: Partial<IngestInput>;
      try {
        body = (await req.json()) as Partial<IngestInput>;
      } catch {
        return Response.json({ error: "invalid json body" }, { status: 400 });
      }
      if (!body.text || typeof body.text !== "string") {
        return Response.json({ error: "text is required" }, { status: 400 });
      }
      try {
        const stub = env.REGIONS.idFromName(actorNameFor(region));
        const result = await stub.ingestReport({
          reporter: body.reporter,
          text: body.text,
          expected_issue_type: body.expected_issue_type ?? null,
          expected_severity: body.expected_severity ?? null,
          expected_duplicate: body.expected_duplicate ?? null,
        });
        return Response.json({ region, ...result });
      } catch (e: unknown) {
        // Demo-safe error handling: log details, return a generic message.
        const msg = e instanceof Error ? e.message : "ingest failed";
        console.error("[ingest]", region, msg);
        return Response.json({ error: "ingest failed" }, { status: 500 });
      }
    }

    // ── GET /debug/state?region=415 ───────────────────────────────────────
    // Full actor state for one region: KV active-issue slot + every SQL
    // aggregate. This is what proves state survives across calls (step 1
    // acceptance gate) and what the dashboard reads in step 4.
    if (url.pathname === "/debug/state" && req.method === "GET") {
      const region = (url.searchParams.get("region") ?? "").trim();
      if (!/^[0-9a-zA-Z.-]{2,8}$/.test(region)) {
        return Response.json({ error: "region must be 2-8 safe characters (e.g. 415)" }, { status: 400 });
      }
      try {
        const stub = env.REGIONS.idFromName(actorNameFor(region));
        const summary: RegionSummary = await stub.getSummary();
        return Response.json({
          region,
          region_actor: actorNameFor(region),
          ...summary,
        });
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : "state fetch failed";
        console.error("[state]", region, msg);
        return Response.json({ error: "state fetch failed" }, { status: 500 });
      }
    }

    // ── POST /intake?region=415 ───────────────────────────────────────────
    // The real report intake: routes into the region actor, which does the
    // KV-read → decision-model classify → SQL-write → KV-policy sequence
    // atomically per region. Response echoes the model's answers plus every
    // application decision taken — handy for curl demos and debugging.
    if (url.pathname === "/intake" && req.method === "POST") {
      const region = (url.searchParams.get("region") ?? "").trim();
      if (!/^[0-9a-zA-Z.-]{2,8}$/.test(region)) {
        return Response.json({ error: "region must be 2-8 safe characters (e.g. 415)" }, { status: 400 });
      }
      let body: Partial<IngestInput>;
      try {
        body = (await req.json()) as Partial<IngestInput>;
      } catch {
        return Response.json({ error: "invalid json body" }, { status: 400 });
      }
      if (!body.text || typeof body.text !== "string") {
        return Response.json({ error: "text is required" }, { status: 400 });
      }
      try {
        const stub = env.REGIONS.idFromName(actorNameFor(region));
        // Worker resolves the key (either binding or process env) and injects
        // it — see the note on IngestInput.api_key.
        const result = await stub.intakeReport({
          reporter: body.reporter,
          text: body.text,
          region,
          api_key: env.TELNYX_API_KEY ?? process.env.TELNYX_API_KEY ?? "",
          expected_issue_type: body.expected_issue_type ?? null,
          expected_severity: body.expected_severity ?? null,
          expected_duplicate: body.expected_duplicate ?? null,
        });
        return Response.json({ region, ...result });
      } catch (e: unknown) {
        // Demo-safe error handling: log details server-side, return generic.
        // `?debug=1` opts INTO the detail — it's a demo affordance, not prod.
        const msg = e instanceof Error ? e.message : "intake failed";
        console.error("[intake]", region, msg);
        return Response.json(
          {
            error: "intake failed",
            ...(url.searchParams.get("debug") === "1" ? { detail: msg } : {}),
          },
          { status: 502 },
        );
      }
    }

    // ── POST /debug/reset?region=415 ──────────────────────────────────────
    // Demo affordance: wipe one region's state so the scripted run starts
    // clean on camera. Deletes ONLY this demo's own test data.
    if (url.pathname === "/debug/reset" && req.method === "POST") {
      const region = (url.searchParams.get("region") ?? "").trim();
      if (!/^[0-9a-zA-Z.-]{2,8}$/.test(region)) {
        return Response.json({ error: "region must be 2-8 safe characters (e.g. 415)" }, { status: 400 });
      }
      try {
        const stub = env.REGIONS.idFromName(actorNameFor(region));
        const result = await stub.resetAll();
        return Response.json({ region, ...result });
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : "reset failed";
        console.error("[reset]", region, msg);
        return Response.json({ error: "reset failed" }, { status: 500 });
      }
    }

    // ── GET /api/summary?regions=415,212 ─────────────────────────────────
    // Fan-out across region actors: per-actor SQL is private, so the only
    // way to aggregate is to ask each region actor for its own summary.
    // Regions = registered set (HotlineIndex) ∪ demo defaults — new area
    // codes arriving via voice calls appear here automatically.
    if (url.pathname === "/api/summary" && req.method === "GET") {
      const queryRegions = (url.searchParams.get("regions") ?? "")
        .split(",")
        .map((r) => r.trim())
        .filter(Boolean);
      let regions = queryRegions.length ? queryRegions : [...DEMO_REGIONS];
      try {
        const registered = await env.HOTLINE_INDEX.idFromName("global").list();
        regions = [...new Set([...regions, ...registered])];
      } catch {
        // index unavailable → fall back to the query/defaults
      }
      regions = regions.slice(0, 12);
      const settled = await Promise.allSettled(
        regions.map(async (r) => ({ region: r, summary: await env.REGIONS.idFromName(actorNameFor(r)).getSummary() })),
      );
      return Response.json({
        regions: settled.map((s) =>
          s.status === "fulfilled"
            ? s.value
            : { region: (s.reason as Error | undefined)?.message ?? "unknown", summary: null },
        ),
      });
    }

    // ── GET /api/eval?region=415 ─────────────────────────────────────────
    // The model's measured report card for one region.
    if (url.pathname === "/api/eval" && req.method === "GET") {
      const region = (url.searchParams.get("region") ?? DEMO_REGIONS[0]).trim();
      try {
        const evaluation = await env.REGIONS.idFromName(actorNameFor(region)).getEval();
        return Response.json({ region, eval: evaluation });
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : "eval failed";
        console.error("[eval]", region, msg);
        return Response.json({ error: "eval failed" }, { status: 500 });
      }
    }

    if (req.method === "GET" && (url.pathname === "/" || url.pathname === "/index.html")) {
      return new Response(DASHBOARD_HTML, {
        headers: { "content-type": "text/html;charset=utf-8" },
      });
    }

    // ── Voice webhook (call control) ─────────────────────────────────────
    // The hotline number points at a call-control application whose webhook
    // is this function. On call.initiated we answer the call BY HANDING IT
    // TO THE AI ASSISTANT — the assistant is the "hands" (talks to the
    // caller), the region actor is the "brain" (classifies, aggregates).
    // Demo note: per the repo's edge examples, production webhook signing
    // (Ed25519) is intentionally out of scope here.
    if (url.pathname === "/webhooks/voice" && req.method === "POST") {
      let body: unknown;
      try {
        body = await req.json();
      } catch {
        return Response.json({ error: "invalid json body" }, { status: 400 });
      }
      const event = (body as { data?: Record<string, unknown> })?.data;
      const eventType = event?.event_type as string | undefined;
      const payload = (event?.payload ?? {}) as Record<string, unknown>;
      const callControlId = payload.call_control_id as string | undefined;

      if (eventType === "call.initiated" && callControlId) {
        const apiKey = env.TELNYX_API_KEY ?? process.env.TELNYX_API_KEY ?? "";
        const assistantId = env.AI_ASSISTANT_ID ?? process.env.AI_ASSISTANT_ID ?? FALLBACK_ASSISTANT_ID;
        if (!apiKey) {
          return Response.json({ error: "TELNYX_API_KEY not configured" }, { status: 500 });
        }
        // Answer AND delegate to the assistant in one command — the
        // assistant's stored greeting/instructions take over from here.
        const resp = await fetch(`https://api.telnyx.com/v2/calls/${encodeURIComponent(callControlId)}/actions/answer`, {
          method: "POST",
          headers: { Authorization: `Bearer ${apiKey}`, "Content-Type": "application/json" },
          body: JSON.stringify({ assistant: { id: assistantId } }),
        });
        if (!resp.ok) {
          const errBody = await resp.text();
          console.error("[voice] answer failed", resp.status, errBody.slice(0, 200));
          return Response.json({ action: "error", step: "answer" }, { status: 502 });
        }
        return Response.json({ action: "answered_with_assistant", assistant_id: assistantId });
      }

      return Response.json({ action: "noop", event: eventType });
    }

    // ── POST /voice/report/<caller> — AI Assistant webhook tool ───────────
    // A real caller phones in: the Telnyx AI Assistant transcribes their
    // report and calls this tool. The caller's own number is injected by
    // Telnyx as the dynamic variable {{telnyx_end_user_target}} in the tool
    // URL — THAT is what derives the region (area code → region actor), so
    // voice reports follow the exact same region-keyed path as synthetic ones.
    if (url.pathname.startsWith("/voice/report/") && req.method === "POST") {
      const rawCaller = decodeURIComponent(url.pathname.slice("/voice/report/".length));
      // NANP derivation: strip non-digits, drop a leading 1, take the area code.
      const digits = rawCaller.replace(/\D/g, "");
      const nanp = digits.length === 11 && digits.startsWith("1") ? digits.slice(1) : digits;
      const region = nanp.slice(0, 3);
      let body: { text?: string };
      try {
        body = (await req.json()) as { text?: string };
      } catch {
        return Response.json({ error: "invalid json body" }, { status: 400 });
      }
      if (!body.text || typeof body.text !== "string") {
        return Response.json({ error: "text is required" }, { status: 400 });
      }
      try {
        const stub = env.REGIONS.idFromName(actorNameFor(region));
        const r = await stub.intakeReport({
          reporter: `voice:${rawCaller}`,
          text: body.text,
          region,
          api_key: env.TELNYX_API_KEY ?? process.env.TELNYX_API_KEY ?? "",
        });
        // The tool's response body goes back to the assistant's LLM, which
        // speaks `message` to the caller — confirmation includes the live
        // regional count, which is the demo's "brain answering the caller" beat.
        const message = !r.category.is_outage
          ? `Got it. This sounds like a ${r.category.label} matter rather than an outage — I've logged it and our team will follow up.`
          : r.escalated
            ? `Got it. That's report number ${r.id} in your area, and it's been flagged for our team right away.`
            : r.judged_duplicate
              ? `Got it. We already know about this issue in your area — you're report number ${r.report_count}. Our team is on it.`
              : `Got it. I've logged your report as number ${r.id} in your area. Our team is on it.`;
        return Response.json({ message, report_id: r.id, region, report_count: r.report_count, escalated: r.escalated });
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : "voice intake failed";
        console.error("[voice-intake]", region, msg);
        return Response.json(
          {
            message: "Sorry — I couldn't log your report right now. Please try again in a moment.",
            error: "intake failed",
            ...(url.searchParams.get("debug") === "1" ? { detail: msg } : {}),
          },
          { status: 502 },
        );
      }
    }

    // ── GET /api/config — the active classification taxonomy ─────────────
    // Public read: the dashboard derives its columns/labels from this, and
    // the report card's thresholds come from the same source of truth.
    if (url.pathname === "/api/config" && req.method === "GET") {
      const config = await env.HOTLINE_CONFIG.idFromName("global").get();
      return Response.json({ config });
    }

    // ── PUT /admin/config — edit the taxonomy WITHOUT a redeploy ─────────
    // Body: a HotlineConfigDoc. Validated against the decision-model
    // endpoint's limits before it's stored; version is bumped by the caller
    // (or set 1). Changing categories/rubric/thresholds takes effect on the
    // NEXT report — historical rows keep the schema_version they were
    // classified under.
    if (url.pathname === "/admin/config" && req.method === "PUT") {
      let body: unknown;
      try {
        body = await req.json();
      } catch {
        return Response.json({ error: "invalid json body" }, { status: 400 });
      }
      const check = validateConfig(body);
      if (!check.ok || !check.value) {
        return Response.json({ error: "invalid config", errors: check.errors }, { status: 400 });
      }
      const stub = env.HOTLINE_CONFIG.idFromName("global");
      const current = await stub.get();
      const next = check.value;
      if (next.version === current.version) next.version = current.version + 1;
      const stored = await stub.put(next);
      return Response.json({ config: stored });
    }

    if (url.pathname === "/admin/config" && req.method === "GET") {
      const config = await env.HOTLINE_CONFIG.idFromName("global").get();
      return Response.json({ config });
    }

    if (req.method === "GET" && (url.pathname === "/routes" || url.pathname === "/index.json")) {
      return Response.json({
        service: "regional-outage-reporting-hotline",
        status: "step-4: dashboard live",
        routes: {
          "GET /": "the incident dashboard (HTML)",
          "POST /intake?region=<r>": "classify + store a report (decision model)",
          "POST /voice/report/<caller>": "AI Assistant tool endpoint — caller number in path keys the region",
          "GET /api/summary?regions=<a,b>": "dashboard data (fan-out across region actors)",
          "GET /api/eval?region=<r>": "model report card (accuracy vs ground truth)",
          "POST /debug/ingest?region=<r>": "log a raw report (no classification)",
          "GET /debug/state?region=<r>": "actor state: KV slot + SQL aggregates",
          "POST /debug/reset?region=<r>": "wipe one region's demo state",
          "GET /health/*": "liveness/readiness",
        },
      });
    }

    return new Response("not found", { status: 404 });
  },
};
