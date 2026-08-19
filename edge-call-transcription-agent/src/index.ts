export { TranscribeAgent, TranscriptRegistry } from "./transcribeAgent";
import type { TranscribeAgent, TranscriptRegistry, TranscriptRecord } from "./transcribeAgent";

import {
  type ActorNamespace,
  type ActorStub,
  type IdFromNameOptions,
} from "@telnyx/edge-runtime";

type TranscribeAgentStub = ActorStub &
  Pick<
    TranscribeAgent,
    | "recordStart"
    | "setTranscribing"
    | "appendTranscript"
    | "onHangup"
    | "summarize"
    | "store"
    | "notify"
    | "getDebugState"
    | "getStoredTranscript"
  >;

interface TranscribeAgentNamespace extends ActorNamespace {
  idFromName(name: string, options?: IdFromNameOptions): TranscribeAgentStub;
}

type RegistryStub = ActorStub & Pick<TranscriptRegistry, "record" | "list" | "get">;

interface RegistryNamespace extends ActorNamespace {
  idFromName(name: string, options?: IdFromNameOptions): RegistryStub;
}

interface Env {
  TRANSCRIBE: TranscribeAgentNamespace;
  REGISTRY: RegistryNamespace;
  TELNYX_API_KEY: string;
  AI_MODEL: string;
  SMS_FROM: string;
  SMS_TO: string;
}

const TELNYX_API = "https://api.telnyx.com/v2";
const GREETING =
  "Hi, I'm a Telnyx transcription agent. I'll transcribe our call and text you a summary when we hang up. Please go ahead.";
const TTS_VOICE = "Telnyx.KokoroTTS.af";

function authHeaders(apiKey: string): HeadersInit {
  return {
    Authorization: `Bearer ${apiKey}`,
    "Content-Type": "application/json",
  };
}

function encodeClientState(state: Record<string, string>): string {
  return btoa(JSON.stringify(state));
}

function decodeClientState(clientState: unknown): Record<string, string> {
  if (typeof clientState !== "string" || !clientState) return {};
  try {
    const decoded = JSON.parse(atob(clientState));
    return decoded && typeof decoded === "object" ? decoded : {};
  } catch {
    return {};
  }
}

function actorName(callControlId: string): string {
  // Dapr-safe: RFC 1123 — no "+", no special chars
  return callControlId.replace(/[^0-9a-zA-Z.-]/g, "");
}

function getApiKey(): string {
  const apiKey = process.env.TELNYX_API_KEY ?? "";
  if (!apiKey) throw new Error("TELNYX_API_KEY not configured");
  return apiKey;
}

async function answerCall(apiKey: string, callControlId: string): Promise<Response> {
  return fetch(`${TELNYX_API}/calls/${callControlId}/actions/answer`, {
    method: "POST",
    headers: authHeaders(apiKey),
  });
}

async function speakText(apiKey: string, callControlId: string, text: string): Promise<Response> {
  return fetch(`${TELNYX_API}/calls/${callControlId}/actions/speak`, {
    method: "POST",
    headers: authHeaders(apiKey),
    body: JSON.stringify({
      payload: text,
      voice: TTS_VOICE,
      language: "en-US",
      client_state: encodeClientState({ speak_stage: "greeting" }),
      command_id: `transcribe-greeting-${Date.now()}`,
    }),
  });
}

async function startTranscription(apiKey: string, callControlId: string): Promise<Response> {
  return fetch(`${TELNYX_API}/calls/${callControlId}/actions/transcription_start`, {
    method: "POST",
    headers: authHeaders(apiKey),
    body: JSON.stringify({
      transcription_tracks: "inbound",
      transcription_engine: "Telnyx",
      command_id: `transcribe-start-${Date.now()}`,
    }),
  });
}

async function stopTranscription(apiKey: string, callControlId: string): Promise<Response> {
  return fetch(`${TELNYX_API}/calls/${callControlId}/actions/transcription_stop`, {
    method: "POST",
    headers: authHeaders(apiKey),
    body: JSON.stringify({ command_id: `transcribe-stop-${Date.now()}` }),
  });
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url);

    // ── Health ─────────────────────────────────────────────────────────
    if (url.pathname === "/health/liveness") return new Response("ok");
    if (url.pathname === "/health/readiness") return new Response("ok");

    // ── Voice webhook ──────────────────────────────────────────────────
    if (url.pathname === "/webhooks/voice" && req.method === "POST") {
      return handleVoiceWebhook(req, env);
    }

    // ── Live dashboard ─────────────────────────────────────────────────
    if (req.method === "GET" && (url.pathname === "/" || url.pathname === "/index.html")) {
      return new Response(DASHBOARD_HTML, {
        headers: { "content-type": "text/html;charset=utf-8" },
      });
    }

    // ── GET /transcripts — list recent transcripts across all calls ───
    if (req.method === "GET" && url.pathname === "/transcripts") {
      try {
        const limitStr = url.searchParams.get("limit") ?? "50";
        const limit = Math.max(1, Math.min(200, Number(limitStr) || 50));
        const rows = await env.REGISTRY.idFromName("global").list(limit);
        return Response.json({ transcripts: rows });
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : "failed to list transcripts";
        return Response.json({ error: msg }, { status: 500 });
      }
    }

    // ── GET /transcripts/:call_control_id ─────────────────────────────
    if (req.method === "GET" && url.pathname.startsWith("/transcripts/")) {
      const callControlId = decodeURIComponent(url.pathname.split("/transcripts/")[1]);
      if (!callControlId) {
        return Response.json({ error: "call_control_id is required" }, { status: 400 });
      }
      try {
        const row: TranscriptRecord | null = await env.REGISTRY.idFromName("global").get(callControlId);
        if (!row) {
          return Response.json({ error: "transcript not found" }, { status: 404 });
        }
        return Response.json(row);
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : "failed to fetch transcript";
        return Response.json({ error: msg }, { status: 500 });
      }
    }

    // ── GET /debug/state?call_control_id=... ───────────────────────────
    if (req.method === "GET" && url.pathname === "/debug/state") {
      const callControlId = url.searchParams.get("call_control_id");
      if (!callControlId) {
        return Response.json({ error: "call_control_id query param is required" }, { status: 400 });
      }
      const stub = env.TRANSCRIBE.idFromName(actorName(callControlId));
      try {
        const state = await stub.getDebugState();
        return Response.json(state);
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : "failed to get state";
        return Response.json({ error: msg }, { status: 500 });
      }
    }

    return new Response("not found", { status: 404 });
  },
};

async function handleVoiceWebhook(req: Request, env: Env): Promise<Response> {
  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return Response.json({ error: "invalid json body" }, { status: 400 });
  }

  const event = (body as { data?: Record<string, unknown> })?.data;
  const eventType = event?.event_type as string | undefined;
  const payload = (event?.payload ?? {}) as Record<string, unknown>;
  if (!eventType) {
    return Response.json({ error: "no event_type in payload" }, { status: 400 });
  }

  let apiKey: string;
  try {
    apiKey = getApiKey();
  } catch (e) {
    const message = e instanceof Error ? e.message : "secrets not configured";
    return Response.json({ error: message }, { status: 500 });
  }

  const callControlId = payload.call_control_id as string;
  if (!callControlId) {
    return Response.json({ error: "no call_control_id in payload" }, { status: 400 });
  }
  const stub = env.TRANSCRIBE.idFromName(actorName(callControlId));

  // ── call.initiated ──────────────────────────────────────────────
  if (eventType === "call.initiated") {
    const from = (payload.from as string) || "unknown";
    const to = (payload.to as string) || "unknown";
    await stub.recordStart(callControlId, from, to);
    const answerResp = await answerCall(apiKey, callControlId);
    if (!answerResp.ok) {
      const errBody = await answerResp.text();
      return Response.json(
        { action: "error", step: "answer", status: answerResp.status, err: errBody.slice(0, 200) },
        { status: 502 },
      );
    }
    return Response.json({ action: "answering", callControlId });
  }

  // ── call.answered ──────────────────────────────────────────────
  if (eventType === "call.answered") {
    const speakResp = await speakText(apiKey, callControlId, GREETING);
    if (!speakResp.ok) {
      const errBody = await speakResp.text();
      return Response.json(
        { action: "error", step: "greeting_speak", status: speakResp.status, err: errBody.slice(0, 200) },
        { status: 502 },
      );
    }
    return Response.json({ action: "greeting" });
  }

  // ── call.speak.ended (greeting done → start transcription) ─────
  if (eventType === "call.speak.ended") {
    const speakStage = decodeClientState(payload.client_state).speak_stage;
    if (speakStage !== "greeting") {
      return Response.json({ action: "ignored_speak_ended", speak_stage: speakStage });
    }
    // Defensive: stop any in-flight transcription, wait briefly, then start
    try {
      await stopTranscription(apiKey, callControlId);
      await sleep(300);
    } catch {
      // best-effort
    }
    await stub.setTranscribing();
    const transResp = await startTranscription(apiKey, callControlId);
    if (!transResp.ok) {
      const errBody = await transResp.text();
      return Response.json(
        { action: "error", step: "transcription_start", status: transResp.status, err: errBody.slice(0, 200) },
        { status: 502 },
      );
    }
    return Response.json({ action: "transcribing" });
  }

  // ── call.transcription ─────────────────────────────────────────
  if (eventType === "call.transcription") {
    const transcriptionData = (payload.transcription_data ?? {}) as {
      transcript?: string;
      is_final?: boolean;
    };
    const fragment = String(transcriptionData.transcript || "").trim();
    if (!fragment) {
      return Response.json({ action: "empty_transcription" });
    }
    const isFinal = transcriptionData.is_final !== false;
    await stub.appendTranscript(fragment, isFinal);
    return Response.json({
      action: isFinal ? "transcript_final" : "transcript_interim",
      turn: fragment.slice(0, 120),
    });
  }

  // ── call.hangup ────────────────────────────────────────────────
  if (eventType === "call.hangup") {
    try {
      await stopTranscription(apiKey, callControlId);
    } catch {
      // best-effort
    }
    await stub.onHangup();
    return Response.json({ action: "finalizing" });
  }

  return Response.json({ action: "noop", event: eventType });
}

// ── Minimal live dashboard ──────────────────────────────────────────────
const DASHBOARD_HTML = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Call Transcription Agent — Live</title>
<style>
  :root { --bg:#fafafa; --card:#ffffff; --border:#e5e5e5; --text:#1a1a1a; --muted:#666; --accent:#4a1; }
  * { box-sizing: border-box; }
  body { font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
         max-width:960px; margin:0 auto; padding:32px; color:var(--text); background:var(--bg); }
  h1 { font-size:24px; margin:0 0 4px; }
  .sub { color:var(--muted); font-size:14px; margin-bottom:24px; }
  .card { background:var(--card); border:1px solid var(--border); border-radius:8px; padding:20px; margin-bottom:20px; }
  .card h2 { font-size:16px; margin:0 0 16px; font-weight:600; }
  input { width:100%; padding:10px 12px; border:1px solid var(--border); border-radius:6px;
          font-size:14px; margin-bottom:14px; font-family:inherit; }
  button { background:var(--accent); color:white; border:none; padding:12px 24px;
           border-radius:6px; font-size:14px; font-weight:600; cursor:pointer; }
  button:hover { opacity:0.9; }
  button:disabled { opacity:0.5; cursor:not-allowed; }
  pre { background:#f7f7f7; padding:12px; border-radius:6px; font-size:13px;
        white-space:pre-wrap; word-wrap:break-word; max-height:300px; overflow-y:auto;
        margin:0; font-family:'SF Mono',Monaco,monospace; }
  table { width:100%; border-collapse:collapse; font-size:13px; }
  th,td { text-align:left; padding:8px 10px; border-bottom:1px solid var(--border); }
  th { color:var(--muted); font-weight:600; font-size:12px; text-transform:uppercase; letter-spacing:0.5px; }
  .muted { color:var(--muted); }
  a { color:var(--accent); }
</style>
</head>
<body>
  <h1>Call Transcription Agent</h1>
  <div class="sub">Live STT → durable transcript → LLM summary → SMS on hangup. Edge Compute + Agent SDK.</div>

  <div class="card">
    <h2>1. Inspect a live call</h2>
    <input type="text" id="callId" placeholder="call_control_id (e.g. v3:550e8400-...)">
    <button id="inspectBtn">Inspect state</button>
    <div id="stateOut" style="margin-top:12px;"></div>
  </div>

  <div class="card">
    <h2>2. Recent transcripts</h2>
    <button id="listBtn">Load latest 50</button>
    <div id="listOut" style="margin-top:12px;"></div>
  </div>

<script>
function esc(s){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}

document.getElementById('inspectBtn').addEventListener('click', async () => {
  const id = document.getElementById('callId').value.trim();
  const out = document.getElementById('stateOut');
  if (!id) { out.innerHTML = '<span class="muted">Enter a call_control_id</span>'; return; }
  try {
    const res = await fetch('/debug/state?call_control_id=' + encodeURIComponent(id));
    const data = await res.json();
    out.innerHTML = '<pre>' + esc(JSON.stringify(data, null, 2)) + '</pre>';
  } catch (e) {
    out.innerHTML = '<span class="muted">Error: ' + esc(String(e)) + '</span>';
  }
});

document.getElementById('listBtn').addEventListener('click', async () => {
  const out = document.getElementById('listOut');
  out.innerHTML = '<span class="muted">Loading…</span>';
  try {
    const res = await fetch('/transcripts');
    const data = await res.json();
    if (!data.transcripts || data.transcripts.length === 0) {
      out.innerHTML = '<span class="muted">No transcripts yet.</span>';
      return;
    }
    const rows = data.transcripts.map(t => (
      '<tr><td><a href="/transcripts/' + encodeURIComponent(t.call_control_id) + '">' + esc(t.call_control_id.slice(0,18)) + '…</a></td>' +
      '<td>' + esc(t.from_number) + '</td><td>' + esc(t.to_number) + '</td>' +
      '<td>' + esc((t.summary || '').slice(0,80)) + '</td>' +
      '<td>' + esc(t.status) + '</td><td>' + new Date(t.started_at).toLocaleString() + '</td></tr>'
    )).join('');
    out.innerHTML = '<table><thead><tr><th>ID</th><th>From</th><th>To</th><th>Summary</th><th>Status</th><th>Started</th></tr></thead><tbody>' + rows + '</tbody></table>';
  } catch (e) {
    out.innerHTML = '<span class="muted">Error: ' + esc(String(e)) + '</span>';
  }
});
</script>
</body>
</html>`;
