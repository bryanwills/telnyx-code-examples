import { Agent } from "@telnyx/edge-runtime";

export type CallPhase =
  | "init"
  | "answering"
  | "greeting"
  | "listening"
  | "thinking"
  | "replying"
  | "done";

export interface CallState extends Record<string, unknown> {
  callControlId: string;
  from: string;
  to: string;
  phase: CallPhase;
  turnCount: number;
  startedAt: number;
  endedAt?: number;
  lastTranscript?: string;
  lastReply?: string;
  listeningSince?: number;
  recentReplies: string[];
}

interface VoiceEnv {
  TELNYX: {
    ai: {
      openai: {
        chat: {
          createCompletion(req: {
            model: string;
            messages: Array<{ role: string; content: string }>;
            max_tokens?: number;
            temperature?: number;
          }): Promise<{ choices: Array<{ message: { content: string } }> }>;
        };
      };
    };
  };
  AI_MODEL?: string;
}

const DEFAULT_MODEL = "zai-org/GLM-5.2";

const SYSTEM_PROMPT =
  "You are a helpful phone assistant on a live call. Keep answers short and conversational — 2-3 sentences max. Ask follow-up questions when appropriate. If you don't know something, say so. Be friendly and natural. Do NOT repeat what the caller said back to them.";

/**
 * VoiceAgent — one actor instance per inbound call (keyed by call_control_id).
 *
 * Lifecycle:
 *   1. recordStart() — capture callId, from, to, phase
 *   2. setPhase() — advance through greeting → listening → thinking → replying → done
 *   3. appendUser(transcript) — add caller speech to durable message history
 *   4. respond() — run LLM turn via this.env.TELNYX.ai.openai.chat.createCompletion()
 *      (zero-credential), add reply to history, return reply text for TTS
 *   5. finishCall() — mark endedAt, phase = done
 *
 * Conversation history lives in this.messages (durable). Call state lives in
 * this.getState()/setState() (durable). Both survive restarts in the same PoP.
 */
export class VoiceAgent extends Agent<VoiceEnv, CallState> {
  protected override initialState(): CallState {
    return {
      callControlId: "",
      from: "",
      to: "",
      phase: "init",
      turnCount: 0,
      startedAt: Date.now(),
      recentReplies: [],
    };
  }

  async recordStart(callControlId: string, from: string, to: string): Promise<void> {
    await this.setState({
      callControlId,
      from,
      to,
      phase: "answering",
      startedAt: Date.now(),
      recentReplies: [],
    });
  }

  async setPhase(phase: CallPhase): Promise<void> {
    const state = await this.getState();
    const patch: Partial<CallState> = { phase };
    if (phase === "listening") {
      patch.listeningSince = Date.now();
    }
    await this.setState({ ...state, ...patch });
  }

  async appendUser(text: string): Promise<void> {
    await this.messages.add("user", text);
    const state = await this.getState();
    await this.setState({ lastTranscript: text, turnCount: state.turnCount + 1 });
  }

  async appendAssistant(text: string): Promise<void> {
    await this.messages.add("assistant", text);
    const state = await this.getState();
    const recentReplies = [...(state.recentReplies ?? []), text].slice(-5);
    await this.setState({ lastReply: text, recentReplies });
  }

  /**
   * Check if a transcript is likely the agent hearing its own TTS output.
   * Compares against recent replies using token overlap.
   */
  isOwnSpeech(transcript: string): boolean {
    const norm = transcript.toLowerCase().replace(/[^a-z0-9\s]/g, "").trim();
    if (!norm || norm.length < 3) return false;
    const transWords = new Set(norm.split(/\s+/));
    const state = this.getStateSync();
    for (const reply of state.recentReplies ?? []) {
      const replyNorm = reply.toLowerCase().replace(/[^a-z0-9\s]/g, "").trim();
      const replyWords = new Set(replyNorm.split(/\s+/));
      if (replyWords.size === 0) continue;
      let overlap = 0;
      for (const w of transWords) {
        if (replyWords.has(w) && w.length > 3) overlap++;
      }
      const overlapRatio = overlap / Math.min(transWords.size, replyWords.size);
      if (overlapRatio > 0.5) return true;
    }
    return false;
  }

  private getStateSync(): CallState {
    return (this as unknown as { __state?: CallState }).__state ?? {
      callControlId: "",
      from: "",
      to: "",
      phase: "init",
      turnCount: 0,
      startedAt: 0,
      recentReplies: [],
    };
  }

  /**
   * Run one LLM turn using the zero-credential Telnyx binding.
   * Reads conversation history via this.messages.toOpenAI(), calls
   * this.env.TELNYX.ai.openai.chat.createCompletion(), stores the reply,
   * and returns it for the webhook handler to speak via Call Control.
   */
  async respond(): Promise<string> {
    const history = await this.messages.toOpenAI();
    const model = this.env.AI_MODEL || DEFAULT_MODEL;

    let reply = "";
    try {
      // Race the LLM call against a 10s timeout — if it takes longer, fall back
      const completionPromise = this.env.TELNYX.ai.openai.chat.createCompletion({
        model,
        messages: [{ role: "system", content: SYSTEM_PROMPT }, ...history],
        max_tokens: 200,
        temperature: 0.5,
      });
      const timeoutPromise = new Promise<never>((_, reject) =>
        setTimeout(() => reject(new Error("LLM timeout after 10s")), 10_000)
      );
      const completion = await Promise.race([completionPromise, timeoutPromise]);
      reply = completion.choices[0]?.message?.content?.trim() || "";
    } catch {
      reply = "Sorry, I didn't catch that. Could you repeat it?";
    }

    if (!reply) reply = "Could you repeat that?";

    await this.appendAssistant(reply);
    return reply;
  }

  async finishCall(): Promise<void> {
    await this.setState({ phase: "done", endedAt: Date.now() });
  }

  async recordEvent(event: {
    eventType: string;
    at: number;
    payloadSummary: string;
    action?: string;
    error?: string;
  }): Promise<void> {
    const state = await this.getState();
    const events = (state as CallState & { events?: unknown[] }).events ?? [];
    events.push(event);
    const trimmed = events.slice(-50);
    await this.setState({ ...state, events: trimmed } as CallState & { events?: unknown[] });
  }

  async getDebugState(): Promise<{
    state: CallState;
    messageCount: number;
    lastMessage: unknown;
  }> {
    const state = await this.getState();
    const messageCount = await this.messages.count();
    const lastMessage = await this.messages.last();
    return { state, messageCount, lastMessage };
  }
}
