export { RateLimitAgent, RateLimitRegistry } from "./rateLimitAgent";
import type { RateLimitAgent, RateLimitRegistry } from "./rateLimitAgent";

import {
  type ActorNamespace,
  type ActorStub,
  type IdFromNameOptions,
} from "@telnyx/edge-runtime";

type RateLimitStub = ActorStub &
  Pick<
    RateLimitAgent,
    | "checkRequest"
    | "checkLimit"
    | "allow"
    | "reject"
    | "sendAlert"
    | "finalize"
    | "getStatus"
    | "getSummary"
    | "getWindowCount"
    | "resetKey"
  >;

interface RateLimitNamespace extends ActorNamespace {
  idFromName(name: string, options?: IdFromNameOptions): RateLimitStub;
}

type RegistryStub = ActorStub &
  Pick<RateLimitRegistry, "record" | "listKeys" | "getKey">;

interface RegistryNamespace extends ActorNamespace {
  idFromName(name: string, options?: IdFromNameOptions): RegistryStub;
}

interface Env {
  RATE_AGENT: RateLimitNamespace;
  REGISTRY: RegistryNamespace;
  TELNYX_API_KEY: string;
  ALERT_PHONE: string;
  SENDER_PHONE: string;
  RATE_LIMIT: string;
  WINDOW_SECONDS: string;
  ALERT_THRESHOLD: string;
}

// Dapr-safe actor names: no "+", no special chars (RFC 1123 job-name-safe).
function actorName(id: string): string {
  return id.replace(/[^0-9a-zA-Z.-]/g, "");
}

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url);

    // ── Health ─────────────────────────────────────────────────────────
    if (url.pathname === "/health/liveness") return new Response("ok");
    if (url.pathname === "/health/readiness") return new Response("ok");

    // ── Check a request against the rate limit ─────────────────────────
    if (req.method === "POST" && url.pathname === "/check") {
      return handleCheck(req, env);
    }

    // ── Get status for a specific key ──────────────────────────────────
    if (req.method === "GET" && url.pathname.startsWith("/status/")) {
      const key = decodeURIComponent(url.pathname.split("/status/")[1]);
      if (!key) return Response.json({ error: "missing key" }, { status: 400 });

      try {
        const summary = await env.RATE_AGENT.idFromName(actorName(key)).getSummary();
        return Response.json(summary);
      } catch (e: any) {
        return Response.json({ error: e?.message || "failed to get status" }, { status: 500 });
      }
    }

    // ── Get current window count for a key ──────────────────────────────
    if (req.method === "GET" && url.pathname.startsWith("/count/")) {
      const key = decodeURIComponent(url.pathname.split("/count/")[1]);
      if (!key) return Response.json({ error: "missing key" }, { status: 400 });

      try {
        const result = await env.RATE_AGENT.idFromName(actorName(key)).getWindowCount(key);
        return Response.json(result);
      } catch (e: any) {
        return Response.json({ error: e?.message || "failed to get count" }, { status: 500 });
      }
    }

    // ── List all tracked keys ──────────────────────────────────────────
    if (req.method === "GET" && url.pathname === "/keys") {
      try {
        const keys = await env.REGISTRY.idFromName("shared").listKeys();
        return Response.json({ keys, total: keys.length });
      } catch (e: any) {
        return Response.json({ error: e?.message || "failed to list keys" }, { status: 500 });
      }
    }

    // ── Reset a key's counter ──────────────────────────────────────────
    if (req.method === "POST" && url.pathname.startsWith("/reset/")) {
      const key = decodeURIComponent(url.pathname.split("/reset/")[1]);
      if (!key) return Response.json({ error: "missing key" }, { status: 400 });

      try {
        const result = await env.RATE_AGENT.idFromName(actorName(key)).resetKey(key);
        return Response.json(result);
      } catch (e: any) {
        return Response.json({ error: e?.message || "failed to reset" }, { status: 500 });
      }
    }

    // ── Simulate a burst of requests (for testing) ─────────────────────
    if (req.method === "POST" && url.pathname === "/simulate") {
      return handleSimulate(req, env);
    }

    // ── Get config ─────────────────────────────────────────────────────
    if (req.method === "GET" && url.pathname === "/config") {
      return Response.json({
        rateLimit: parseInt(env.RATE_LIMIT, 10) || 100,
        windowSeconds: parseInt(env.WINDOW_SECONDS, 10) || 60,
        alertThreshold: parseInt(env.ALERT_THRESHOLD, 10) || 10,
      });
    }

    return new Response("not found", { status: 404 });
  },
};

// ── Check handler ────────────────────────────────────────────────────────
async function handleCheck(req: Request, env: Env): Promise<Response> {
  try {
    const body = (await req.json().catch(() => ({}))) as {
      key?: string;
    };

    if (!body.key) {
      return Response.json({ error: "Missing field: key" }, { status: 400 });
    }

    const agentId = actorName(body.key);
    await env.RATE_AGENT.idFromName(agentId).checkRequest({ key: body.key });

    // Record in registry
    const summary = await env.RATE_AGENT.idFromName(agentId).getSummary();
    await env.REGISTRY.idFromName("shared").record({
      key: body.key,
      totalRequests: summary.totalRequests,
      allowedRequests: summary.allowedRequests,
      rejectedRequests: summary.rejectedRequests,
      alertTriggered: summary.alertTriggered,
      lastRequestAt: summary.lastRequestAt,
    });

    const status = summary.status === "allowed" ? 200 : summary.status === "rejected" || summary.status === "done" ? 429 : 200;

    return Response.json(
      {
        key: body.key,
        action: summary.status === "allowed" ? "allowed" : "rejected",
        currentCount: summary.currentCount,
        limit: summary.limit,
        windowSeconds: summary.windowSeconds,
        totalRequests: summary.totalRequests,
        allowedRequests: summary.allowedRequests,
        rejectedRequests: summary.rejectedRequests,
        alertTriggered: summary.alertTriggered,
      },
      { status },
    );
  } catch (e: any) {
    return Response.json({ error: e?.message || "check failed" }, { status: 500 });
  }
}

// ── Simulate handler (for testing rate limits) ────────────────────────────
async function handleSimulate(req: Request, env: Env): Promise<Response> {
  try {
    const body = (await req.json().catch(() => ({}))) as {
      key?: string;
      count?: number;
    };

    const key = body.key || "+18005551234";
    const count = body.count ?? 5;

    if (count > 1000) {
      return Response.json({ error: "Max 1000 requests per simulate" }, { status: 400 });
    }

    const agent = env.RATE_AGENT.idFromName(actorName(key));
    const results: { request: number; action: string; currentCount: number }[] = [];

    for (let i = 0; i < count; i++) {
      await agent.checkRequest({ key });
      const summary = await agent.getSummary();
      results.push({
        request: i + 1,
        action: summary.status === "allowed" ? "allowed" : "rejected",
        currentCount: summary.currentCount,
      });
    }

    // Record in registry
    const finalSummary = await agent.getSummary();
    await env.REGISTRY.idFromName("shared").record({
      key,
      totalRequests: finalSummary.totalRequests,
      allowedRequests: finalSummary.allowedRequests,
      rejectedRequests: finalSummary.rejectedRequests,
      alertTriggered: finalSummary.alertTriggered,
      lastRequestAt: finalSummary.lastRequestAt,
    });

    return Response.json({
      key,
      simulated: count,
      allowed: results.filter((r) => r.action === "allowed").length,
      rejected: results.filter((r) => r.action === "rejected").length,
      alertTriggered: finalSummary.alertTriggered,
      results,
    });
  } catch (e: any) {
    return Response.json({ error: e?.message || "simulate failed" }, { status: 500 });
  }
}
