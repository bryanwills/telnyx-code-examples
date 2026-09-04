// Re-export the actor classes so they ship with the bundle.
export { ConferenceAgent, ConferenceRegistry } from "./conferenceAgent";
import type { ConferenceAgent, ConferenceRegistry, ConferenceRecord, TurnRecord } from "./conferenceAgent";

import {
  type ActorNamespace,
  type ActorStub,
  type IdFromNameOptions,
} from "@telnyx/edge-runtime";

type ConferenceStub = ActorStub &
  Pick<
    ConferenceAgent,
    | "onConferenceStart"
    | "addParticipant"
    | "removeParticipant"
    | "onTranscript"
    | "mediate"
    | "onConferenceEnd"
    | "getSnapshot"
    | "getTurns"
    | "getEvents"
  >;

interface ConferenceNamespace extends ActorNamespace {
  idFromName(name: string, options?: IdFromNameOptions): ConferenceStub;
}

type RegistryStub = ActorStub & Pick<ConferenceRegistry, "record" | "list">;

interface RegistryNamespace extends ActorNamespace {
  idFromName(name: string, options?: IdFromNameOptions): RegistryStub;
}

interface Env {
  CONFERENCE: ConferenceNamespace;
  REGISTRY: RegistryNamespace;
  TELNYX_API_KEY: string;
  AI_MODEL: string;
  SMS_FROM: string;
  SMS_TO: string;
  DEMO_MODE: string;
}

function isDemoMode(env: Env): boolean {
  return (env.DEMO_MODE ?? "true").toLowerCase() !== "false";
}

function conferenceActorName(conferenceId: string): string {
  // Dapr-safe: RFC 1123 — no "+", no special chars
  return conferenceId.replace(/[^0-9a-zA-Z.-]/g, "");
}

// ── Router ───────────────────────────────────────────────────────────────

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url);

    // ── Health ───────────────────────────────────────────────────────
    if (url.pathname === "/health/liveness") return new Response("ok");
    if (url.pathname === "/health/readiness") {
      return Response.json({ status: "ok", demoMode: isDemoMode(env) });
    }

    // ── Voice webhook ────────────────────────────────────────────────
    if (url.pathname === "/webhooks/voice" && req.method === "POST") {
      return handleVoiceWebhook(req, env);
    }

    // ── Demo simulation (safe — no live calls/SMS) ───────────────────
    if (req.method === "POST" && url.pathname === "/demo/conference") {
      return demoStart(req, env);
    }
    if (req.method === "POST" && url.pathname.startsWith("/demo/conference/")) {
      const rest = url.pathname.slice("/demo/conference/".length);
      const [id, action] = rest.split("/");
      if (!id || !action) return Response.json({ error: "expected /demo/conference/{id}/{join|say|end}" }, { status: 400 });
      if (action === "join") return demoJoin(req, env, id);
      if (action === "say") return demoSay(req, env, id);
      if (action === "end") return demoEnd(env, id);
      return Response.json({ error: `unknown demo action '${action}'` }, { status: 404 });
    }

    // ── Conference queries ───────────────────────────────────────────
    if (req.method === "GET" && url.pathname === "/conferences") {
      try {
        const limit = Math.max(1, Math.min(200, Number(url.searchParams.get("limit")) || 50));
        const rows: ConferenceRecord[] = await env.REGISTRY.idFromName("global").list(limit);
        return Response.json({ conferences: rows });
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : "failed to list conferences";
        return Response.json({ error: msg }, { status: 500 });
      }
    }
    if (req.method === "GET" && url.pathname.startsWith("/conferences/")) {
      const parts = url.pathname.split("/conferences/")[1].split("/");
      const id = parts[0];
      if (!id) return Response.json({ error: "conference id required" }, { status: 400 });
      try {
        const stub = env.CONFERENCE.idFromName(conferenceActorName(id));
        if (parts[1] === "transcript") {
          const since = Number(url.searchParams.get("since")) || 0;
          const data = await stub.getTurns(since);
          return Response.json({ conference_id: id, ...data });
        }
        if (parts[1] === "events") {
          const afterSeq = Number(url.searchParams.get("afterSeq")) || 0;
          const events = await stub.getEvents(afterSeq);
          return Response.json({ conference_id: id, events });
        }
        const state = await stub.getSnapshot();
        if (!state.conferenceId) return Response.json({ error: "conference not found" }, { status: 404 });
        // Write-back on read: once the pipeline is finished, publish the final
        // record to the registry actor (fetch env owns cross-actor writes).
        if (state.phase === "done" || state.phase === "error") {
          try {
            await env.REGISTRY.idFromName("global").record(snapshotToRecord(state));
          } catch {
            // best-effort — the snapshot above is the source of truth
          }
        }
        return Response.json(state);
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : "failed to fetch conference";
        return Response.json({ error: msg }, { status: 500 });
      }
    }

    // ── Live dashboard ───────────────────────────────────────────────
    if (req.method === "GET" && (url.pathname === "/" || url.pathname === "/index.html")) {
      return new Response(DASHBOARD_HTML, {
        headers: { "content-type": "text/html;charset=utf-8" },
      });
    }

    return new Response("not found", { status: 404 });
  },
};

// ── Telnyx voice webhook handler ─────────────────────────────────────────

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

  const conferenceId = (payload.conference_id as string) ?? (payload.conferenceId as string);
  const stub = env.CONFERENCE.idFromName(conferenceActorName(conferenceId || "unknown"));

  // ── conference.created / conference.start ──────────────────────
  if (eventType === "conference.created" || eventType === "conference.start") {
    if (!conferenceId) return Response.json({ error: "no conference_id in payload" }, { status: 400 });
    await stub.onConferenceStart(conferenceId, {
      demo: isDemoMode(env),
      friendlyName: (payload.name as string) ?? "",
      model: env.AI_MODEL,
    });
    await trackConferenceStart(env, {
      conference_id: conferenceId,
      friendly_name: (payload.name as string) ?? "",
      participants: 0,
      turn_count: 0,
      summary: "",
      started_at: Date.now(),
      ended_at: 0,
      status: "active",
    });
    return Response.json({ action: "agent_joined", conferenceId });
  }

  // ── conference.participant.joined ─────────────────────────────
  if (eventType === "conference.participant.joined") {
    if (!conferenceId) return Response.json({ error: "no conference_id in payload" }, { status: 400 });
    const name = (payload.call_control_id as string) ?? (payload.connection_id as string) ?? "participant";
    await stub.addParticipant(name, (payload.call_control_id as string) ?? undefined);
    return Response.json({ action: "participant_tracked", conferenceId });
  }

  // ── conference.participant.left ───────────────────────────────
  if (eventType === "conference.participant.left") {
    if (!conferenceId) return Response.json({ error: "no conference_id in payload" }, { status: 400 });
    const name = (payload.call_control_id as string) ?? "participant";
    await stub.removeParticipant(name);
    return Response.json({ action: "participant_removed", conferenceId });
  }

  // ── call.transcription ────────────────────────────────────────
  if (eventType === "call.transcription") {
    if (!conferenceId) return Response.json({ error: "no conference_id in payload" }, { status: 400 });
    const transcriptionData = (payload.transcription_data ?? {}) as {
      transcript?: string;
      is_final?: boolean;
    };
    const fragment = String(transcriptionData.transcript || "").trim();
    if (!fragment) return Response.json({ action: "empty_transcription" });
    const isFinal = transcriptionData.is_final !== false;
    if (!isFinal) return Response.json({ action: "transcript_interim" });
    // Speaker: prefer the call leg id; client_state may carry a friendly name.
    const speaker = decodeClientState(payload.client_state).speaker
      ?? ((payload.call_control_id as string) || "participant");
    await stub.onTranscript(speaker, fragment);
    return Response.json({ action: "transcript_final", turn: fragment.slice(0, 120) });
  }

  // ── conference.ended ──────────────────────────────────────────
  if (eventType === "conference.ended" || eventType === "conference.end") {
    if (!conferenceId) return Response.json({ error: "no conference_id in payload" }, { status: 400 });
    await stub.onConferenceEnd();
    return Response.json({ action: "finalizing", conferenceId });
  }

  return Response.json({ action: "noop", event: eventType });
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

export { encodeClientState };

// ── Demo simulation handlers ─────────────────────────────────────────────
// These drive the exact same agent pipeline as live webhooks, minus real
// Call Control / SMS side effects (agent runs with demo=true).

function newDemoId(): string {
  return `demo-${Date.now().toString(36)}-${Math.floor(Math.random() * 1e6).toString(36)}`;
}

async function demoStart(req: Request, env: Env): Promise<Response> {
  const body = (await safeJson(req)) as { name?: string };
  const conferenceId = newDemoId();
  const stub = env.CONFERENCE.idFromName(conferenceActorName(conferenceId));
  await stub.onConferenceStart(conferenceId, {
    demo: true,
    friendlyName: body?.name ?? "Demo Conference",
    model: env.AI_MODEL,
  });
  await trackConferenceStart(env, {
    conference_id: conferenceId,
    friendly_name: body?.name ?? "Demo Conference",
    participants: 0,
    turn_count: 0,
    summary: "",
    started_at: Date.now(),
    ended_at: 0,
    status: "active",
  });
  return Response.json({ conference_id: conferenceId, demo: true, next: "POST /demo/conference/{id}/join" });
}

/** Best-effort registry write from the fetch env (actors can't reach it). */
async function trackConferenceStart(env: Env, record: ConferenceRecord): Promise<void> {
  try {
    await env.REGISTRY.idFromName("global").record(record);
  } catch {
    // best-effort — /conferences/{id} write-back fills it in later
  }
}

async function demoJoin(req: Request, env: Env, id: string): Promise<Response> {
  const body = (await safeJson(req)) as { name?: string };
  const name = body?.name?.trim();
  if (!name) return Response.json({ error: "name is required" }, { status: 400 });
  await env.CONFERENCE.idFromName(conferenceActorName(id)).addParticipant(name);
  return Response.json({ joined: name, conference_id: id });
}

async function demoSay(req: Request, env: Env, id: string): Promise<Response> {
  const body = (await safeJson(req)) as { speaker?: string; text?: string };
  const speaker = body?.speaker?.trim();
  const text = body?.text?.trim();
  if (!speaker || !text) return Response.json({ error: "speaker and text are required" }, { status: 400 });
  await env.CONFERENCE.idFromName(conferenceActorName(id)).onTranscript(speaker, text);
  return Response.json({ recorded: true, conference_id: id });
}

async function demoEnd(env: Env, id: string): Promise<Response> {
  await env.CONFERENCE.idFromName(conferenceActorName(id)).onConferenceEnd();
  return Response.json({
    ending: true,
    conference_id: id,
    next: "GET /conferences/{id} — summarize → store → notify pipeline runs asynchronously",
  });
}

async function safeJson(req: Request): Promise<Record<string, unknown>> {
  try {
    return (await req.json()) as Record<string, unknown>;
  } catch {
    return {};
  }
}

function snapshotToRecord(state: {
  conferenceId: string;
  friendlyName: string;
  participants: Record<string, number>;
  turns: Array<unknown>;
  summary: string;
  startedAt: number;
  endedAt: number;
  phase: string;
}): ConferenceRecord {
  return {
    conference_id: state.conferenceId,
    friendly_name: state.friendlyName,
    participants: Object.keys(state.participants).length,
    turn_count: state.turns.length,
    summary: state.summary || "",
    started_at: state.startedAt,
    ended_at: state.endedAt || Date.now(),
    status: state.phase === "error" ? "error" : "stored",
  };
}

// ── Minimal live dashboard ───────────────────────────────────────────────

const DASHBOARD_HTML = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Conference Agent Mediator — Live</title>
<style>
  :root { --bg:#fafafa; --card:#fff; --border:#e5e5e5; --text:#1a1a1a; --muted:#666; --accent:#41a; }
  * { box-sizing: border-box; }
  body { font-family: ui-sans-serif, system-ui, sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 24px; }
  h1 { font-size: 20px; margin: 0 0 4px; }
  .sub { color: var(--muted); font-size: 13px; margin-bottom: 20px; }
  .card { background: var(--card); border: 1px solid var(--border); border-radius: 8px; padding: 16px; margin-bottom: 16px; }
  .turn { padding: 6px 0; border-bottom: 1px dashed var(--border); font-size: 14px; }
  .turn:last-child { border-bottom: none; }
  .who { font-weight: 600; color: var(--accent); margin-right: 8px; }
  .mediator .who { color: #a63; }
  .phase { display: inline-block; padding: 2px 10px; border-radius: 999px; background: #eef; font-size: 12px; margin-left: 8px; }
  .summary { white-space: pre-wrap; font-size: 14px; }
  button { font: inherit; padding: 6px 14px; border-radius: 6px; border: 1px solid var(--border); background: #fff; cursor: pointer; margin-right: 8px; }
  button:hover { background: #f2f2f2; }
  input { font: inherit; padding: 6px 10px; border: 1px solid var(--border); border-radius: 6px; margin-right: 8px; width: 160px; }
  #status { color: var(--muted); font-size: 12px; margin-top: 12px; }
</style>
</head>
<body>
<h1>Conference Agent Mediator</h1>
<div class="sub">AI meeting facilitator — transcribes, mediates turn-taking, summarizes. Telnyx Edge Compute.<br>The Mediator prompts participants who have been silent for ~60 seconds.</div>

<div class="card">
  <button onclick="startDemo()">Start demo conference</button>
  <input id="confId" placeholder="conference_id">
  <input id="name" placeholder="participant name">
  <button onclick="join()">Join</button>
  <input id="say" placeholder="What they said…" style="width:280px">
  <button onclick="say()">Say</button>
  <button onclick="endConf()">End conference</button>
  <div id="status"></div>
</div>

<div class="card" id="liveCard" style="display:none">
  <div>Transcript <span class="phase" id="phase"></span></div>
  <div id="turns"></div>
</div>

<div class="card" id="summaryCard" style="display:none">
  <div><b>Post-conference summary</b></div>
  <div class="summary" id="summary"></div>
</div>

<script>
let confId = "", since = 0, timer = null;
function status(s, isErr) {
  const el = document.getElementById("status");
  el.textContent = s;
  el.style.color = isErr ? "#c33" : "";
}
async function api(path, body) {
  const res = await fetch(path, { method: "POST", headers: {"content-type":"application/json"}, body: JSON.stringify(body || {}) });
  if (!res.ok) throw new Error("HTTP " + res.status);
  return res.json();
}
async function startDemo() {
  try {
    const r = await api("/demo/conference", { name: "Demo Conference" });
    confId = r.conference_id; document.getElementById("confId").value = confId;
    document.getElementById("turns").innerHTML = "";
    document.getElementById("liveCard").style.display = "block";
    document.getElementById("summaryCard").style.display = "none";
    since = 0; poll();
    status("Started " + confId + " — add participants, then type what they say. Silent participants get an AI prompt after ~60s.");
  } catch (e) { status("Start failed: " + e.message, true); }
}
async function join() {
  if (!conf()) return;
  const name = document.getElementById("name").value.trim();
  if (!name) { status("Type a participant name first.", true); return; }
  try {
    await api("/demo/conference/" + confId + "/join", { name });
    status(name + " joined — type what they say in the next box, then press Say.");
  } catch (e) { status("Join failed: " + e.message, true); }
}
async function say() {
  if (!conf()) return;
  const name = document.getElementById("name").value.trim() || "participant";
  const text = document.getElementById("say").value.trim();
  if (!text) { status("Type what they said first.", true); return; }
  try {
    await api("/demo/conference/" + confId + "/say", { speaker: name, text });
    document.getElementById("say").value = "";
    status("Recorded [" + name + "] — transcript updates below within ~2s.");
  } catch (e) { status("Say failed: " + e.message, true); }
}
async function endConf() {
  if (!conf()) return;
  try {
    await api("/demo/conference/" + confId + "/end");
    status("Conference ending — summarizing with the LLM, usually ~10–30s…");
    if (!timer) timer = setInterval(poll, 2000);
  } catch (e) { status("End failed: " + e.message, true); }
}
function conf() {
  confId = document.getElementById("confId").value.trim() || confId;
  if (!confId) { status("Start a demo conference or paste a conference_id first.", true); return false; }
  document.getElementById("liveCard").style.display = "block";
  if (!timer) timer = setInterval(poll, 2000);
  return true;
}
async function poll() {
  if (!confId) return;
  try {
    const r = await fetch("/conferences/" + confId + "/transcript?since=" + since).then(r => r.json());
    if (r.turns && r.turns.length) {
      const el = document.getElementById("turns");
      for (const t of r.turns) {
        const d = document.createElement("div");
        d.className = "turn" + (t.speaker === "mediator" ? " mediator" : "");
        const who = document.createElement("span");
        who.className = "who";
        who.textContent = t.speaker === "mediator" ? "Mediator:" : t.speaker + ":";
        d.appendChild(who);
        d.appendChild(document.createTextNode(t.text));
        el.appendChild(d);
      }
      since = r.turns[r.turns.length - 1].at;
    }
    document.getElementById("phase").textContent = r.phase ? "phase: " + r.phase : "";
    if (r.phase === "done" || r.phase === "error") {
      document.getElementById("summary").textContent =
        r.summary || "(no summary generated" + (r.phase === "error" ? " — " + (r.summary || "see /events for the error") : "") + ")";
      document.getElementById("summaryCard").style.display = "block";
      status("Done — summary is below. Start another conference any time.");
      clearInterval(timer); timer = null;
    }
  } catch (e) { /* transient — next tick retries */ }
}
</script>
</body>
</html>`;
