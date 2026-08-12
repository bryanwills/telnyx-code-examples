export { TriageAgent } from "./triageAgent";
import type { TriageAgent } from "./triageAgent";

import {
  type ActorNamespace,
  type ActorStub,
  type IdFromNameOptions,
} from "@telnyx/edge-runtime";

type TriageAgentStub = ActorStub &
  Pick<
    TriageAgent,
    | "setRoute"
    | "getRoutes"
    | "triage"
    | "getHistory"
    | "getDebugState"
  >;

interface TriageAgentNamespace extends ActorNamespace {
  idFromName(name: string, options?: IdFromNameOptions): TriageAgentStub;
}

interface Env {
  TRIAGE: TriageAgentNamespace;
}

function actorName(e164: string): string {
  return e164.replace(/[^0-9a-zA-Z.-]/g, "");
}

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url);

    if (url.pathname === "/health/liveness") return new Response("ok");
    if (url.pathname === "/health/readiness") return new Response("ok");

    // ── POST /webhooks/sms — inbound SMS from customer ──────────────
    if (req.method === "POST" && (url.pathname === "/webhooks/sms" || url.pathname === "/")) {
      try {
        const body = (await req.json().catch(() => ({}))) as any;
        const evt = body?.data;
        if (!evt || evt.event_type !== "message.received") {
          return Response.json({ error: "unexpected event_type" }, { status: 400 });
        }
        const payload = evt.payload || {};
        const from = (payload.from?.phone_number || payload.from) as string;
        const to = (payload.to?.[0]?.phone_number || payload.to?.[0] || payload.to) as string;
        const text = (payload.text || "") as string;

        if (!from || !text.trim()) {
          return Response.json({ error: "missing from or text" }, { status: 400 });
        }

        // Use the inbound number (to) as the actor key — one actor per inbound number
        const stub = env.TRIAGE.idFromName(actorName(String(to)));
        const result = await stub.triage(String(from), String(text));
        return Response.json({ action: "triaged", from, to, ...result });
      } catch (e: any) {
        return Response.json({ error: e?.message || "bad request" }, { status: 400 });
      }
    }

    // ── POST /routes — update a route in the route table ────────────
    if (url.pathname === "/routes" && req.method === "POST") {
      const body = (await req.json().catch(() => ({}))) as {
        topic?: string;
        queue?: string;
        number?: string;
      };

      const topic = body.topic?.trim();
      const queue = body.queue?.trim();
      const number = body.number?.trim() || "+16282564655";

      if (!topic || !queue) {
        return Response.json({ error: "topic and queue are required" }, { status: 400 });
      }

      const stub = env.TRIAGE.idFromName(actorName(number));
      await stub.setRoute(topic, queue);
      return Response.json({ topic, queue, number });
    }

    // ── GET /routes — list the route table ──────────────────────────
    if (url.pathname === "/routes" && req.method === "GET") {
      const number = url.searchParams.get("number") || "+16282564655";
      const stub = env.TRIAGE.idFromName(actorName(number));
      const routes = await stub.getRoutes();
      return Response.json({ number, routes });
    }

    // ── GET /history — get triage history ───────────────────────────
    if (url.pathname === "/history" && req.method === "GET") {
      const number = url.searchParams.get("number") || "+16282564655";
      const limit = parseInt(url.searchParams.get("limit") || "20", 10);
      const stub = env.TRIAGE.idFromName(actorName(number));
      const history = await stub.getHistory(limit);
      return Response.json({ number, ...history });
    }

    // ── POST /debug/triage — simulate an inbound SMS without real SMS ─
    if (url.pathname === "/debug/triage" && req.method === "POST") {
      const body = (await req.json().catch(() => ({}))) as {
        from?: string;
        to?: string;
        text?: string;
      };

      const from = body.from?.trim() || "+17177247292";
      const to = body.to?.trim() || "+16282564655";
      const text = body.text?.trim() || "I need help with my bill";

      const stub = env.TRIAGE.idFromName(actorName(to));
      const result = await stub.triage(from, text);
      return Response.json({ action: "triaged", from, to, text, ...result });
    }

    // ── GET /debug/state — inspect actor state ─────────────────────
    if (url.pathname === "/debug/state" && req.method === "GET") {
      const number = url.searchParams.get("number") || "+16282564655";
      const stub = env.TRIAGE.idFromName(actorName(number));
      try {
        const state = await stub.getDebugState();
        return Response.json(state);
      } catch (e: any) {
        return Response.json({ error: e?.message || "failed to get state" }, { status: 500 });
      }
    }

    return new Response("not found", { status: 404 });
  },
};
