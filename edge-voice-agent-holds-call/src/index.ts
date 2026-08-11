export { VoiceAgent } from "./voiceAgent";
import type { VoiceAgent, CallPhase } from "./voiceAgent";

import {
  type ActorNamespace,
  type ActorStub,
  type IdFromNameOptions,
} from "@telnyx/edge-runtime";

type VoiceAgentStub = ActorStub &
  Pick<
    VoiceAgent,
    | "recordStart"
    | "setPhase"
    | "appendUser"
    | "respond"
    | "finishCall"
    | "getDebugState"
  >;

interface VoiceAgentNamespace extends ActorNamespace {
  idFromName(name: string, options?: IdFromNameOptions): VoiceAgentStub;
}

interface Env {
  VOICE_AGENT: VoiceAgentNamespace;
  AI_MODEL: string;
}

const TELNYX_API = "https://api.telnyx.com/v2";
const GREETING = "Hi, this is an AI voice agent. What can I help you with today?";
const TTS_VOICE = "Telnyx.KokoroTTS.af";

type SpeakStage = "greeting" | "reply";

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

async function speakText(
  apiKey: string,
  callControlId: string,
  text: string,
  stage: SpeakStage,
): Promise<Response> {
  return fetch(`${TELNYX_API}/calls/${callControlId}/actions/speak`, {
    method: "POST",
    headers: authHeaders(apiKey),
    body: JSON.stringify({
      payload: text,
      voice: TTS_VOICE,
      language: "en-US",
      client_state: encodeClientState({ speak_stage: stage }),
      command_id: `voice-agent-${stage}`,
    }),
  });
}

async function startTranscription(apiKey: string, callControlId: string): Promise<Response> {
  return fetch(`${TELNYX_API}/calls/${callControlId}/actions/transcription_start`, {
    method: "POST",
    headers: authHeaders(apiKey),
    body: JSON.stringify({
      transcription_tracks: "inbound",
      transcription_engine: "Google",
      transcription_engine_config: {
        transcription_engine: "Google",
        language: "en",
      },
      command_id: "voice-agent-transcription-start",
    }),
  });
}

async function stopTranscription(apiKey: string, callControlId: string): Promise<Response> {
  return fetch(`${TELNYX_API}/calls/${callControlId}/actions/transcription_stop`, {
    method: "POST",
    headers: authHeaders(apiKey),
    body: JSON.stringify({ command_id: "voice-agent-transcription-stop" }),
  });
}

async function hangupCall(apiKey: string, callControlId: string): Promise<Response> {
  return fetch(`${TELNYX_API}/calls/${callControlId}/actions/hangup`, {
    method: "POST",
    headers: authHeaders(apiKey),
  });
}

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url);

    if (url.pathname === "/health/liveness") return new Response("ok");
    if (url.pathname === "/health/readiness") return new Response("ok");

    if (url.pathname === "/webhooks/voice" && req.method === "POST") {
      return handleVoiceWebhook(req, env);
    }

    if (url.pathname === "/debug/call" && req.method === "GET") {
      const callControlId = url.searchParams.get("call_control_id");
      if (!callControlId) {
        return Response.json({ error: "call_control_id query param is required" }, { status: 400 });
      }
      const stub = env.VOICE_AGENT.idFromName(actorName(callControlId));
      try {
        const result = await stub.getDebugState();
        return Response.json(result);
      } catch (e: unknown) {
        const message = e instanceof Error ? e.message : "failed to get state";
        return Response.json({ error: message }, { status: 500 });
      }
    }

    if (url.pathname === "/debug/respond" && req.method === "POST") {
      const body = (await req.json().catch(() => ({}))) as { call_control_id?: string };
      const callControlId = body.call_control_id;
      if (!callControlId) {
        return Response.json({ error: "call_control_id field is required" }, { status: 400 });
      }
      const stub = env.VOICE_AGENT.idFromName(actorName(callControlId));
      try {
        const reply = await stub.respond();
        return Response.json({ reply });
      } catch (e: unknown) {
        const message = e instanceof Error ? e.message : "respond failed";
        return Response.json({ error: message }, { status: 500 });
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
  const stub = env.VOICE_AGENT.idFromName(actorName(callControlId));

  if (eventType === "call.initiated") {
    const from = (payload.from as string) || "unknown";
    const to = (payload.to as string) || "unknown";

    await stub.recordStart(callControlId, from, to);
    const answerResp = await answerCall(apiKey, callControlId);
    if (!answerResp.ok) {
      const errBody = await answerResp.text();
      return Response.json({
        action: "error",
        step: "answer",
        status: answerResp.status,
        err: errBody.slice(0, 200),
      });
    }
    return Response.json({ action: "answering", callControlId });
  }

  if (eventType === "call.answered") {
    await stub.setPhase("greeting");
    const speakResp = await speakText(apiKey, callControlId, GREETING, "greeting");
    if (!speakResp.ok) {
      const errBody = await speakResp.text();
      return Response.json({
        action: "error",
        step: "greeting_speak",
        status: speakResp.status,
        err: errBody.slice(0, 200),
      });
    }
    return Response.json({ action: "greeting" });
  }

  if (eventType === "call.speak.ended") {
    const speakStage = decodeClientState(payload.client_state).speak_stage as
      | SpeakStage
      | undefined;

    if (speakStage === "greeting" || speakStage === "reply") {
      await stub.setPhase("listening");
      const transResp = await startTranscription(apiKey, callControlId);
      if (!transResp.ok) {
        const errBody = await transResp.text();
        return Response.json({
          action: "error",
          step: "transcription_start",
          status: transResp.status,
          err: errBody.slice(0, 200),
        });
      }
      return Response.json({ action: "listening", speak_stage: speakStage });
    }

    return Response.json({ action: "ignored_speak_ended", speak_stage: speakStage });
  }

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
    if (!isFinal || fragment.length < 5) {
      return Response.json({ action: "transcription_accumulated", transcript: fragment });
    }

    await stub.setPhase("thinking");
    await stub.appendUser(fragment);

    try {
      await stopTranscription(apiKey, callControlId);
    } catch {
      // best-effort — proceed to LLM turn anyway
    }

    let reply: string;
    try {
      reply = await stub.respond();
    } catch (e) {
      reply = "Sorry, I couldn't process that. Could you say it again?";
    }

    await stub.setPhase("replying");
    const speakResp = await speakText(apiKey, callControlId, reply, "reply");
    if (!speakResp.ok) {
      const errBody = await speakResp.text();
      return Response.json({
        action: "error",
        step: "reply_speak",
        status: speakResp.status,
        err: errBody.slice(0, 200),
      });
    }

    return Response.json({ action: "replying", turn: fragment.slice(0, 120) });
  }

  if (eventType === "call.hangup") {
    await stub.finishCall();
    return Response.json({ action: "hungup" });
  }

  return Response.json({ action: "noop", event: eventType });
}
