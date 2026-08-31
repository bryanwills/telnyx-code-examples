import { Agent, StatefulActor, KV, schedule, queue, CloudFS, WebSocketHandler } from '@telnyx/edge-sdk';
import type { HttpRequest, HttpResponse, WebhookContext } from '@telnyx/edge-sdk';

// --- Configuration -----------------------------------------------------------

const TELNYX_API_KEY = process.env.TELNYX_API_KEY ?? '';
const TELNYX_PUBLIC_KEY = process.env.TELNYX_PUBLIC_KEY ?? '';
const TELNYX_NUMBER = process.env.TELNYX_NUMBER ?? '+1555XXXXXXXX';
const SUMMARY_RECIPIENT = process.env.SUMMARY_RECIPIENT ?? '+1555XXXXXXXX';
const DEMO_MODE = (process.env.DEMO_MODE ?? 'true').toLowerCase() === 'true';

// --- Types ------------------------------------------------------------------

interface TurnRecord {
  speaker: string;
  text: string;
  timestamp: number;
}

interface ConferenceState {
  conferenceId: string;
  callControlId: string;
  participants: string[];
  turns: TurnRecord[];
  lastSpokenAt: Record<string, number>;
  startedAt: number;
  endedAt?: number;
  summary?: string;
}

// --- ConferenceAgent --------------------------------------------------------
// StatefulActor that joins a Call Control conference, transcribes speech,
// mediates turn-taking via an LLM, and emits a post-conference summary.

export class ConferenceAgent extends Agent {
  state: ConferenceState;
  observers: Set<WebSocketHandler>;

  constructor(id: string, initialState: ConferenceState) {
    super(id);
    this.state = initialState;
    this.observers = new Set();
  }

  // Stream a live transcript chunk to all connected observers.
  private broadcastTranscript(chunk: TurnRecord): void {
    const payload = JSON.stringify({
      type: 'transcript',
      conferenceId: this.state.conferenceId,
      chunk,
    });
    for (const ws of this.observers) {
      try {
        ws.send(payload);
      } catch {
        this.observers.delete(ws);
      }
    }
  }

  // Called by the STT binding whenever a new utterance is finalized.
  onTranscript(speaker: string, text: string): void {
    const now = Date.now();
    const turn: TurnRecord = { speaker, text, timestamp: now };
    this.state.turns.push(turn);
    this.state.lastSpokenAt[speaker] = now;
    this.broadcastTranscript(turn);

    // Persist state to KV so other actors / cold starts can recover.
    KV.put(`conference:${this.state.conferenceId}`, JSON.stringify(this.state));

    // Enqueue a turn-taking check on the queue primitive.
    queue.enqueue('turn-taking', {
      conferenceId: this.state.conferenceId,
      speaker,
      timestamp: now,
    });
  }

  // Periodic turn-taking mediator. Runs every 30s via this.every().
  mediateTurnTaking(): void {
    const now = Date.now();
    const silenceThresholdMs = 60_000; // 60 seconds
    for (const participant of this.state.participants) {
      const last = this.state.lastSpokenAt[participant] ?? this.state.startedAt;
      if (now - last > silenceThresholdMs) {
        this.promptParticipant(participant);
      }
    }
  }

  // Speak a prompt into the conference via Call Control.
  private promptParticipant(participant: string): void {
    const message = `${participant}, you've been quiet for a while. Would you like to add anything?`;
    if (DEMO_MODE) {
      console.log(`[demo] Would speak via Call Control: "${message}"`);
    } else {
      // In live mode, use the Call Control speak command on the conference.
      // The Telnyx Edge SDK exposes `this.call.speak()` for the bound call leg.
      this.call?.speak({
        payload: message,
        voice: 'female',
        language: 'en-US',
      }).catch((err: unknown) => {
        console.error('Failed to speak prompt:', err);
      });
    }
  }

  // Generate a post-conference summary and send via SMS.
  async summarizeAndNotify(): Promise<void> {
    const transcript = this.state.turns
      .map((t) => `[${new Date(t.timestamp).toISOString()}] ${t.speaker}: ${t.text}`)
      .join('\n');

    const summary = await this.inference.summarize({
      prompt: 'Summarize this conference call and list action items:',
      input: transcript,
    });

    this.state.summary = summary;
    this.state.endedAt = Date.now();
    KV.put(`conference:${this.state.conferenceId}`, JSON.stringify(this.state));

    // Persist the full transcript to CloudFS for archival.
    await CloudFS.put(
      `transcripts/${this.state.conferenceId}.json`,
      JSON.stringify(this.state),
      { contentType: 'application/json' }
    );

    // Send summary via SMS (or log in demo mode).
    if (DEMO_MODE) {
      console.log(`[demo] Would send SMS to ${SUMMARY_RECIPIENT}:\n${summary}`);
    } else {
      await this.sms.send({
        from: TELNYX_NUMBER,
        to: SUMMARY_RECIPIENT,
        text: `Conference summary:\n${summary}`,
      });
    }
  }
}

// --- HTTP Handlers ----------------------------------------------------------

export default {
  async fetch(req: HttpRequest, env: unknown): Promise<HttpResponse> {
    const url = new URL(req.url);

    // Webhook receiver for Telnyx Call Control events.
    if (url.pathname === '/webhooks/telnyx' && req.method === 'POST') {
      return handleTelnyxWebhook(req);
    }

    // WebSocket upgrade for live transcript observers.
    if (url.pathname === '/transcript/stream' && req.headers.get('upgrade') === 'websocket') {
      return handleWebSocketUpgrade(req);
    }

    // Health check.
    if (url.pathname === '/health' && req.method === 'GET') {
      return json({ status: 'ok', demoMode: DEMO_MODE }, 200);
    }

    return json({ error: 'Not found' }, 404);
  },
};

// --- Webhook Handler --------------------------------------------------------

async function handleTelnyxWebhook(req: HttpRequest): Promise<HttpResponse> {
  // Verify the Telnyx Ed25519 signature.
  let verified: unknown;
  try {
    verified = WebhookContext.unwrap(req, TELNYX_PUBLIC_KEY);
  } catch (err) {
    console.error('Webhook signature verification failed:', err);
    return json({ error: 'Invalid signature' }, 401);
  }

  const event = verified as { data?: { payload?: Record<string, unknown> } };
  const payload = event?.data?.payload;
  if (!payload) {
    return json({ error: 'Missing payload' }, 400);
  }

  const eventType = payload.event_type as string | undefined;
  const conferenceId = (payload.conference_id as string) ?? (payload.call_control_id as string);

  switch (eventType) {
    case 'conference.created':
    case 'conference.participant.joined': {
      await onConferenceStart(conferenceId, payload);
      break;
    }
    case 'conference.participant.left':
    case 'conference.ended': {
      await onConferenceEnd(conferenceId);
      break;
    }
    case 'call.transcription': {
      const speaker = (payload.speaker as string) ?? 'unknown';
      const text = (payload.transcript as string) ?? '';
      const agent = await getAgent(conferenceId);
      if (agent) {
        agent.onTranscript(speaker, text);
      }
      break;
    }
    default:
      console.log(`Unhandled event type: ${eventType}`);
  }

  return json({ received: true }, 200);
}

// --- Conference Lifecycle ---------------------------------------------------

async function onConferenceStart(conferenceId: string, payload: Record<string, unknown>): Promise<void> {
  const callControlId = (payload.call_control_id as string) ?? '';
  const participants = (payload.participants as string[]) ?? [];

  const agent = new ConferenceAgent(`agent:${conferenceId}`, {
    conferenceId,
    callControlId,
    participants,
    turns: [],
    lastSpokenAt: {},
    startedAt: Date.now(),
  });

  // Bind the agent to the Call Control leg so it can speak/listen.
  await agent.bind(callControlId);

  // Schedule turn-taking mediation every 30 seconds.
  agent.every(30, () => agent.mediateTurnTaking());

  // Store the agent in KV for retrieval across webhook events.
  await KV.put(`agent:${conferenceId}`, agent.id);

  console.log(`ConferenceAgent joined conference ${conferenceId}`);
}

async function onConferenceEnd(conferenceId: string): Promise<void> {
  const agent = await getAgent(conferenceId);
  if (agent) {
    await agent.summarizeAndNotify();
    console.log(`Conference ${conferenceId} ended; summary sent.`);
  }
}

async function getAgent(conferenceId: string): Promise<ConferenceAgent | null> {
  const agentId = await KV.get(`agent:${conferenceId}`);
  if (!agentId) return null;
  return StatefulActor.get<ConferenceAgent>(agentId);
}

// --- WebSocket Transcript Stream -------------------------------------------

function handleWebSocketUpgrade(req: HttpRequest): HttpResponse {
  const ws = WebSocketHandler.accept(req);
  const conferenceId = new URL(req.url).searchParams.get('conferenceId');

  if (!conferenceId) {
    ws.close(1008, 'Missing conferenceId');
    return json({ error: 'Missing conferenceId' }, 400) as unknown as HttpResponse;
  }

  // Attach this observer to the agent so it receives live transcript chunks.
  getAgent(conferenceId).then((agent) => {
    if (agent) {
      agent.observers.add(ws);
      ws.send(JSON.stringify({ type: 'connected', conferenceId }));
    } else {
      ws.send(JSON.stringify({ type: 'error', message: 'Conference not found' }));
      ws.close(1011, 'Conference not found');
    }
  });

  ws.on('close', () => {
    getAgent(conferenceId).then((agent) => {
      if (agent) agent.observers.delete(ws);
    });
  });

  return new Response(null, { status: 101 }) as unknown as HttpResponse;
}

// --- Utilities --------------------------------------------------------------

function json(body: unknown, status: number): HttpResponse {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'content-type': 'application/json' },
  }) as unknown as HttpResponse;
}

// --- Smoke Test Entry (for `smoke_test.ts`) ---------------------------------
// Exported so the smoke test can import and verify the module loads.
export const __smoke = { ConferenceAgent, json };
