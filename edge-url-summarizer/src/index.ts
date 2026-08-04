// Re-export the actor class so it ships with the bundle.
export { Summarizer } from "./summarizer";
import type { Summarizer } from "./summarizer";

import {
  type ActorNamespace,
  type ActorStub,
  type IdFromNameOptions,
} from "@telnyx/edge-runtime";

type SummarizerStub = ActorStub &
  Pick<
    Summarizer,
    | "getSummary"
    | "cacheSummary"
    | "recordHit"
    | "recordMiss"
    | "invalidate"
    | "getSummaryStats"
    | "listCached"
  >;

interface SummarizerNamespace extends ActorNamespace {
  idFromName(name: string, options?: IdFromNameOptions): SummarizerStub;
}

interface Env {
  SUMMARIZER: SummarizerNamespace;
  TELNYX_API_KEY: string;
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

async function fetchUrlText(url: string): Promise<string> {
  const resp = await fetch(url, {
    headers: { "User-Agent": "Mozilla/5.0" },
  });
  if (!resp.ok) throw new Error(`failed to fetch URL: HTTP ${resp.status}`);
  const contentType = resp.headers.get("content-type") || "";
  let text = await resp.text();

  // If it's HTML-like, remove script/style blocks and then neutralize tag delimiters.
  // Using single-character replacement for `<` and `>` avoids incomplete
  // multi-character sanitization issues.
  if (contentType.includes("html") || text.toLowerCase().startsWith("<!doctype") || text.startsWith("<html")) {
    text = text
      .replace(/<script[^>]*>[\s\S]*?<\/script>/gi, " ")
      .replace(/<style[^>]*>[\s\S]*?<\/style>/gi, " ")
      .replace(/[<>]/g, " ")
        .replace(/<script\b[^>]*>[\s\S]*?<\/script\b[^>]*>/gi, "")
        .replace(/<style\b[^>]*>[\s\S]*?<\/style\b[^>]*>/gi, "")
  }
  return text;
}

function extractTitle(text: string): string | undefined {
  const titleMatch = text.match(/<title[^>]*>([^<]+)<\/title>/i);
  if (titleMatch) return titleMatch[1].trim();
  const ogMatch = text.match(/<meta[^>]+property=["']og:title["'][^>]+content=["']([^"']+)["']/i);
  if (ogMatch) return ogMatch[1].trim();
  return undefined;
}

async function summarizeViaInference(text: string): Promise<string[]> {
  const apiKey = process.env.TELNYX_API_KEY ?? "";
  if (!apiKey) throw new Error("TELNYX_API_KEY not configured");
  const systemPrompt = `You are a summarizer. Summarize the given text into exactly 3 concise bullet points. Return JSON only: {"bullets": ["point 1", "point 2", "point 3"]}`;
  const userPrompt = `Summarize this text into 3 bullet points:\n\n${text.slice(0, 6000)}`;

  const resp = await fetch(`${TELNYX_API}/ai/chat/completions`, {
    method: "POST",
    headers: authHeaders(apiKey),
    body: JSON.stringify({
      model: INFERENCE_MODEL,
      messages: [
        { role: "system", content: systemPrompt },
        { role: "user", content: userPrompt },
      ],
      max_tokens: 4000,
      temperature: 0.3,
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
  return parsed.bullets || [];
}

const ACTOR_NAME = "global";

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url);

    // Health checks
    if (url.pathname === "/health/liveness") return new Response("ok");
    if (url.pathname === "/health/readiness") return new Response("ok");

    const stub = env.SUMMARIZER.idFromName(ACTOR_NAME);

    // ── POST /summarize ──────────────────────────────────────────────
    if (url.pathname === "/summarize" && req.method === "POST") {
      const body = (await req.json().catch(() => ({}))) as any;
      const targetUrl = body.url?.trim();
      if (!targetUrl) return Response.json({ error: "url field is required" }, { status: 400 });

      // Check cache first
      const cached = await stub.getSummary(targetUrl);
      if (cached) {
        await stub.recordHit();
        return Response.json({ ...cached, cached: true });
      }

      await stub.recordMiss();

      try {
        const text = await fetchUrlText(targetUrl);
        const title = extractTitle(text);
        const bullets = await summarizeViaInference(text);
        const summary = {
          url: targetUrl,
          title: title || targetUrl,
          bullets,
          word_count: text.split(/\s+/).length,
          generated_at: new Date().toISOString(),
        };
        await stub.cacheSummary(targetUrl, summary);
        return Response.json({ ...summary, cached: false }, { status: 201 });
      } catch (e: any) {
        return Response.json({ error: e?.message || "summarize failed" }, { status: 500 });
      }
    }

    // ── GET /summarize/cached ────────────────────────────────────────
    if (url.pathname === "/summarize/cached" && req.method === "GET") {
      const targetUrl = url.searchParams.get("url");
      if (!targetUrl) return Response.json({ error: "url query param is required" }, { status: 400 });
      const cached = await stub.getSummary(targetUrl);
      if (cached) {
        return Response.json({ ...cached, cached: true });
      }
      return Response.json({ error: "not cached" }, { status: 404 });
    }

    // ── POST /summarize/refresh ──────────────────────────────────────
    if (url.pathname === "/summarize/refresh" && req.method === "POST") {
      const body = (await req.json().catch(() => ({}))) as any;
      const targetUrl = body.url?.trim();
      if (!targetUrl) return Response.json({ error: "url field is required" }, { status: 400 });
      await stub.invalidate(targetUrl);
      return Response.json({ url: targetUrl, invalidated: true });
    }

    // ── GET /stats ───────────────────────────────────────────────────
    if (url.pathname === "/stats" && req.method === "GET") {
      const stats = await stub.getSummaryStats();
      return Response.json(stats);
    }

    // ── GET /cached ──────────────────────────────────────────────────
    if (url.pathname === "/cached" && req.method === "GET") {
      const urls = await stub.listCached();
      return Response.json({ urls });
    }

    return new Response("not found", { status: 404 });
  },
};
