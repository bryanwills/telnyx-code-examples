import Telnyx from "telnyx";
import { BRAND_VERSION, demoHtml } from "./demo-html";
import { QuizAgent } from "./quiz-agent";
import type { Env, TelnyxMessageWebhook } from "./types";

export { QuizAgent };

const telnyxClient = new Telnyx({ apiKey: "unused-webhook-verification-only" });

function demoUiEnabled(env: Env): boolean {
  return env.DEMO_MODE !== "false";
}

function smsTransportEnabled(env: Env): boolean {
  return env.SMS_TRANSPORT !== "demo";
}

function json(data: unknown, init: ResponseInit = {}): Response {
  return new Response(JSON.stringify(data), {
    ...init,
    headers: {
      "content-type": "application/json",
      "cache-control": "no-store",
      ...(init.headers || {}),
    },
  });
}

function badRequest(message: string): Response {
  return json({ error: message }, { status: 400 });
}

function validatePhone(value: unknown, fallback = ""): string {
  if (typeof value !== "string") return fallback;
  const phone = value.trim();
  return /^\+[1-9]\d{6,14}$/.test(phone) ? phone : fallback;
}

function actorNameForPhone(phone: string): string {
  return `phone-${phone.replace(/\D/g, "")}`;
}

async function parseJson<T>(request: Request): Promise<T> {
  return await request.json() as T;
}

async function verifyAndParseWebhook(request: Request, env: Env): Promise<TelnyxMessageWebhook> {
  const body = await request.text();
  const publicKey = await env.SECRETS?.get("TELNYX_PUBLIC_KEY");
  if (!publicKey) {
    throw new Error("TELNYX_PUBLIC_KEY is required when SMS transport is enabled");
  }
  const headers = Object.fromEntries(request.headers.entries());

  return telnyxClient.webhooks.unwrap(body, {
    headers,
    key: publicKey,
  }) as TelnyxMessageWebhook;
}

async function handleSend(request: Request, env: Env): Promise<Response> {
  if (!demoUiEnabled(env)) return new Response("not found", { status: 404 });

  const body = await parseJson<{ text?: string; from?: string }>(request);
  const text = typeof body.text === "string" ? body.text.trim() : "";
  const from = validatePhone(body.from, env.DEMO_SENDER_NUMBER || "+15551234567");
  const to = validatePhone(env.DEMO_FROM_NUMBER, "+15557654321");

  if (!text) return badRequest("text is required");
  if (!from) return badRequest("from must be E.164, for example +14155550100");

  await env.QUIZ.idFromName(actorNameForPhone(from)).receive({
    text,
    from,
    to,
    eventId: `demo:${crypto.randomUUID()}`,
  });

  return json({ ok: true });
}

async function handleEvents(request: Request, env: Env): Promise<Response> {
  if (!demoUiEnabled(env)) return new Response("not found", { status: 404 });

  const url = new URL(request.url);
  const from = validatePhone(url.searchParams.get("from"), env.DEMO_SENDER_NUMBER || "+15551234567");
  const limit = Number(url.searchParams.get("limit") || "50");
  const events = await env.QUIZ.idFromName(actorNameForPhone(from)).getEvents(limit);

  return json({ events });
}

async function handleStatus(request: Request, env: Env): Promise<Response> {
  if (!demoUiEnabled(env)) return new Response("not found", { status: 404 });

  const url = new URL(request.url);
  const from = validatePhone(url.searchParams.get("from"), env.DEMO_SENDER_NUMBER || "+15551234567");
  const status = await env.QUIZ.idFromName(actorNameForPhone(from)).getStatus();

  return json({ status });
}

async function handleWebhook(request: Request, env: Env): Promise<Response> {
  let hook: TelnyxMessageWebhook;
  try {
    hook = smsTransportEnabled(env)
      ? await verifyAndParseWebhook(request, env)
      : await parseJson<TelnyxMessageWebhook>(request);
  } catch (error) {
    return json({ error: error instanceof Error ? error.message : "Invalid webhook" }, { status: 401 });
  }

  if (hook.data.event_type !== "message.received") {
    return json({ ignored: true, event_type: hook.data.event_type });
  }

  const from = hook.data.payload.from.phone_number;
  const to = hook.data.payload.to[0]?.phone_number || "";
  const text = hook.data.payload.text || "";
  const eventId = hook.data.id;

  if (!from || !to || !text || !eventId) return badRequest("Invalid message.received payload");

  await env.QUIZ.idFromName(actorNameForPhone(from)).receive({ text, from, to, eventId });
  return json({ ok: true });
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    if (request.method === "GET" && url.pathname === "/health") {
      return json({
        ok: true,
        demo: demoUiEnabled(env),
        smsTransport: smsTransportEnabled(env) ? "enabled" : "demo",
        production: smsTransportEnabled(env),
        brand: BRAND_VERSION,
      });
    }

    if (request.method === "GET" && url.pathname === "/version") {
      return json({ brand: BRAND_VERSION });
    }

    if (request.method === "GET" && url.pathname === "/" && demoUiEnabled(env)) {
      return new Response(demoHtml(env.DEMO_SENDER_NUMBER || "+15551234567"), {
        headers: {
          "content-type": "text/html; charset=utf-8",
          "cache-control": "no-store",
          "x-brand-version": BRAND_VERSION,
        },
      });
    }

    if (request.method === "POST" && url.pathname === "/send") {
      return handleSend(request, env);
    }

    if (request.method === "GET" && url.pathname === "/events") {
      return handleEvents(request, env);
    }

    if (request.method === "GET" && url.pathname === "/status") {
      return handleStatus(request, env);
    }

    if (request.method === "POST" && (url.pathname === "/" || url.pathname === "/webhooks/messaging")) {
      return handleWebhook(request, env);
    }

    return new Response("not found", { status: 404 });
  },
};
