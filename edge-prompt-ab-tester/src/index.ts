// Re-export the actor class so it ships with the bundle.
export { ABTester } from "./abTester";
import type { ABTester, Experiment } from "./abTester";

import {
  type ActorNamespace,
  type ActorStub,
  type IdFromNameOptions,
} from "@telnyx/edge-runtime";

type ABTesterStub = ActorStub &
  Pick<
    ABTester,
    "createExperiment" | "vote" | "closeExperiment" | "getExperiment" | "listExperiments" | "getStats"
  >;

interface ABTesterNamespace extends ActorNamespace {
  idFromName(name: string, options?: IdFromNameOptions): ABTesterStub;
}

interface Env {
  AB_TESTER: ABTesterNamespace;
  AI_MODEL: string;
}

const TELNYX_API = "https://api.telnyx.com/v2";
const INFERENCE_MODEL = "zai-org/GLM-5.2";

function authHeaders(apiKey: string): HeadersInit {
  return {
    Authorization: `Bearer ${apiKey}`,
    "Content-Type": "application/json",
  };
}

let actorCounter = 0;

async function runPrompt(apiKey: string, systemPrompt: string, task: string): Promise<string> {
  const resp = await fetch(`${TELNYX_API}/ai/chat/completions`, {
    method: "POST",
    headers: authHeaders(apiKey),
    body: JSON.stringify({
      model: INFERENCE_MODEL,
      messages: [
        { role: "system", content: systemPrompt },
        { role: "user", content: task },
      ],
      max_tokens: 4000,
      temperature: 0.7,
    }),
  });

  if (!resp.ok) {
    const err = await resp.text();
    throw new Error(`inference failed: HTTP ${resp.status}: ${err}`);
  }

  const data = (await resp.json()) as any;
  let content = data?.choices?.[0]?.message?.content;
  return content?.trim() || "(no content)";
}

const ACTOR_NAME = "global";

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url);

    // Health checks
    if (url.pathname === "/health/liveness") return new Response("ok");
    if (url.pathname === "/health/readiness") return new Response("ok");

    const stub = env.AB_TESTER.idFromName(ACTOR_NAME);

    // ── POST /experiments ────────────────────────────────────────────
    // Create a new A/B experiment: run both prompts against the same task,
    // return both responses so the user can vote.
    if (url.pathname === "/experiments" && req.method === "POST") {
      const body = (await req.json().catch(() => ({}))) as any;
      const task = (body.task || "").trim();
      const promptA = (body.variant_a || "").trim();
      const promptB = (body.variant_b || "").trim();

      if (!task || !promptA || !promptB) {
        return Response.json({ error: "task, variant_a, and variant_b are all required" }, { status: 400 });
      }

      const apiKey = process.env.TELNYX_API_KEY ?? "";
      if (!apiKey) return Response.json({ error: "TELNYX_API_KEY not configured" }, { status: 500 });

      try {
        const [respA, respB] = await Promise.all([
          runPrompt(apiKey, promptA, task),
          runPrompt(apiKey, promptB, task),
        ]);

        const experiment: Experiment = {
          id: `exp-${Date.now().toString(36)}-${(actorCounter++).toString(36)}`,
          task,
          variant_a: { prompt: promptA, response: respA },
          variant_b: { prompt: promptB, response: respB },
          votes_a: 0,
          votes_b: 0,
          status: "open",
          created_at: new Date().toISOString(),
        };

        await stub.createExperiment(experiment);
        return Response.json(experiment, { status: 201 });
      } catch (e: any) {
        return Response.json({ error: e?.message || "experiment failed" }, { status: 500 });
      }
    }

    // ── POST /experiments/<id>/vote ──────────────────────────────────
    const voteMatch = url.pathname.match(/^\/experiments\/([^/]+)\/vote$/);
    if (voteMatch && req.method === "POST") {
      const experimentId = voteMatch[1]!;
      const body = (await req.json().catch(() => ({}))) as any;
      const variant = (body.variant || "").toLowerCase();
      if (variant !== "a" && variant !== "b") {
        return Response.json({ error: "variant must be 'a' or 'b'" }, { status: 400 });
      }
      const updated = await stub.vote(experimentId, variant);
      if (!updated) {
        return Response.json({ error: "experiment not found or already closed" }, { status: 404 });
      }
      return Response.json(updated);
    }

    // ── POST /experiments/<id>/close ─────────────────────────────────
    const closeMatch = url.pathname.match(/^\/experiments\/([^/]+)\/close$/);
    if (closeMatch && req.method === "POST") {
      const experimentId = closeMatch[1]!;
      const closed = await stub.closeExperiment(experimentId);
      if (!closed) return Response.json({ error: "experiment not found" }, { status: 404 });
      return Response.json(closed);
    }

    // ── GET /experiments ─────────────────────────────────────────────
    if (url.pathname === "/experiments" && req.method === "GET") {
      const limit = Math.min(50, Math.max(1, parseInt(url.searchParams.get("limit") || "20", 10)));
      const experiments = await stub.listExperiments(limit);
      return Response.json({ experiments });
    }

    // ── GET /experiments/<id> ────────────────────────────────────────
    const experimentMatch = url.pathname.match(/^\/experiments\/([^\/]+)$/);
    if (experimentMatch && req.method === "GET") {
      const id = experimentMatch[1]!;
      const experiment = await stub.getExperiment(id);
      if (!experiment) return Response.json({ error: "experiment not found" }, { status: 404 });
      return Response.json(experiment);
    }

    // ── GET /stats ───────────────────────────────────────────────────
    if (url.pathname === "/stats" && req.method === "GET") {
      const stats = await stub.getStats();
      return Response.json(stats);
    }

    return new Response("not found", { status: 404 });
  },
};
