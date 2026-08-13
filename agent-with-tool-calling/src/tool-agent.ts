import { Agent } from "@telnyx/edge-runtime";
import type {
  Env,
  EventsResponse,
  ProcessLogEvent,
  ProcessLogRow,
  ReceiveMessageInput,
  TelnyxEdgeClient,
  ToolEvent,
  ToolLogRow,
  ToolName,
  ToolState,
} from "./types.js";

const DEFAULT_MODEL = "zai-org/GLM-5.2";

const TOOL_SYSTEM_PROMPT = `You are a concise SMS assistant with three tools: send_sms, make_call, and check_status.

Rules:
- If the user asks you to text or send a message to a phone number, call send_sms.
- If the user asks you to call a phone number, call make_call.
- If the user asks about whether a prior action happened, call check_status.
- Require E.164 phone numbers. If a request is missing a phone number, ask for it instead of guessing.
- After a tool runs, summarize what happened in one short sentence.
- If send_sms returns status "mocked", say it was completed in demo mode and do not claim carrier delivery.`;

const TOOL_DEFINITIONS = [
  {
    type: "function",
    function: {
      name: "send_sms",
      description: "Send an SMS message to a phone number",
      parameters: {
        type: "object",
        properties: {
          to: { type: "string", description: "E.164 phone number, e.g. +13125550001" },
          body: { type: "string", description: "The SMS body to send" },
        },
        required: ["to", "body"],
      },
    },
  },
  {
    type: "function",
    function: {
      name: "make_call",
      description: "Place an outbound phone call to a phone number",
      parameters: {
        type: "object",
        properties: {
          to: { type: "string", description: "E.164 phone number to call" },
        },
        required: ["to"],
      },
    },
  },
  {
    type: "function",
    function: {
      name: "check_status",
      description: "Check the status of a previous SMS or call by tool name",
      parameters: {
        type: "object",
        properties: {
          what: {
            type: "string",
            enum: ["send_sms", "make_call"],
            description: "Which tool to check",
          },
        },
        required: ["what"],
      },
    },
  },
];

interface NormalizedToolCall {
  id: string;
  name: string;
  args: unknown;
}

function telnyx(env: Env): TelnyxEdgeClient {
  return env.TELNYX as unknown as TelnyxEdgeClient;
}

function smsTransportEnabled(env: Env): boolean {
  return env.SMS_TRANSPORT === "production";
}

function maxIterations(env: Env): number {
  const parsed = Number(env.MAX_TOOL_ITERATIONS || "3");
  if (!Number.isFinite(parsed)) return 3;
  return Math.max(1, Math.min(8, Math.floor(parsed)));
}

function callControlAppId(env: Env): string {
  const configured = env.CALL_CONTROL_APP_ID || "";
  return configured.startsWith("<") ? "" : configured;
}

function isE164(value: unknown): value is string {
  return typeof value === "string" && /^\+[1-9]\d{6,14}$/.test(value);
}

function normalizePhone(value: unknown): string | undefined {
  if (typeof value !== "string") return undefined;
  const trimmed = value.trim();
  if (/^\+[1-9]\d{6,14}$/.test(trimmed)) return trimmed;
  const digits = trimmed.replace(/\D/g, "");
  if (digits.length === 10) return `+1${digits}`;
  if (digits.length === 11 && digits.startsWith("1")) return `+${digits}`;
  return undefined;
}

function parseArgs(raw: string): unknown {
  try {
    return JSON.parse(raw);
  } catch {
    return {};
  }
}

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value)
    ? value as Record<string, unknown>
    : {};
}

function normalizeToolArgs(name: string, args: unknown): unknown {
  const parsed = asRecord(args);
  if (name === "send_sms") {
    return {
      to: normalizePhone(parsed.to) || parsed.to,
      body: typeof parsed.body === "string" ? parsed.body.trim() : parsed.body,
    };
  }
  if (name === "make_call") {
    return {
      to: normalizePhone(parsed.to) || parsed.to,
    };
  }
  if (name === "check_status") {
    return { what: parsed.what };
  }
  return args;
}

function stableJson(value: unknown): string {
  if (!value || typeof value !== "object" || Array.isArray(value)) return JSON.stringify(value);
  const record = value as Record<string, unknown>;
  const sorted: Record<string, unknown> = {};
  for (const key of Object.keys(record).sort()) sorted[key] = record[key];
  return JSON.stringify(sorted);
}

function errorMessage(error: unknown): string {
  if (error instanceof Error) return error.message;
  const record = asRecord(error);
  if (typeof record.message === "string") return record.message;
  return "Telnyx Call Control request failed";
}

function toToolEvent(row: ToolLogRow): ToolEvent {
  return {
    id: row.id,
    tool_call_id: row.tool_call_id,
    tool: row.tool,
    args: parseArgs(row.args),
    result: parseArgs(row.result),
    status: row.status,
    at: row.at,
  };
}

function toProcessLogEvent(row: ProcessLogRow): ProcessLogEvent {
  return {
    id: row.id,
    iteration: row.iteration,
    phase: row.phase,
    tool_choice: row.tool_choice,
    finish_reason: row.finish_reason,
    tool_calls: parseArgs(row.tool_calls),
    note: row.note,
    at: row.at,
  };
}

export class ToolAgent extends Agent<Env, ToolState> {
  protected override initialState(): ToolState {
    return { from: "", to: "", iterations: 0, lastReply: "", updatedAt: 0 };
  }

  async receive({ text, from, to, eventId }: ReceiveMessageInput): Promise<void> {
    this.ensureTables();

    try {
      this.ctx.storage.sql.exec(
        "INSERT INTO webhook_events(event_id, at) VALUES (?, ?)",
        eventId,
        Date.now(),
      );
    } catch {
      return;
    }

    const now = Date.now();
    await this.setState({ from, to, iterations: 0, updatedAt: now });
    await this.messages.add("user", text);
    this.ctx.storage.sql.exec(
      "INSERT INTO conversation(role, content, at) VALUES (?, ?, ?)",
      "user",
      text,
      now,
    );
    await this.queue("process");
  }

  async process(): Promise<void> {
    this.ensureTables();

    const state = await this.getState();
    if (!state.from || !state.to) return;
    if (state.iterations >= maxIterations(this.env)) {
      await this.finish("I stopped because the tool loop hit its safety limit. Please try a simpler request.");
      return;
    }

    const lastMessage = await this.messages.last();
    const toolChoice = lastMessage?.role === "tool" ? "none" : "auto";
    const history = await this.messages.toOpenAI();
    this.logProcess({
      iteration: state.iterations,
      phase: "before_model",
      toolChoice,
      finishReason: null,
      toolCalls: [],
      note: `history_messages=${history.length}; last_role=${lastMessage?.role || "none"}`,
    });
    const response = await telnyx(this.env).ai.openai.chat.createCompletion({
      model: this.env.MODEL || DEFAULT_MODEL,
      messages: [{ role: "system", content: TOOL_SYSTEM_PROMPT }, ...history],
      tools: TOOL_DEFINITIONS,
      tool_choice: toolChoice,
    });

    const message = response.choices[0]?.message;
    const finishReason = response.choices[0]?.finish_reason || null;
    if (!message) {
      this.logProcess({
        iteration: state.iterations,
        phase: "after_model",
        toolChoice,
        finishReason,
        toolCalls: [],
        note: "model returned no message",
      });
      await this.finish("I could not get a model response. Please try again.");
      return;
    }

    if (message.tool_calls?.length) {
      const toolCalls = message.tool_calls.map<NormalizedToolCall>((toolCall) => ({
        id: toolCall.id,
        name: toolCall.function.name,
        args: normalizeToolArgs(toolCall.function.name, parseArgs(toolCall.function.arguments)),
      }));

      this.logProcess({
        iteration: state.iterations,
        phase: "after_model",
        toolChoice,
        finishReason,
        toolCalls,
        note: "model requested tools",
      });

      await this.messages.append({
        role: "assistant",
        content: message.content || "",
        toolCalls,
      });

      for (const toolCall of toolCalls) {
        const result = await this.dispatchToolOnce(
          toolCall.id,
          toolCall.name,
          toolCall.args,
          state.from,
          state.to,
        );
        await this.messages.append({
          role: "tool",
          content: JSON.stringify(result),
          toolCallId: toolCall.id,
          name: toolCall.name,
        });
      }

      await this.setState({ iterations: state.iterations + 1, updatedAt: Date.now() });
      await this.queue("process");
      return;
    }

    this.logProcess({
      iteration: state.iterations,
      phase: "after_model",
      toolChoice,
      finishReason,
      toolCalls: [],
      note: "model returned final assistant message",
    });
    await this.finish(message.content || "Done.");
  }

  async getEvents(limit = 50): Promise<EventsResponse> {
    this.ensureTables();
    const boundedLimit = Math.max(1, Math.min(100, Math.floor(limit)));
    const toolRows = this.ctx.storage.sql
      .exec<ToolLogRow>(
        `SELECT id, tool_call_id, tool, args, result, status, at
         FROM tool_log
         ORDER BY id DESC
         LIMIT ?`,
        boundedLimit,
      )
      .toArray();
    const conversation = this.ctx.storage.sql
      .exec<{ id: number; role: "user" | "assistant"; content: string; at: number }>(
        `SELECT id, role, content, at
         FROM conversation
         ORDER BY id DESC
         LIMIT ?`,
        boundedLimit,
      )
      .toArray();
    const processRows = this.ctx.storage.sql
      .exec<ProcessLogRow>(
        `SELECT id, iteration, phase, tool_choice, finish_reason, tool_calls, note, at
         FROM process_log
         ORDER BY id DESC
         LIMIT ?`,
        boundedLimit,
      )
      .toArray();

    return {
      toolEvents: toolRows.map(toToolEvent),
      conversation,
      processLog: processRows.map(toProcessLogEvent),
    };
  }

  private async finish(reply: string): Promise<void> {
    const { from, to } = await this.getState();
    const text = reply.trim().slice(0, 1000) || "Done.";
    const now = Date.now();

    await this.messages.add("assistant", text);
    this.ctx.storage.sql.exec(
      "INSERT INTO conversation(role, content, at) VALUES (?, ?, ?)",
      "assistant",
      text,
      now,
    );

    if (smsTransportEnabled(this.env) && from && to) {
      try {
        await telnyx(this.env).messages.send({ from: to, to: from, text });
      } catch {
        // Tool results are still logged; production reply delivery can be inspected in Telnyx logs.
      }
    }

    await this.setState({ iterations: 0, lastReply: text, updatedAt: now });
  }

  private async dispatchToolOnce(
    toolCallId: string,
    name: string,
    args: unknown,
    from: string,
    to: string,
  ): Promise<unknown> {
    const normalizedArgs = normalizeToolArgs(name, args);
    const existing = this.ctx.storage.sql
      .exec<{ result: string }>(
        "SELECT result FROM tool_log WHERE tool_call_id = ? AND status = 'done' LIMIT 1",
        toolCallId,
      )
      .toArray()[0];
    if (existing) return parseArgs(existing.result);

    const sameSuccessfulTool = this.ctx.storage.sql
      .exec<{ result: string }>(
        `SELECT result
         FROM tool_log
         WHERE tool = ? AND args = ? AND status = 'done'
         ORDER BY id DESC
         LIMIT 1`,
        name,
        stableJson(normalizedArgs),
      )
      .toArray()[0];
    if (sameSuccessfulTool) {
      const result = parseArgs(sameSuccessfulTool.result);
      if (asRecord(result).ok === true) {
        const deduped = { ...asRecord(result), duplicate_suppressed: true };
        this.ctx.storage.sql.exec(
          `INSERT INTO tool_log(tool_call_id, tool, args, result, status, at)
           VALUES (?, ?, ?, ?, 'done', ?)
           ON CONFLICT(tool_call_id) DO UPDATE SET
             result = excluded.result,
             status = 'done',
             at = excluded.at`,
          toolCallId,
          name,
          stableJson(normalizedArgs),
          JSON.stringify(deduped),
          Date.now(),
        );
        return deduped;
      }
    }

    const result = await this.dispatchTool(toolCallId, name, normalizedArgs, from, to);
    this.ctx.storage.sql.exec(
      `INSERT INTO tool_log(tool_call_id, tool, args, result, status, at)
       VALUES (?, ?, ?, ?, 'done', ?)
       ON CONFLICT(tool_call_id) DO UPDATE SET
         result = excluded.result,
         status = 'done',
         at = excluded.at`,
      toolCallId,
      name,
      stableJson(normalizedArgs),
      JSON.stringify(result),
      Date.now(),
    );
    return result;
  }

  private async dispatchTool(
    toolCallId: string,
    name: string,
    args: unknown,
    _from: string,
    to: string,
  ): Promise<unknown> {
    if (name === "send_sms") {
      return this.sendSms(toolCallId, args, to);
    }
    if (name === "make_call") {
      return this.makeCall(toolCallId, args, to);
    }
    if (name === "check_status") {
      return this.checkStatus(args);
    }
    return { ok: false, tool: name, error: `unknown tool: ${name}` };
  }

  private async sendSms(toolCallId: string, args: unknown, fromNumber: string): Promise<unknown> {
    const parsed = asRecord(args);
    const to = parsed.to;
    const body = parsed.body;
    if (!isE164(to)) return { ok: false, tool: "send_sms", error: "to must be an E.164 phone number" };
    if (typeof body !== "string" || !body.trim()) {
      return { ok: false, tool: "send_sms", error: "body is required" };
    }

    if (!smsTransportEnabled(this.env)) {
      return {
        ok: true,
        tool: "send_sms",
        status: "mocked",
        message_id: `demo_${toolCallId}`,
        to,
        body: body.trim(),
      };
    }

    let response;
    try {
      response = await telnyx(this.env).messages.send({
        from: fromNumber,
        to,
        text: body.trim(),
      });
    } catch (error) {
      return {
        ok: false,
        tool: "send_sms",
        error: errorMessage(error),
        from: fromNumber,
        to,
        body: body.trim(),
      };
    }
    return {
      ok: true,
      tool: "send_sms",
      status: "sent",
      message_id: response.data?.id,
      to,
      body: body.trim(),
    };
  }

  private async makeCall(toolCallId: string, args: unknown, fromNumber: string): Promise<unknown> {
    const parsed = asRecord(args);
    const to = parsed.to;
    if (!isE164(to)) return { ok: false, tool: "make_call", error: "to must be an E.164 phone number" };
    const connectionId = callControlAppId(this.env);
    if (!connectionId) {
      return {
        ok: false,
        tool: "make_call",
        error: "CALL_CONTROL_APP_ID is not configured",
        to,
      };
    }

    let response;
    try {
      response = await telnyx(this.env).calls.dial({
        connection_id: connectionId,
        from: fromNumber,
        to,
        command_id: toolCallId,
      });
    } catch (error) {
      return {
        ok: false,
        tool: "make_call",
        error: errorMessage(error),
        from: fromNumber,
        to,
      };
    }

    return {
      ok: true,
      tool: "make_call",
      status: response.data.status || "queued",
      call_control_id: response.data.call_control_id,
      call_leg_id: response.data.call_leg_id,
      call_session_id: response.data.call_session_id,
      to,
    };
  }

  private checkStatus(args: unknown): unknown {
    const parsed = asRecord(args);
    const what = parsed.what;
    if (what !== "send_sms" && what !== "make_call") {
      return { ok: false, tool: "check_status", error: "what must be send_sms or make_call" };
    }

    const row = this.ctx.storage.sql
      .exec<ToolLogRow>(
        `SELECT id, tool_call_id, tool, args, result, status, at
         FROM tool_log
         WHERE tool = ?
         ORDER BY id DESC
         LIMIT 1`,
        what,
      )
      .toArray()[0];

    if (!row) return { ok: false, tool: "check_status", error: `no prior ${what} call found` };
    return { ok: true, tool: "check_status", checked: what, last: toToolEvent(row) };
  }

  private ensureTables(): void {
    this.ctx.storage.sql.exec(
      `CREATE TABLE IF NOT EXISTS webhook_events(
         event_id TEXT PRIMARY KEY,
         at INTEGER
       )`,
    );
    this.ctx.storage.sql.exec(
      `CREATE TABLE IF NOT EXISTS tool_log(
         id INTEGER PRIMARY KEY AUTOINCREMENT,
         tool_call_id TEXT UNIQUE NOT NULL,
         tool TEXT NOT NULL,
         args TEXT NOT NULL,
         result TEXT NOT NULL,
         status TEXT NOT NULL,
         at INTEGER NOT NULL
       )`,
    );
    this.ctx.storage.sql.exec(
      `CREATE TABLE IF NOT EXISTS conversation(
         id INTEGER PRIMARY KEY AUTOINCREMENT,
         role TEXT NOT NULL,
         content TEXT NOT NULL,
         at INTEGER NOT NULL
       )`,
    );
    this.ctx.storage.sql.exec(
      `CREATE TABLE IF NOT EXISTS process_log(
         id INTEGER PRIMARY KEY AUTOINCREMENT,
         iteration INTEGER NOT NULL,
         phase TEXT NOT NULL,
         tool_choice TEXT NOT NULL,
         finish_reason TEXT,
         tool_calls TEXT NOT NULL,
         note TEXT NOT NULL,
         at INTEGER NOT NULL
       )`,
    );
  }

  private logProcess({
    iteration,
    phase,
    toolChoice,
    finishReason,
    toolCalls,
    note,
  }: {
    iteration: number;
    phase: string;
    toolChoice: string;
    finishReason: string | null;
    toolCalls: unknown[];
    note: string;
  }): void {
    this.ctx.storage.sql.exec(
      `INSERT INTO process_log(iteration, phase, tool_choice, finish_reason, tool_calls, note, at)
       VALUES (?, ?, ?, ?, ?, ?, ?)`,
      iteration,
      phase,
      toolChoice,
      finishReason,
      JSON.stringify(toolCalls),
      note,
      Date.now(),
    );
  }
}
