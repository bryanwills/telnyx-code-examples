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
  "You are a helpful phone assistant on a live call. Keep answers short and conversational — 2-3 sentences max. Ask follow-up questions when appropriate. If you don't know something, say so. Be friendly and natural.";

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
    };
  }

  async recordStart(callControlId: string, from: string, to: string): Promise<void> {
    await this.setState({
      callControlId,
      from,
      to,
      phase: "answering",
      startedAt: Date.now(),
    });
  }

  async setPhase(phase: CallPhase): Promise<void> {
    await this.setState({ phase });
  }

  async appendUser(text: string): Promise<void> {
    await this.messages.add("user", text);
    const state = await this.getState();
    await this.setState({ lastTranscript: text, turnCount: state.turnCount + 1 });
  }

  async appendAssistant(text: string): Promise<void> {
    await this.messages.add("assistant", text);
    await this.setState({ lastReply: text });
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
      const completion = await this.env.TELNYX.ai.openai.chat.createCompletion({
        model,
        messages: [{ role: "system", content: SYSTEM_PROMPT }, ...history],
        max_tokens: 500,
        temperature: 0.7,
      });
      reply = completion.choices[0]?.message?.content?.trim() || "";
    } catch {
      reply = "Sorry, I had trouble with that. Could you say it again?";
    }

    if (!reply) reply = "Could you repeat that?";

    await this.appendAssistant(reply);
    return reply;
  }

  async finishCall(): Promise<void> {
    await this.setState({ phase: "done", endedAt: Date.now() });
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
