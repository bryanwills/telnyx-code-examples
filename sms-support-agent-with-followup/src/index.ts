// Re-export the actor class so it ships with the bundle.
export { SupportAgent } from "./supportAgent";
import type { SupportAgent } from "./supportAgent";

import {
  type ActorNamespace,
  type ActorStub,
  type IdFromNameOptions,
} from "@telnyx/edge-runtime";

type SupportAgentStub = ActorStub &
  Pick<
    SupportAgent,
    "receive" | "process" | "followup"
  >;

interface SupportAgentNamespace extends ActorNamespace {
  idFromName(name: string, options?: IdFromNameOptions): SupportAgentStub;
}

interface Env {
  SUPPORT: SupportAgentNamespace;
}

// Dapr-safe actor names: no "+", no special chars (RFC 1123 job-name-safe).
function actorName(e164: string): string {
  return e164.replace(/[^0-9a-zA-Z.-]/g, "");
}

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url);

    // Health
    if (url.pathname === "/health/liveness") return new Response("ok");
    if (url.pathname === "/health/readiness") return new Response("ok");

    // ── Telnyx SMS webhook (message.received) ──────────────────────────
    if (req.method === "POST" && (url.pathname === "/webhooks/sms" || url.pathname === "/")) {
      try {
        const body = (await req.json().catch(() => ({}))) as any;
        const evt = body?.data;
        if (!evt || evt.event_type !== "message.received") {
          return Response.json({ error: "unexpected event_type" }, { status: 400 });
        }
        const payload = evt.payload || {};
        const from = payload.from?.phone_number || payload.from;
        const to = (payload.to && payload.to[0] && (payload.to[0].phone_number || payload.to[0])) || payload.to;
        const text = payload.text || "";
        if (!from || !text.trim()) {
          return Response.json({ error: "missing from or text" }, { status: 400 });
        }

        await env.SUPPORT.idFromName(actorName(String(from))).receive({
          text: String(text),
          from: String(from),
          to: String(to),
        });
        return Response.json({ action: "queued", from });
      } catch (e: any) {
        return Response.json({ error: e?.message || "bad request" }, { status: 400 });
      }
    }

    // ── Debug: simulate an inbound SMS without a real messaging profile ──
    if (url.pathname === "/debug/message" && req.method === "POST") {
      const body = (await req.json().catch(() => ({}))) as any;
      const from = String(body.from || "+17177247292");
      const to = String(body.to || "+16282564655");
      const text = String(body.text || "hi, this is a test message");
      await env.SUPPORT.idFromName(actorName(from)).receive({ text, from, to });
      return Response.json({ action: "queued", from, to });
    }

    return new Response("not found", { status: 404 });
  },
};
