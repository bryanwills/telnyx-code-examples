import { Agent } from "@telnyx/edge-runtime";

export interface SupportState extends Record<string, unknown> {
  from: string;
  to: string;
  lastReply: string;
  at: number;
}

// Minimal hand-typed slice of the [telnyx] binding — `telnyx-edge types` generates full types.
interface SupportEnv {
  TELNYX: {
    messages: {
      send(m: { from: string; to: string; text: string }): Promise<unknown>;
    };
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
}

const SYSTEM_PROMPT =
  "You are a helpful support agent. Answer questions briefly and clearly. If the user seems frustrated, acknowledge their concern and offer to follow up.";

const FOLLOW_UP_SECONDS = 86_400; // 24 hours

/**
 * SupportAgent — one actor instance per phone number (conversation).
 *
 * On inbound SMS:
 *   1. Log the message in durable history (this.messages)
 *   2. Queue a background turn — webhook acks in ms
 *   3. Call the LLM via the Telnyx binding (no API key in code)
 *   4. Reply via the Telnyx binding (no API key in code)
 *   5. Schedule a 24h follow-up ("did that solve your problem?")
 */
export class SupportAgent extends Agent<SupportEnv, SupportState> {
  protected override initialState(): SupportState {
    return { from: "", to: "", lastReply: "", at: 0 };
  }

  async receive({ text, from, to }: { text: string; from: string; to: string }): Promise<void> {
    await this.setState({ from, to });
    await this.messages.add("user", text);
    await this.queue("process");
  }

  async process(): Promise<void> {
    const state = await this.getState();
    const history = await this.messages.toOpenAI();

    let reply = "";
    let debugInfo = "";
    try {
      const completion = await this.env.TELNYX.ai.openai.chat.createCompletion({
        model: "zai-org/GLM-5.2",
        messages: [{ role: "system", content: SYSTEM_PROMPT }, ...history],
        max_tokens: 1000,
        temperature: 0.7,
      });

      // Log the raw response shape for debugging
      debugInfo = JSON.stringify(completion).slice(0, 500);
      reply = completion.choices[0]?.message?.content?.trim() || "";
    } catch (e: any) {
      debugInfo = `error: ${e?.message || String(e)}`;
    }

    if (!reply) {
      reply = "Sorry, I couldn't answer that right now.";
    }

    // Store debug info in state so we can inspect it
    await this.setState({ lastReply: reply, at: Date.now(), debug: debugInfo } as any);

    await this.messages.add("assistant", reply);
    await this.env.TELNYX.messages.send({ from: state.to, to: state.from, text: reply.slice(0, 300) });

    // Schedule the follow-up check-in 24h from now
    await this.schedule(FOLLOW_UP_SECONDS, "followup", null, { id: `followup-${state.from}` });
  }

  async followup(): Promise<void> {
    const state = await this.getState();
    const last = await this.messages.last();
    // If the customer replied after our last answer, skip the nudge.
    if (!last || last.role !== "assistant") return;

    await this.env.TELNYX.messages.send({
      from: state.to,
      to: state.from,
      text: "Did that solve your problem? Reply yes or no, or ask for a human.",
    });
  }

  /** Debug: return current state + message count for inspection. */
  async getDebugState(): Promise<{ state: SupportState; messageCount: number; lastMessage: any }> {
    const state = await this.getState();
    const count = await this.messages.count();
    const last = await this.messages.last();
    return { state, messageCount: count, lastMessage: last };
  }
}
