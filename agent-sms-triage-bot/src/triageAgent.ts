import { Agent } from "@telnyx/edge-runtime";

export type Topic = "billing" | "support" | "sales" | "general";

export interface TriageEntry {
  at: number;
  from: string;
  text: string;
  topic: Topic;
  route: string;
  confidence: number;
}

export interface TriageState extends Record<string, unknown> {
  phoneNumber: string;
  fromNumber: string;
  routeTable: Record<string, string>;
  triageHistory: TriageEntry[];
  totalMessages: number;
  topicCounts: Record<string, number>;
}

interface TriageEnv {
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
  AI_MODEL?: string;
}

const DEFAULT_MODEL = "moonshotai/Kimi-K2.6";

const CLASSIFY_SYSTEM_PROMPT = `You are an SMS triage classifier. Analyze the customer's message and classify it into one of these topics:
- billing: questions about invoices, payments, charges, refunds, account balance, subscription costs
- support: technical issues, bugs, how-to questions, product help, troubleshooting
- sales: questions about pricing, plans, demos, upgrades, new accounts, purchasing
- general: anything that doesn't fit the above categories

Return JSON only: {"topic": "billing"|"support"|"sales"|"general", "confidence": 0.0-1.0, "reason": "one short sentence"}

Do NOT include any text outside the JSON.`;

const DEFAULT_ROUTE_TABLE: Record<string, string> = {
  billing: "billing-queue",
  support: "support-queue",
  sales: "sales-queue",
  general: "general-queue",
};

const REPLY_TEMPLATES: Record<Topic, string> = {
  billing: "Thanks for reaching out! I've routed your message to our Billing team. They'll get back to you within 24 hours. Reference: {route}",
  support: "Thanks for reaching out! I've routed your message to our Support team. They'll get back to you within 4 hours. Reference: {route}",
  sales: "Thanks for reaching out! I've routed your message to our Sales team. They'll get back to you within 2 hours. Reference: {route}",
  general: "Thanks for reaching out! I've routed your message to our team. They'll get back to you within 24 hours. Reference: {route}",
};

/**
 * TriageAgent — one actor instance per inbound phone number.
 *
 * Lifecycle:
 *   1. setRoute(topic, queue) — update the KV route table
 *   2. triage(from, text) — LLM classifies the topic, looks up the route,
 *      sends a reply SMS via this.env.TELNYX.messages.send(), logs the entry
 *   3. getHistory() — return triage history for inspection
 */
export class TriageAgent extends Agent<TriageEnv, TriageState> {
  protected override initialState(): TriageState {
    return {
      phoneNumber: "",
      fromNumber: "",
      routeTable: { ...DEFAULT_ROUTE_TABLE },
      triageHistory: [],
      totalMessages: 0,
      topicCounts: { billing: 0, support: 0, sales: 0, general: 0 },
    };
  }

  /**
   * Set or update a route in the route table.
   */
  async setRoute(topic: string, queue: string): Promise<void> {
    const state = await this.getState();
    const routeTable = { ...state.routeTable, [topic]: queue };
    await this.setState({ ...state, routeTable });
  }

  /**
   * Get the current route table.
   */
  async getRoutes(): Promise<Record<string, string>> {
    const state = await this.getState();
    return state.routeTable;
  }

  /**
   * Triage an inbound SMS: classify via LLM, look up route, reply via SMS.
   */
  async triage(from: string, text: string): Promise<{ topic: Topic; route: string; confidence: number }> {
    const state = await this.getState();

    // Classify via LLM
    let topic: Topic = "general";
    let confidence = 0;
    let reason = "";

    try {
      const completion = await this.env.TELNYX.ai.openai.chat.createCompletion({
        model: this.env.AI_MODEL || DEFAULT_MODEL,
        messages: [
          { role: "system", content: CLASSIFY_SYSTEM_PROMPT },
          { role: "user", content: `Customer message: "${text}"` },
        ],
        max_tokens: 2000,
        temperature: 0.2,
      });

      const content = completion.choices[0]?.message?.content?.trim() || "";
      if (!content) throw new Error("empty content from model");
      const cleaned = content.startsWith("```")
        ? content.split("\n").slice(1).join("\n").replace(/```/g, "").trim()
        : content;
      const parsed = JSON.parse(cleaned);
      topic = (["billing", "support", "sales", "general"].includes(parsed.topic) ? parsed.topic : "general") as Topic;
      confidence = typeof parsed.confidence === "number" ? parsed.confidence : 0;
      reason = parsed.reason || "";
    } catch {
      // Default to general if LLM fails
      topic = "general";
      confidence = 0;
      reason = "LLM classification failed";
    }

    // Look up route in the route table
    const route = state.routeTable[topic] || state.routeTable["general"] || "general-queue";

    // Send reply SMS via zero-credential binding
    const replyText = REPLY_TEMPLATES[topic].replace("{route}", route);
    try {
      await this.env.TELNYX.messages.send({
        from: state.fromNumber || state.phoneNumber,
        to: from,
        text: replyText,
      });
    } catch {
      // best-effort — still log the triage entry
    }

    // Log the triage entry
    const entry: TriageEntry = {
      at: Date.now(),
      from,
      text,
      topic,
      route,
      confidence,
    };

    const topicCounts = { ...state.topicCounts };
    topicCounts[topic] = (topicCounts[topic] || 0) + 1;

    await this.setState({
      ...state,
      triageHistory: [...state.triageHistory, entry].slice(-100),
      totalMessages: state.totalMessages + 1,
      topicCounts,
    });

    return { topic, route, confidence };
  }

  /**
   * Get triage history.
   */
  async getHistory(limit = 20): Promise<{ entries: TriageEntry[]; total: number; topicCounts: Record<string, number> }> {
    const state = await this.getState();
    return {
      entries: state.triageHistory.slice(-limit),
      total: state.totalMessages,
      topicCounts: state.topicCounts,
    };
  }

  /**
   * Get debug state for inspection.
   */
  async getDebugState(): Promise<TriageState> {
    return await this.getState();
  }
}
