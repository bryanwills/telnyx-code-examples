import {
  Agent,
  type ActorContext,
  type ActorNamespace,
  type Env,
  type KvNamespace,
  type Secrets,
  type SqlDatabase,
} from "@telnyx/edge-runtime";
import { verifyTelnyxSignature } from "./verify";

// ---------------------------------------------------------------------------
// Environment interface — bindings declared in telnyx.toml
// ---------------------------------------------------------------------------
export interface SponsorEnv extends Env {
  SECRETS: Secrets;
  SPONSOR_AGENT: ActorNamespace<SponsorAgent>;
  LEADS_DB: SqlDatabase;
  RATE_LIMIT_KV: KvNamespace;
  TELNYX: {
    messages: {
      send: (params: { to: string; from: string; text: string }) => Promise<any>;
    };
    ai: {
      openai: {
        chat: {
          createCompletion: (params: {
            model: string;
            messages: Array<{ role: string; content: string }>;
          }) => Promise<{ choices: Array<{ message: { content: string } }> }>;
        };
      };
    };
    calls: {
      create: (params: Record<string, any>) => Promise<any>;
    };
    v2: {
      messages: {
        create: (params: Record<string, any>) => Promise<any>;
      };
    };
  };
  AI_MODEL: string;
  DEMO_MODE: string;
  SALES_TEAM_NUMBER: string;
  FROM_NUMBER: string;
  EVENT_NAME: string;
  GIVEAWAY_PRIZE: string;
}

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
export interface LeadRecord {
  id?: string;
  phone: string;
  name?: string;
  email?: string;
  company?: string;
  useCase?: string;
  companySize?: string;
  timeline?: string;
  channel: "sms" | "whatsapp" | "email" | "chat" | "voice";
  qualified: boolean;
  giveawayEntry: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface SessionState extends Record<string, unknown> {
  phone: string;
  name?: string;
  channel: "sms" | "whatsapp" | "chat" | "voice";
  step: string;
  language: string;
  collected: Record<string, string>;
  giveawayEntry: boolean;
  demoRequested: boolean;
  lastInteraction: string;
}

export interface RateLimitResult {
  allowed: boolean;
  remaining: number;
  resetAt: number;
}

// ---------------------------------------------------------------------------
// Rate limiter helper
// ---------------------------------------------------------------------------
export class SimpleRateLimiter {
  constructor(private kv: KvNamespace, private windowSeconds: number, private maxRequests: number) {}

  async check(identifier: string): Promise<RateLimitResult> {
    const now = Math.floor(Date.now() / 1000);
    const window = Math.floor(now / this.windowSeconds);
    const key = `rl:${identifier}:${window}`;

    const current = (await this.kv.get(key, { type: "json" }).catch(() => 0)) as number | string | null;
    const count = Number(current ?? 0);

    if (count >= this.maxRequests) {
      return { allowed: false, remaining: 0, resetAt: (window + 1) * this.windowSeconds };
    }

    await this.kv.put(key, String(count + 1), {
      expirationTtl: this.windowSeconds,
    });

    return {
      allowed: true,
      remaining: this.maxRequests - count - 1,
      resetAt: (window + 1) * this.windowSeconds,
    };
  }
}

// ---------------------------------------------------------------------------
// SponsorAgent — the main agent handling all attendee interactions.
// One durable actor per attendee, addressed by phone number (or session id
// for in-browser chat) via `idFromName`.
// ---------------------------------------------------------------------------
export class SponsorAgent extends Agent<SponsorEnv, SessionState> {
  constructor(ctx: ActorContext, env: SponsorEnv) {
    super(ctx, env);
  }

  protected initialState(): SessionState {
    return {
      phone: "",
      channel: "sms",
      step: "welcome",
      language: "en",
      collected: {},
      giveawayEntry: false,
      demoRequested: false,
      lastInteraction: new Date().toISOString(),
    };
  }

  // -----------------------------------------------------------------------
  // Public RPC-callable methods (invoked via stub from the fetch handler)
  // -----------------------------------------------------------------------

  /**
   * Handle an inbound SMS or WhatsApp message from an attendee.
   */
  async handleInboundMessage(params: {
    from: string;
    to: string;
    text: string;
    channel: "sms" | "whatsapp";
  }): Promise<{ success: boolean; message: string }> {
    const { from, text, channel } = params;

    // Rate limit
    const limiter = new SimpleRateLimiter(this.env.RATE_LIMIT_KV, 60, 10);
    const rl = await limiter.check(from);
    if (!rl.allowed) {
      return { success: false, message: "Rate limit exceeded. Please try again later." };
    }

    // Load or create session
    let state = await this.getState();
    if (!state.phone) {
      state = { ...state, phone: from, channel, lastInteraction: new Date().toISOString() };
    }

    // Detect language via inference
    const lang = await this.detectLanguage(text);
    state.language = lang;

    // Process the message through the agent flow
    const response = await this.processMessage(text, state, channel);

    // Persist session
    await this.setState({ ...state, lastInteraction: new Date().toISOString() });

    // Send response
    await this.sendResponse(from, response, channel);

    return { success: true, message: response };
  }

  /**
   * Handle an inbound voice call.
   */
  async handleInboundCall(params: {
    callId: string;
    from: string;
    to: string;
  }): Promise<{ success: boolean; message: string }> {
    const { from, callId } = params;

    const limiter = new SimpleRateLimiter(this.env.RATE_LIMIT_KV, 60, 5);
    const rl = await limiter.check(from);
    if (!rl.allowed) {
      return { success: false, message: "Rate limit exceeded." };
    }

    const state = await this.getState();
    const updated = { ...state, phone: from, channel: "voice" as const, lastInteraction: new Date().toISOString() };
    await this.setState(updated);

    // In demo mode, just log; in live mode, use Call Control
    if (this.env.DEMO_MODE === "true") {
      console.log(`[DEMO] Voice call from ${from}, callId=${callId}. Would connect to agent.`);
    } else {
      // Real Call Control would use telnyx.calls.create or Call Control API
      console.log(`[LIVE] Initiating Call Control for ${from}, callId=${callId}`);
    }

    return { success: true, message: "Call received and queued for agent." };
  }

  /**
   * Handle in-browser chat message.
   */
  async handleChatMessage(params: {
    sessionId: string;
    text: string;
  }): Promise<{ success: boolean; message: string; data?: any }> {
    const { sessionId, text } = params;

    const limiter = new SimpleRateLimiter(this.env.RATE_LIMIT_KV, 60, 20);
    const rl = await limiter.check(sessionId);
    if (!rl.allowed) {
      return { success: false, message: "Rate limit exceeded." };
    }

    const state = await this.getState();
    const updated = { ...state, channel: "chat" as const, lastInteraction: new Date().toISOString() };
    await this.setState(updated);

    const response = await this.processMessage(text, updated, "chat");

    return { success: true, message: response };
  }

  /**
   * Handle post-event follow-up scheduling.
   */
  async scheduleFollowUp(params: {
    phone: string;
    channel: "sms" | "whatsapp" | "email" | "voice";
    delaySeconds: number;
  }): Promise<{ success: boolean; scheduledId?: string }> {
    const { phone, channel, delaySeconds } = params;

    const scheduledId = await this.schedule(delaySeconds, "sendFollowUp", { phone, channel });

    return { success: true, scheduledId };
  }

  /**
   * Task handler: send follow-up message after event.
   * Invoked by the Agent task scheduler — do NOT override `alarm()`, which
   * would break the scheduler.
   */
  async sendFollowUp(payload: { phone: string; channel: "sms" | "whatsapp" | "email" | "voice" }): Promise<void> {
    const { phone, channel } = payload;

    const lead = await this.getLeadByPhone(phone);
    if (!lead) return;

    const followUpText = await this.generateFollowUpMessage(lead);

    if (channel === "sms" || channel === "whatsapp") {
      await this.sendResponse(phone, followUpText, channel);
    } else if (channel === "email") {
      if (this.env.DEMO_MODE === "true") {
        console.log(`[DEMO] Would send email to ${lead.email}: ${followUpText}`);
      } else {
        // In live mode, use Telnyx Email API via raw fetch or TELNYX binding
        console.log(`[LIVE] Sending email to ${lead.email}`);
      }
    } else if (channel === "voice") {
      if (this.env.DEMO_MODE === "true") {
        console.log(`[DEMO] Would place voice call to ${phone}: ${followUpText}`);
      } else {
        console.log(`[LIVE] Placing voice call to ${phone}`);
      }
    }
  }

  /**
   * Generate an attribution report for captured, qualified, and converted leads.
   */
  async generateAttributionReport(): Promise<{
    totalCaptured: number;
    totalQualified: number;
    totalConverted: number;
    byChannel: Record<string, number>;
    byUseCase: Record<string, number>;
  }> {
    await this.env.LEADS_DB.exec(`
      CREATE TABLE IF NOT EXISTS leads (
        phone TEXT PRIMARY KEY,
        name TEXT,
        email TEXT,
        company TEXT,
        useCase TEXT,
        companySize TEXT,
        timeline TEXT,
        channel TEXT,
        qualified BOOLEAN,
        giveawayEntry BOOLEAN,
        createdAt TEXT,
        updatedAt TEXT
      )
    `);

    const result = await this.env.LEADS_DB.prepare(
      "SELECT channel, useCase, qualified, giveawayEntry FROM leads"
    ).all<{ channel: string; useCase: string; qualified: boolean; giveawayEntry: boolean }>();

    const leads = result.results || [];
    const report = {
      totalCaptured: leads.length,
      totalQualified: leads.filter((l: any) => l.qualified).length,
      totalConverted: leads.filter((l: any) => l.giveawayEntry).length,
      byChannel: {} as Record<string, number>,
      byUseCase: {} as Record<string, number>,
    };

    for (const lead of leads) {
      report.byChannel[lead.channel] = (report.byChannel[lead.channel] || 0) + 1;
      if (lead.useCase) {
        report.byUseCase[lead.useCase] = (report.byUseCase[lead.useCase] || 0) + 1;
      }
    }

    return report;
  }

  // -----------------------------------------------------------------------
  // Private helpers
  // -----------------------------------------------------------------------

  private async detectLanguage(text: string): Promise<string> {
    try {
      const response = await this.env.TELNYX.ai.openai.chat.createCompletion({
        model: this.env.AI_MODEL || "gpt-4o-mini",
        messages: [
          {
            role: "system",
            content: "Detect the language of the following text. Respond with only the ISO 639-1 language code (e.g., 'en', 'es', 'fr', 'de', 'ja', 'zh').",
          },
          { role: "user", content: text },
        ],
      });

      return response.choices[0]?.message?.content?.trim() || "en";
    } catch (err) {
      console.error("Language detection failed:", err);
      return "en";
    }
  }

  private async processMessage(
    text: string,
    state: SessionState,
    channel: "sms" | "whatsapp" | "chat" | "voice"
  ): Promise<string> {
    const lowerText = text.toLowerCase().trim();

    // Giveaway entry
    if (lowerText.includes("giveaway") || lowerText.includes("enter") || lowerText.includes("prize")) {
      state.giveawayEntry = true;
      await this.saveLead(state);
      return this.localize("🎉 You're entered in the giveaway! Prize: " + this.env.GIVEAWAY_PRIZE + ". A sales rep will contact you shortly.", state.language);
    }

    // Demo booking
    if (lowerText.includes("demo") || lowerText.includes("book") || lowerText.includes("schedule")) {
      state.demoRequested = true;
      await this.saveLead(state);
      return this.localize("📅 Great! Let's book a demo. What's your company name?", state.language);
    }

    // Product questions
    if (lowerText.includes("product") || lowerText.includes("what") || lowerText.includes("how")) {
      const answer = await this.answerProductQuestion(text, state.language);
      return answer;
    }

    // Qualification flow
    if (state.step === "welcome" || state.step === "ask_name") {
      if (!state.collected.name) {
        state.step = "ask_name";
        return this.localize("Hi! Welcome to " + this.env.EVENT_NAME + ". What's your name?", state.language);
      }
      if (!state.collected.company) {
        state.step = "ask_company";
        return this.localize("Nice to meet you, " + state.collected.name + "! What company do you work for?", state.language);
      }
      if (!state.collected.useCase) {
        state.step = "ask_usecase";
        return this.localize("What's your primary use case for Telnyx?", state.language);
      }
      if (!state.collected.companySize) {
        state.step = "ask_company_size";
        return this.localize("How many employees are at your company?", state.language);
      }
      if (!state.collected.timeline) {
        state.step = "ask_timeline";
        return this.localize("When are you looking to implement a solution?", state.language);
      }
    }

    // Default: use inference to generate a contextual response
    const contextualResponse = await this.generateAgentResponse(text, state, channel);
    return contextualResponse;
  }

  private async answerProductQuestion(question: string, language: string): Promise<string> {
    try {
      const response = await this.env.TELNYX.ai.openai.chat.createCompletion({
        model: this.env.AI_MODEL || "gpt-4o-mini",
        messages: [
          {
            role: "system",
            content: `You are a helpful product expert for Telnyx at ${this.env.EVENT_NAME || "the event"}. Answer the following question concisely. Respond in ${language}.`,
          },
          { role: "user", content: question },
        ],
      });

      return response.choices[0]?.message?.content?.trim() || "I'm not sure about that. Let me connect you with a specialist.";
    } catch (err) {
      console.error("Product Q&A failed:", err);
      return "I'm not sure about that. Let me connect you with a specialist.";
    }
  }

  private async generateAgentResponse(
    text: string,
    state: SessionState,
    channel: "sms" | "whatsapp" | "chat" | "voice"
  ): Promise<string> {
    try {
      const context = `
You are a multilingual event sponsorship agent for ${this.env.EVENT_NAME || "the event"}.
The attendee's name is ${state.collected.name || "unknown"}.
Their company is ${state.collected.company || "unknown"}.
Their use case is ${state.collected.useCase || "unknown"}.
Their company size is ${state.collected.companySize || "unknown"}.
Their timeline is ${state.collected.timeline || "unknown"}.
They are interacting via ${channel}.
They have entered the giveaway: ${state.giveawayEntry}.
They have requested a demo: ${state.demoRequested}.
Respond helpfully in ${state.language}. Keep responses concise for SMS.
`;

      const response = await this.env.TELNYX.ai.openai.chat.createCompletion({
        model: this.env.AI_MODEL || "gpt-4o-mini",
        messages: [
          { role: "system", content: context },
          { role: "user", content: text },
        ],
      });

      return response.choices[0]?.message?.content?.trim() || "I'm here to help! You can enter the giveaway, ask product questions, or book a demo.";
    } catch (err) {
      console.error("Agent response generation failed:", err);
      return "I'm here to help! You can enter the giveaway, ask product questions, or book a demo.";
    }
  }

  private async generateFollowUpMessage(lead: LeadRecord): Promise<string> {
    const fallback = `Hi ${lead.name || "there"}! Thanks for stopping by ${this.env.EVENT_NAME || "our booth"}. You mentioned ${lead.useCase || "your project"} — happy to pick that conversation back up whenever you're ready.`;

    try {
      const response = await this.env.TELNYX.ai.openai.chat.createCompletion({
        model: this.env.AI_MODEL || "gpt-4o-mini",
        messages: [
          {
            role: "system",
            content: `You are a friendly sales follow-up assistant for ${this.env.EVENT_NAME || "the event"}. Write a short, warm follow-up message. Keep it under 300 characters (SMS-friendly).`,
          },
          {
            role: "user",
            content: `Write a follow-up message for: name=${lead.name || "unknown"}, company=${lead.company || "unknown"}, use case=${lead.useCase || "unknown"}, company size=${lead.companySize || "unknown"}, timeline=${lead.timeline || "unknown"}, demo requested=${lead.channel}.`,
          },
        ],
      });

      return response.choices[0]?.message?.content?.trim() || fallback;
    } catch (err) {
      console.error("Follow-up generation failed:", err);
      return fallback;
    }
  }

  private localize(text: string, language: string): string {
    // In a real implementation, this would use the inference API for translation
    // For now, we return the text as-is (English) since the agent generates responses in the detected language
    return text;
  }

  private async saveLead(state: SessionState): Promise<void> {
    const now = new Date().toISOString();
    const lead: LeadRecord = {
      phone: state.phone,
      name: state.collected.name || "",
      email: state.collected.email || "",
      company: state.collected.company || "",
      useCase: state.collected.useCase || "",
      companySize: state.collected.companySize || "",
      timeline: state.collected.timeline || "",
      channel: state.channel,
      qualified: !!(state.collected.useCase && state.collected.companySize && state.collected.timeline),
      giveawayEntry: state.giveawayEntry,
      createdAt: now,
      updatedAt: now,
    };

    // Upsert into SQLDB
    await this.env.LEADS_DB.exec(`
      CREATE TABLE IF NOT EXISTS leads (
        phone TEXT PRIMARY KEY,
        name TEXT,
        email TEXT,
        company TEXT,
        useCase TEXT,
        companySize TEXT,
        timeline TEXT,
        channel TEXT,
        qualified BOOLEAN,
        giveawayEntry BOOLEAN,
        createdAt TEXT,
        updatedAt TEXT
      )
    `);

    await this.env.LEADS_DB.prepare(`
      INSERT INTO leads (phone, name, email, company, useCase, companySize, timeline, channel, qualified, giveawayEntry, createdAt, updatedAt)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      ON CONFLICT(phone) DO UPDATE SET
        name = excluded.name,
        email = excluded.email,
        company = excluded.company,
        useCase = excluded.useCase,
        companySize = excluded.companySize,
        timeline = excluded.timeline,
        channel = excluded.channel,
        qualified = excluded.qualified,
        giveawayEntry = excluded.giveawayEntry,
        updatedAt = excluded.updatedAt
    `).bind(
      lead.phone,
      lead.name,
      lead.email,
      lead.company,
      lead.useCase,
      lead.companySize,
      lead.timeline,
      lead.channel,
      lead.qualified,
      lead.giveawayEntry,
      lead.createdAt,
      lead.updatedAt
    ).all();

    // If qualified and demo requested, route hot lead to sales team via SMS
    if (lead.qualified && state.demoRequested) {
      await this.routeHotLeadToSales(lead);
    }
  }

  private async getLeadByPhone(phone: string): Promise<LeadRecord | null> {
    const result = await this.env.LEADS_DB.prepare(
      "SELECT * FROM leads WHERE phone = ?"
    ).bind(phone).all();

    if (result.results && result.results.length > 0) {
      return result.results[0] as unknown as LeadRecord;
    }
    return null;
  }

  private async routeHotLeadToSales(lead: LeadRecord): Promise<void> {
    const message = `🔥 HOT LEAD: ${lead.name || "Unknown"} from ${lead.company || "Unknown"} (${lead.phone}). Use case: ${lead.useCase || "N/A"}. Company size: ${lead.companySize || "N/A"}. Timeline: ${lead.timeline || "N/A"}. Demo requested: YES.`;

    if (this.env.DEMO_MODE === "true") {
      console.log(`[DEMO] Would SMS sales team at ${this.env.SALES_TEAM_NUMBER}: ${message}`);
    } else {
      await this.env.TELNYX.messages.send({
        to: this.env.SALES_TEAM_NUMBER,
        from: this.env.FROM_NUMBER,
        text: message,
      });
    }
  }

  private async sendResponse(
    to: string,
    text: string,
    channel: "sms" | "whatsapp" | "chat" | "voice"
  ): Promise<void> {
    if (channel === "chat") {
      // In-browser chat — response is returned directly to the caller
      return;
    }

    if (this.env.DEMO_MODE === "true") {
      console.log(`[DEMO] Would send ${channel} to ${to}: ${text}`);
      return;
    }

    if (channel === "sms") {
      await this.env.TELNYX.messages.send({
        to,
        from: this.env.FROM_NUMBER,
        text,
      });
    } else if (channel === "whatsapp") {
      await this.env.TELNYX.v2.messages.create({
        from: this.env.FROM_NUMBER,
        to,
        channel: "whatsapp",
        text: { body: text },
      });
    }
  }
}

// ---------------------------------------------------------------------------
// Fetch handler — routes HTTP requests to the appropriate actor method.
// Each route resolves the per-attendee actor with `idFromName(...)` and
// invokes its public methods directly on the returned stub.
// ---------------------------------------------------------------------------

/** Normalize a Telnyx webhook `from`/`to` field (string or `{phone_number}`). */
function normalizePhone(field: any): string {
  if (!field) return "";
  if (typeof field === "string") return field;
  if (typeof field === "object" && typeof field.phone_number === "string") return field.phone_number;
  return "";
}

/** Parse a Telnyx webhook body into a normalized shape. */
function parseWebhookJson(rawBody: ArrayBuffer): { from: string; to: string; text: string; callId: string } {
  let body: any = {};
  try {
    body = JSON.parse(new TextDecoder().decode(rawBody));
  } catch {
    body = {};
  }
  const payload = body?.data?.payload ?? body ?? {};

  return {
    from: normalizePhone(payload.from),
    to: normalizePhone(payload.to),
    text: typeof payload.text === "string" ? payload.text : "",
    callId: typeof payload.call_control_id === "string" ? payload.call_control_id : "",
  };
}

export default {
  async fetch(req: Request, e: SponsorEnv): Promise<Response> {
    const url = new URL(req.url);
    const path = url.pathname;

    // Route: Inbound SMS webhook (signature-verified)
    if (path === "/webhook/sms" && req.method === "POST") {
      const raw = await req.arrayBuffer();
      if (verifyTelnyxSignature(req.headers, raw, process.env.TELNYX_PUBLIC_KEY ?? "") !== 0) {
        return new Response(JSON.stringify({ error: "Invalid signature" }), { status: 401 });
      }
      const { from, to, text } = parseWebhookJson(raw);
      if (!from || !text) {
        return new Response(JSON.stringify({ error: "Missing from or text" }), { status: 400 });
      }

      const result = await e.SPONSOR_AGENT.idFromName(from).handleInboundMessage({ from, to, text, channel: "sms" });
      return new Response(JSON.stringify(result), { status: 200 });
    }

    // Route: Inbound WhatsApp webhook (signature-verified)
    if (path === "/webhook/whatsapp" && req.method === "POST") {
      const raw = await req.arrayBuffer();
      if (verifyTelnyxSignature(req.headers, raw, process.env.TELNYX_PUBLIC_KEY ?? "") !== 0) {
        return new Response(JSON.stringify({ error: "Invalid signature" }), { status: 401 });
      }
      const { from, to, text } = parseWebhookJson(raw);
      if (!from || !text) {
        return new Response(JSON.stringify({ error: "Missing from or text" }), { status: 400 });
      }

      const result = await e.SPONSOR_AGENT.idFromName(from).handleInboundMessage({ from, to, text, channel: "whatsapp" });
      return new Response(JSON.stringify(result), { status: 200 });
    }

    // Route: Inbound voice webhook (signature-verified)
    if (path === "/webhook/voice" && req.method === "POST") {
      const raw = await req.arrayBuffer();
      if (verifyTelnyxSignature(req.headers, raw, process.env.TELNYX_PUBLIC_KEY ?? "") !== 0) {
        return new Response(JSON.stringify({ error: "Invalid signature" }), { status: 401 });
      }
      const { from, callId } = parseWebhookJson(raw);
      if (!from || !callId) {
        return new Response(JSON.stringify({ error: "Missing from or call_control_id" }), { status: 400 });
      }

      const result = await e.SPONSOR_AGENT.idFromName(from).handleInboundCall({ callId, from, to: "" });
      return new Response(JSON.stringify(result), { status: 200 });
    }

    // Route: In-browser chat (REST endpoint)
    if (path === "/api/chat" && req.method === "POST") {
      const body = await req.json().catch(() => ({} as any));
      const sessionId = typeof body.sessionId === "string" && body.sessionId ? body.sessionId : `chat:${Date.now()}`;
      const text = typeof body.text === "string" ? body.text : "";

      if (!text) {
        return new Response(JSON.stringify({ error: "Missing text" }), { status: 400 });
      }

      const result = await e.SPONSOR_AGENT.idFromName(sessionId).handleChatMessage({ sessionId, text });
      return new Response(JSON.stringify(result), { status: 200 });
    }

    // Route: Schedule follow-up
    if (path === "/api/followup" && req.method === "POST") {
      const body = await req.json().catch(() => ({} as any));
      const { phone, channel, delaySeconds } = body;

      if (!phone || !channel || !delaySeconds) {
        return new Response(JSON.stringify({ error: "Missing phone, channel, or delaySeconds" }), { status: 400 });
      }

      const result = await e.SPONSOR_AGENT.idFromName(phone).scheduleFollowUp({ phone, channel, delaySeconds });
      return new Response(JSON.stringify(result), { status: 200 });
    }

    // Route: Attribution report
    if (path === "/api/report" && req.method === "GET") {
      const report = await e.SPONSOR_AGENT.idFromName("report").generateAttributionReport();
      return new Response(JSON.stringify(report), { status: 200 });
    }

    // Route: Health check
    if (path === "/health" && req.method === "GET") {
      return new Response(JSON.stringify({ status: "ok", service: "event-sponsorship-agent" }), { status: 200 });
    }

    // Default: serve microsite
    if (path === "/" || path === "/index.html") {
      const html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${e.EVENT_NAME || "Event Sponsorship"}</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; }
    #chat { height: 400px; border: 1px solid #ddd; padding: 10px; overflow-y: auto; margin-bottom: 10px; }
    .msg { margin: 5px 0; padding: 8px; border-radius: 4px; }
    .user { background: #e3f2fd; }
    .agent { background: #f5f5f5; }
    #input { width: 80%; padding: 8px; }
    button { padding: 8px 12px; }
  </style>
</head>
<body>
  <h1>${e.EVENT_NAME || "Event Sponsorship"}</h1>
  <p>Text, call, or chat with our agent to enter the giveaway, ask product questions, or book a demo!</p>
  <div id="chat"></div>
  <input type="text" id="input" placeholder="Type a message..." />
  <button onclick="sendMessage()">Send</button>
  <script>
    const sessionId = 'web_' + Date.now();
    const chatEl = document.getElementById('chat');
    function addMessage(text, cls) {
      const div = document.createElement('div');
      div.className = 'msg ' + cls;
      div.textContent = text;
      chatEl.appendChild(div);
      chatEl.scrollTop = chatEl.scrollHeight;
    }
    async function sendMessage() {
      const input = document.getElementById('input');
      const text = input.value.trim();
      if (!text) return;
      addMessage(text, 'user');
      input.value = '';
      const resp = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sessionId, text })
      });
      const data = await resp.json();
      addMessage(data.message, 'agent');
    }
    document.getElementById('input').addEventListener('keypress', (e) => {
      if (e.key === 'Enter') sendMessage();
    });
  </script>
</body>
</html>`;
      return new Response(html, { headers: { "Content-Type": "text/html" } });
    }

    return new Response("Not Found", { status: 404 });
  },
};
