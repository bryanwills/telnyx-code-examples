import { Agent } from "@telnyx/edge-runtime";
import type {
  Env,
  ReceiveMessageInput,
  SentimentLabel,
  SentimentRow,
  SentimentState,
} from "./types.js";

const SENTIMENT_SYSTEM_PROMPT = `You classify inbound SMS sentiment for a support team.
Return only valid JSON with this shape:
{"label":"positive|neutral|negative","score":0.0,"reply":"short SMS reply"}

Rules:
- label must be exactly one of positive, neutral, negative.
- score is confidence from 0 to 1.
- reply must be brief, useful, and empathetic.
- If the sender is angry, frustrated, or mentions refund/churn/broken service, use label negative.`;

interface ParsedSentiment {
  label: SentimentLabel;
  score: number;
  reply: string;
}

const DEFAULT_REPLY = "Thanks for your message. We have it and will follow up shortly.";

function isDemo(env: Env): boolean {
  return env.PRODUCTION_MODE !== "true";
}

function clampScore(score: unknown): number {
  const parsed = typeof score === "number" ? score : Number(score);
  if (!Number.isFinite(parsed)) return 0;
  return Math.max(0, Math.min(1, parsed));
}

function normalizeLabel(label: unknown): SentimentLabel {
  if (label === "positive" || label === "neutral" || label === "negative") return label;
  return "neutral";
}

function extractJsonObject(raw: string): string {
  const trimmed = raw.trim();
  if (trimmed.startsWith("{") && trimmed.endsWith("}")) return trimmed;
  const match = trimmed.match(/\{[\s\S]*\}/);
  return match?.[0] ?? "{}";
}

function parseSentiment(raw: string): ParsedSentiment {
  try {
    const parsed = JSON.parse(extractJsonObject(raw)) as Partial<ParsedSentiment>;
    const label = normalizeLabel(parsed.label);
    const score = clampScore(parsed.score);
    const reply = typeof parsed.reply === "string" && parsed.reply.trim()
      ? parsed.reply.trim().slice(0, 320)
      : DEFAULT_REPLY;
    return { label, score, reply };
  } catch {
    return { label: "neutral", score: 0, reply: DEFAULT_REPLY };
  }
}

export class SentimentAgent extends Agent<Env, SentimentState> {
  protected override initialState(): SentimentState {
    return { from: "", to: "", lastLabel: "", lastAt: 0 };
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

    await this.setState({ from, to });
    await this.messages.add("user", text);
    await this.queue("process");
  }

  async process(): Promise<void> {
    this.ensureTables();

    const { from, to } = await this.getState();
    const last = await this.messages.last();
    if (!from || !to || !last || last.role !== "user") return;

    const response = await this.env.TELNYX.ai.openai.chat.createCompletion({
      model: this.env.MODEL || "zai-org/GLM-5.2",
      messages: [
        { role: "system", content: SENTIMENT_SYSTEM_PROMPT },
        { role: "user", content: last.content },
      ],
    });

    const raw = response.choices[0]?.message?.content ?? "{}";
    const sentiment = parseSentiment(raw);
    const escalated = sentiment.label === "negative";
    const now = Date.now();

    this.ctx.storage.sql.exec(
      `INSERT INTO sentiment(sender, message, label, score, escalated, reply, at)
       VALUES (?, ?, ?, ?, ?, ?, ?)`,
      from,
      last.content,
      sentiment.label,
      sentiment.score,
      escalated ? 1 : 0,
      sentiment.reply,
      now,
    );

    if (escalated && !isDemo(this.env) && this.env.OPS_ALERT_PHONE) {
      await this.env.TELNYX.messages.send({
        from: to,
        to: this.env.OPS_ALERT_PHONE,
        text: `Negative sentiment (${sentiment.score.toFixed(2)}) from ${from}: "${last.content}"`,
      });
    }

    if (!isDemo(this.env)) {
      await this.env.TELNYX.messages.send({ from: to, to: from, text: sentiment.reply });
    }

    await this.messages.add("assistant", sentiment.reply);
    await this.setState({ lastLabel: sentiment.label, lastAt: now });
  }

  async getEvents(limit = 50): Promise<SentimentRow[]> {
    this.ensureTables();

    return this.ctx.storage.sql
      .exec<{
        id: number;
        sender: string;
        message: string;
        label: SentimentLabel;
        score: number;
        escalated: number;
        reply: string;
        at: number;
      }>(
        `SELECT id, sender, message, label, score, escalated, reply, at
         FROM sentiment
         ORDER BY id DESC
         LIMIT ?`,
        Math.max(1, Math.min(100, limit)),
      )
      .toArray()
      .map((row) => ({ ...row, escalated: row.escalated === 1 }));
  }

  async resetEvents(): Promise<void> {
    this.ensureTables();
    this.ctx.storage.sql.exec("DELETE FROM sentiment");
    this.ctx.storage.sql.exec("DELETE FROM webhook_events");
    await this.setState({ lastLabel: "", lastAt: 0 });
  }

  private ensureTables(): void {
    this.ctx.storage.sql.exec(
      `CREATE TABLE IF NOT EXISTS webhook_events(
         event_id TEXT PRIMARY KEY,
         at INTEGER
       )`,
    );
    this.ctx.storage.sql.exec(
      `CREATE TABLE IF NOT EXISTS sentiment(
         id INTEGER PRIMARY KEY AUTOINCREMENT,
         sender TEXT NOT NULL,
         message TEXT NOT NULL,
         label TEXT NOT NULL,
         score REAL NOT NULL,
         escalated INTEGER NOT NULL,
         reply TEXT NOT NULL,
         at INTEGER NOT NULL
       )`,
    );
  }
}
