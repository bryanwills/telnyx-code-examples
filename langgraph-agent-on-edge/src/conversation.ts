import { Agent } from "@telnyx/edge-runtime";
import { SystemMessage, HumanMessage, AIMessage, type BaseMessage } from "@langchain/core/messages";
import { buildGraph } from "./graph.js";
import type {
  ConvState,
  Env,
  EventsResponse,
  ConversationEvent,
  ProcessLogRow,
  ProcessLogEvent,
  ReceiveMessageInput,
  TelnyxEdgeClient,
  Intent,
} from "./types.js";

const DEFAULT_MODEL = "zai-org/GLM-5.2";
const NUDGE_TEXT = "Just checking in — did that sort things out?";
const NUDGE_DELAY_SECONDS = 86_400;

function telnyx(env: Env): TelnyxEdgeClient {
  return env.TELNYX as unknown as TelnyxEdgeClient;
}

function smsTransportEnabled(env: Env): boolean {
  return env.SMS_TRANSPORT === "production";
}

function modelId(env: Env): string {
  return env.MODEL || DEFAULT_MODEL;
}

function toBaseMessages(history: Array<{ role: string; content: string }>): BaseMessage[] {
  return history.map((m) => {
    if (m.role === "user") return new HumanMessage(m.content);
    if (m.role === "system") return new SystemMessage(m.content);
    if (m.role === "tool") return new HumanMessage(m.content);
    return new AIMessage(m.content);
  });
}

export class Conversation extends Agent<Env, ConvState> {
  protected override initialState(): ConvState {
    return {
      from: "",
      to: "",
      turn: 0,
      queuedTurn: 0,
      processingTurn: 0,
      lastSentTurn: 0,
      pendingOutbound: null,
      lastIntent: "unknown" as Intent,
      at: 0,
    };
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

    const state = await this.getState();
    const turn = state.turn + 1;
    const now = Date.now();

    await this.messages.add("user", text);
    this.ctx.storage.sql.exec(
      "INSERT INTO conversation(role, content, at) VALUES (?, ?, ?)",
      "user",
      text,
      now,
    );

    await this.setState({
      from,
      to,
      turn,
      queuedTurn: turn,
    });

    this.logProcess(turn, "receive", "unknown", `queued; text="${text.slice(0, 80)}"`);
    await this.queue("process");
  }

  async process(): Promise<void> {
    this.ensureTables();

    const state = await this.getState();
    if (!state.from || !state.to) return;

    const targetTurn = state.queuedTurn;

    if (targetTurn <= state.lastSentTurn) {
      this.logProcess(targetTurn, "stale_noop", "unknown", `target=${targetTurn} <= lastSent=${state.lastSentTurn}`);
      return;
    }

    await this.setState({ processingTurn: targetTurn });
    this.logProcess(targetTurn, "process_start", "unknown", `target=${targetTurn}; lastSent=${state.lastSentTurn}`);

    const history = await this.messages.toLangChain();
    const baseMessages = toBaseMessages(history);
    const messages = [new SystemMessage("You are a concise SMS support agent for Telnyx Logistics."), ...baseMessages];

    const graph = buildGraph(this.env, modelId(this.env));
    const out = await graph.invoke({ messages });

    const reply = String(out.replyText ?? "").trim() || "I'll get back to you shortly.";
    const intent = (out.intentLabel as Intent) || "unknown";

    this.logProcess(targetTurn, "graph_done", intent, `reply="${reply.slice(0, 80)}"`);

    const clientRef = `turn-${targetTurn}`;
    await this.setState({
      pendingOutbound: { turn: targetTurn, reply, clientRef },
    });

    await this.messages.add("assistant", reply);
    this.ctx.storage.sql.exec(
      "INSERT INTO conversation(role, content, at) VALUES (?, ?, ?)",
      "assistant",
      reply,
      Date.now(),
    );

    const { from, to } = await this.getState();

    if (smsTransportEnabled(this.env) && from && to) {
      await telnyx(this.env).messages.send({ from: to, to: from, text: reply });
      this.logProcess(targetTurn, "sms_sent", intent, `clientRef=${clientRef}`);
    } else {
      this.logProcess(targetTurn, "sms_mocked", intent, `clientRef=${clientRef}; text="${reply.slice(0, 80)}"`);
    }

    await this.setState({
      lastSentTurn: targetTurn,
      processingTurn: 0,
      pendingOutbound: null,
      at: Date.now(),
      lastIntent: intent,
    });

    this.logProcess(targetTurn, "commit", intent, `lastSentTurn=${targetTurn}`);

    const s2 = await this.getState();
    if (s2.queuedTurn > targetTurn) {
      this.logProcess(targetTurn, "requeue", intent, `queuedTurn=${s2.queuedTurn} > target=${targetTurn}`);
      await this.queue("process");
    }

    await this.schedule(NUDGE_DELAY_SECONDS, "nudge", null, { id: "nudge" });
  }

  async nudge(): Promise<void> {
    const state = await this.getState();
    if (!state.from || !state.to) return;

    const last = await this.messages.last();
    if (last?.role === "assistant") return;

    if (smsTransportEnabled(this.env)) {
      try {
        await telnyx(this.env).messages.send({
          from: state.to,
          to: state.from,
          text: NUDGE_TEXT,
        });
      } catch {
        return;
      }
    }

    this.logProcess(state.turn, "nudge", "unknown", "sent nudge");
  }

  async getEvents(limit = 50): Promise<EventsResponse> {
    this.ensureTables();
    const boundedLimit = Math.max(1, Math.min(100, Math.floor(limit)));

    const conversation = this.ctx.storage.sql
      .exec<ConversationEvent>(
        `SELECT id, role, content, at FROM conversation ORDER BY id DESC LIMIT ?`,
        boundedLimit,
      )
      .toArray();

    const processRows = this.ctx.storage.sql
      .exec<ProcessLogRow>(
        `SELECT id, turn, phase, intent, note, at FROM process_log ORDER BY id DESC LIMIT ?`,
        boundedLimit,
      )
      .toArray();

    const state = await this.getState();

    return {
      conversation,
      processLog: processRows.map((row): ProcessLogEvent => ({
        id: row.id,
        turn: row.turn,
        phase: row.phase,
        intent: row.intent,
        note: row.note,
        at: row.at,
      })),
      turnState: {
        turn: state.turn,
        queuedTurn: state.queuedTurn,
        processingTurn: state.processingTurn,
        lastSentTurn: state.lastSentTurn,
        pendingOutbound: state.pendingOutbound,
      },
    };
  }

  private ensureTables(): void {
    this.ctx.storage.sql.exec(
      `CREATE TABLE IF NOT EXISTS webhook_events(event_id TEXT PRIMARY KEY, at INTEGER)`,
    );
    this.ctx.storage.sql.exec(
      `CREATE TABLE IF NOT EXISTS conversation(id INTEGER PRIMARY KEY AUTOINCREMENT, role TEXT NOT NULL, content TEXT NOT NULL, at INTEGER NOT NULL)`,
    );
    this.ctx.storage.sql.exec(
      `CREATE TABLE IF NOT EXISTS process_log(id INTEGER PRIMARY KEY AUTOINCREMENT, turn INTEGER, phase TEXT, intent TEXT, note TEXT, at INTEGER)`,
    );
  }

  private logProcess(turn: number, phase: string, intent: string, note: string): void {
    this.ctx.storage.sql.exec(
      "INSERT INTO process_log(turn, phase, intent, note, at) VALUES (?, ?, ?, ?, ?)",
      turn,
      phase,
      intent,
      note,
      Date.now(),
    );
  }
}
