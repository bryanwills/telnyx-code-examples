export { CacheAgent } from "./cacheAgent";
import type { CacheAgent } from "./cacheAgent";

import {
  type ActorNamespace,
  type ActorStub,
  type IdFromNameOptions,
} from "@telnyx/edge-runtime";

type CacheAgentStub = ActorStub &
  Pick<
    CacheAgent,
    "start" | "invalidate" | "updateManifest" | "notify" | "getStatus" | "checkCacheStatus" | "clearCacheFlag"
  >;

interface CacheAgentNamespace extends ActorNamespace {
  idFromName(name: string, options?: IdFromNameOptions): CacheAgentStub;
}

interface Env {
  CACHE: CacheAgentNamespace;
  TELNYX_API_KEY: string;
  ALERT_PHONE: string;
  SENDER_PHONE: string;
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

    // ── Trigger cache invalidation ─────────────────────────────────────
    if (req.method === "POST" && url.pathname === "/invalidate") {
      try {
        const body = (await req.json().catch(() => ({}))) as {
          content_id?: string;
          content_version?: string;
          locations?: string[];
        };

        if (!body.content_id) {
          return Response.json(
            { error: "Missing 'content_id' (what changed — URL, asset path, etc.)" },
            { status: 400 },
          );
        }

        if (!body.content_version) {
          return Response.json(
            { error: "Missing 'content_version' (new version identifier)" },
            { status: 400 },
          );
        }

        if (!body.locations || !Array.isArray(body.locations) || body.locations.length === 0) {
          return Response.json(
            { error: "Missing 'locations' (array of edge location names to invalidate)" },
            { status: 400 },
          );
        }

        const agentId = actorName(`${body.content_id}-${body.content_version}-${Date.now()}`);
        await env.CACHE.idFromName(agentId).start({
          contentId: body.content_id,
          contentVersion: body.content_version,
          locations: body.locations,
        });

        return Response.json({
          action: "queued",
          agentId,
          contentId: body.content_id,
          contentVersion: body.content_version,
          locations: body.locations,
          statusUrl: `/status/${agentId}`,
        });
      } catch (e: any) {
        return Response.json({ error: e?.message || "invalidation failed" }, { status: 500 });
      }
    }

    // ── Check invalidation status ──────────────────────────────────────
    if (req.method === "GET" && url.pathname.startsWith("/status/")) {
      const agentId = url.pathname.split("/status/")[1];
      if (!agentId) return Response.json({ error: "missing agent id" }, { status: 400 });

      try {
        const state = await env.CACHE.idFromName(agentId).getStatus();
        return Response.json(state);
      } catch (e: any) {
        return Response.json({ error: e?.message || "failed to get state" }, { status: 500 });
      }
    }

    // ── Check cache status for a specific location ─────────────────────
    if (req.method === "GET" && url.pathname.startsWith("/cache-status/")) {
      const parts = url.pathname.split("/cache-status/")[1];
      const [location, contentId] = parts.split("/").map(decodeURIComponent);

      if (!location || !contentId) {
        return Response.json({ error: "Missing location or contentId" }, { status: 400 });
      }

      try {
        const agentId = actorName(`status-${contentId}`);
        const status = await env.CACHE.idFromName(agentId).checkCacheStatus(location, contentId);
        return Response.json({ location, contentId, ...status });
      } catch (e: any) {
        return Response.json({ error: e?.message || "failed to check cache status" }, { status: 500 });
      }
    }

    // ── Clear cache flag for a location (simulate cache refresh) ──────
    if (req.method === "POST" && url.pathname.startsWith("/cache-clear/")) {
      const parts = url.pathname.split("/cache-clear/")[1];
      const [location, contentId] = parts.split("/").map(decodeURIComponent);

      if (!location || !contentId) {
        return Response.json({ error: "Missing location or contentId" }, { status: 400 });
      }

      try {
        const agentId = actorName(`clear-${contentId}`);
        await env.CACHE.idFromName(agentId).clearCacheFlag(location, contentId);
        return Response.json({ action: "cleared", location, contentId });
      } catch (e: any) {
        return Response.json({ error: e?.message || "failed to clear cache flag" }, { status: 500 });
      }
    }

    // ── List all edge locations (demo) ────────────────────────────────
    if (req.method === "GET" && url.pathname === "/locations") {
      const demoLocations = [
        "us-east-1",
        "us-west-1",
        "eu-central-1",
        "ap-southeast-1",
      ];
      return Response.json({ locations: demoLocations });
    }

    return new Response("not found", { status: 404 });
  },
};
