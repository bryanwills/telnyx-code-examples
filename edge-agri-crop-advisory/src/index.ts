// Re-export the actor class so it ships with the bundle.
export { CropAdvisory } from "./cropAdvisory";
import type { CropAdvisory, Advisory } from "./cropAdvisory";

import {
  type ActorNamespace,
  type ActorStub,
  type IdFromNameOptions,
} from "@telnyx/edge-runtime";

type CropAdvisoryStub = ActorStub &
  Pick<
    CropAdvisory,
    "addAdvisory" | "getAdvisory" | "listAdvisories" | "getCropStats"
  >;

interface CropAdvisoryNamespace extends ActorNamespace {
  idFromName(name: string, options?: IdFromNameOptions): CropAdvisoryStub;
}

interface Env {
  CROP_ADVISORY: CropAdvisoryNamespace;
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

async function fetchUrlText(url: string): Promise<string> {
  const resp = await fetch(url, {
    headers: { "User-Agent": "Mozilla/5.0" },
  });
  if (!resp.ok) throw new Error(`failed to fetch URL: HTTP ${resp.status}`);
  const contentType = resp.headers.get("content-type") || "";
  let text = await resp.text();

  // Strip HTML tags if it's HTML. Loop until stable (CodeQL: incomplete sanitization).
  if (contentType.includes("html") || text.toLowerCase().startsWith("<!doctype") || text.startsWith("<html")) {
    let prev: string;
    do {
      prev = text;
      text = text
        .replace(/<script[^>]*>[\s\S]*?<\/script>/gi, "")
        .replace(/<style[^>]*>[\s\S]*?<\/style>/gi, "")
        .replace(/<[^>]+>/g, " ")
        .replace(/\s+/g, " ")
        .trim();
    } while (text !== prev);
  }
  return text;
}

const SYSTEM_PROMPT = `You are an agricultural extension agronomist. A farmer will describe a crop issue. Analyze it and return structured JSON only:

{
  "crop_type": "the crop name (corn, wheat, tomato, soybean, rice, potato, etc.)",
  "issue_type": "disease | pest | nutrient | water | weather | unknown",
  "severity": "low | medium | high | critical",
  "confidence": 0.0,
  "recommendation": "specific treatment or next step in 1-2 sentences"
}

Classification guide:
- disease: fungal, bacterial, viral signs (spots, mildew, blight, rot, wilt)
- pest: insect damage, larvae, holes in leaves, visible bugs
- nutrient: yellowing, purpling, stunting, deficiency symptoms
- water: over/under watering, flooding, drought stress
- weather: frost, hail, heat stress, wind damage

Severity guide:
- low: affects <10% of the plant, cosmetic
- medium: spreading, affects 10-40%, needs treatment soon
- high: >40% affected, crop at risk
- critical: imminent crop loss without immediate intervention

Set escalate=true ONLY for critical severity.`;

async function classifyCropIssue(apiKey: string, description: string): Promise<Omit<Advisory, "id" | "farmer_description" | "source" | "generated_at" | "escalated_to">> {
  const userPrompt = `Farmer's description: "${description.slice(0, 4000)}"`;
  const resp = await fetch(`${TELNYX_API}/ai/chat/completions`, {
    method: "POST",
    headers: authHeaders(apiKey),
    body: JSON.stringify({
      model: INFERENCE_MODEL,
      messages: [
        { role: "system", content: SYSTEM_PROMPT },
        { role: "user", content: userPrompt },
      ],
      max_tokens: 4000,
      temperature: 0.2,
    }),
  });

  if (!resp.ok) {
    const err = await resp.text();
    throw new Error(`inference failed: HTTP ${resp.status}: ${err}`);
  }

  const data = (await resp.json()) as any;
  let content = data?.choices?.[0]?.message?.content;
  if (!content) throw new Error("no content from model");
  content = content.trim();
  if (content.startsWith("```")) {
    content = content.split("\n").slice(1).join("\n").replace(/```/g, "").trim();
  }
  const parsed = JSON.parse(content);
  return {
    crop_type: parsed.crop_type || "unknown",
    issue_type: parsed.issue_type || "unknown",
    severity: parsed.severity || "medium",
    confidence: typeof parsed.confidence === "number" ? Math.min(1, Math.max(0, parsed.confidence)) : 0.5,
    recommendation: parsed.recommendation || "Consult your local extension office.",
    escalate: parsed.escalate === true,
  };
}

const ACTOR_NAME = "global";

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url);

    // Health checks
    if (url.pathname === "/health/liveness") return new Response("ok");
    if (url.pathname === "/health/readiness") return new Response("ok");

    const stub = env.CROP_ADVISORY.idFromName(ACTOR_NAME);

    // ── POST /advisory ───────────────────────────────────────────────
    if (url.pathname === "/advisory" && req.method === "POST") {
      const body = (await req.json().catch(() => ({}))) as any;
      let description = (body.description || "").trim();
      const sourceUrl = (body.url || "").trim();

      if (!description && !sourceUrl) {
        return Response.json({ error: "either description or url field is required" }, { status: 400 });
      }

      // If only a URL was given, fetch and summarize it into a description
      if (sourceUrl && !description) {
        try {
          description = await fetchUrlText(sourceUrl);
          description = description.slice(0, 4000);
        } catch (e: any) {
          return Response.json({ error: e?.message || "failed to fetch URL" }, { status: 400 });
        }
      }

      if (description.length < 20) {
        return Response.json({ error: "description is too short (min 20 chars)" }, { status: 400 });
      }

      try {
        const apiKey = process.env.TELNYX_API_KEY ?? "";
        if (!apiKey) throw new Error("TELNYX_API_KEY not configured");

        const classification = await classifyCropIssue(apiKey, description);

        const advisory: Advisory = {
          id: `adv-${Date.now().toString(36)}-${(actorCounter++).toString(36)}`,
          farmer_description: description.slice(0, 500),
          source: sourceUrl || "text",
          ...classification,
          generated_at: new Date().toISOString(),
        };

        if (advisory.escalate) {
          advisory.escalated_to = "agronomist-on-call";
        }

        await stub.addAdvisory(advisory);
        return Response.json(advisory, { status: 201 });
      } catch (e: any) {
        return Response.json({ error: e?.message || "classification failed" }, { status: 500 });
      }
    }

    // ── GET /advisories ──────────────────────────────────────────────
    if (url.pathname === "/advisories" && req.method === "GET") {
      const limit = Math.min(50, Math.max(1, parseInt(url.searchParams.get("limit") || "20", 10)));
      const advisories = await stub.listAdvisories(limit);
      return Response.json({ advisories });
    }

    // ── GET /advisories/<id> ─────────────────────────────────────────
    const advisoryMatch = url.pathname.match(/^\/advisories\/([^/]+)$/);
    if (advisoryMatch && req.method === "GET") {
      const id = advisoryMatch[1]!;
      const advisory = await stub.getAdvisory(id);
      if (!advisory) return Response.json({ error: "advisory not found" }, { status: 404 });
      return Response.json(advisory);
    }

    // ── GET /stats ───────────────────────────────────────────────────
    if (url.pathname === "/stats" && req.method === "GET") {
      const stats = await stub.getCropStats();
      return Response.json(stats);
    }

    return new Response("not found", { status: 404 });
  },
};
