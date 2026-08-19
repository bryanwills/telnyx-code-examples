import { Agent } from "@telnyx/edge-runtime";

// ── State ────────────────────────────────────────────────────────────────
export type CallPhase =
  | "init"
  | "answering"
  | "transcribing"
  | "summarizing"
  | "sending"
  | "done"
  | "error";

export interface TranscriptSegment {
  text: string;
  at: number;
  isFinal: boolean;
}

export interface TranscribeState extends Record<string, unknown> {
  callControlId: string;
  from: string;
  to: string;
  phase: CallPhase;
  segments: TranscriptSegment[];
  transcriptText: string;
  summary: string;
  startedAt: number;
  endedAt: number;
  turnCount: number;
  error: string;
}

// ── Env: [telnyx] binding + API key secret + config + registry namespace ──
interface RegistryStub {
  record(row: TranscriptRecord): Promise<void>;
}
interface RegistryNamespace {
  idFromName(name: string): RegistryStub;
}

interface TranscribeEnv {
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
    messages: {
      send(m: { from: string; to: string; text: string }): Promise<unknown>;
    };
  };
  TELNYX_API_KEY: string;
  AI_MODEL: string;
  SMS_FROM: string;
  SMS_TO: string;
  REGISTRY: RegistryNamespace;
}

export interface TranscriptRecord {
  call_control_id: string;
  from_number: string;
  to_number: string;
  transcript: string;
  summary: string;
  started_at: number;
  ended_at: number;
  turn_count: number;
  status: string;
  [key: string]: string | number;
}

const DEFAULT_MODEL = "zai-org/GLM-5.2";

const SUMMARY_SYSTEM_PROMPT = `You are a call summarizer. Given a raw call transcript, produce a concise SMS-friendly summary in 1-3 sentences. Include:
- Who called (if mentioned)
- The key points discussed
- Any action items, deadlines, or follow-ups
Keep it under 320 characters so it fits in one or two SMS segments. Do not add labels, headers, or quotes — just the summary text.`;

/**
 * TranscribeAgent — one actor instance per inbound call (keyed by call_control_id).
 *
 * Lifecycle (driven by webhook handler in index.ts):
 *   1. recordStart()             — capture callId, from, to, phase
 *   2. appendTranscript(text)    — caller STT final segments accumulate into state
 *   3. onHangup()                — pipeline: summarize → store → sms → done
 *
 * Live transcript lives in this.getState()/setState() (durable).
 * On hangup: LLM summary via this.env.TELNYX.ai.openai.chat.createCompletion(),
 * SMS summary via this.env.TELNYX.messages.send(), and a SQL row is written to
 * this.ctx.storage.sql (per-call) AND a TranscriptRecord is sent to the shared
 * TranscriptRegistry actor for cross-call listing.
 */
export class TranscribeAgent extends Agent<TranscribeEnv, TranscribeState> {
  protected override initialState(): TranscribeState {
    return {
      callControlId: "",
      from: "",
      to: "",
      phase: "init",
      segments: [],
      transcriptText: "",
      summary: "",
      startedAt: 0,
      endedAt: 0,
      turnCount: 0,
      error: "",
    };
  }

  /** Webhook handler calls this on call.initiated. */
  async recordStart(callControlId: string, from: string, to: string): Promise<void> {
    this.ensureTables();
    await this.setState({
      callControlId,
      from,
      to,
      phase: "answering",
      segments: [],
      transcriptText: "",
      summary: "",
      startedAt: Date.now(),
      endedAt: 0,
      turnCount: 0,
      error: "",
    });
    this.ctx.storage.sql.exec(
      `INSERT OR REPLACE INTO transcript
       (call_control_id, from_number, to_number, transcript, summary, started_at, ended_at, turn_count, status)
       VALUES (?, ?, ?, '', '', ?, 0, 0, 'transcribing')`,
      callControlId,
      from,
      to,
      Date.now(),
    );
  }

  /** Mark transcribing (call.answered + speak.ended). */
  async setTranscribing(): Promise<void> {
    const state = await this.getState();
    await this.setState({ ...state, phase: "transcribing" });
  }

  /**
   * Append a transcript segment. Final segments accumulate into transcriptText
   * (used for the LLM summary); interim segments are kept in `segments` for the
   * live dashboard but not yet committed to transcriptText.
   */
  async appendTranscript(text: string, isFinal: boolean): Promise<void> {
    const trimmed = text.trim();
    if (!trimmed) return;
    const state = await this.getState();
    const segments = [...state.segments, { text: trimmed, at: Date.now(), isFinal }];
    const transcriptText = isFinal
      ? (state.transcriptText ? state.transcriptText + " " : "") + trimmed
      : state.transcriptText;
    const turnCount = isFinal ? state.turnCount + 1 : state.turnCount;
    await this.setState({ ...state, segments, transcriptText, turnCount });
  }

  /** On hangup: kick off the finalize pipeline (summarize → store → notify → done). */
  async onHangup(): Promise<void> {
    const state = await this.getState();
    if (state.phase === "done" || state.phase === "summarizing" || state.phase === "sending") {
      return;
    }
    await this.setState({ ...state, phase: "summarizing", endedAt: Date.now() });
    await this.queue("summarize");
  }

  /** Pipeline stage 1: summarize the transcript via LLM (zero-credential binding). */
  async summarize(): Promise<void> {
    const state = await this.getState();
    try {
      const transcript = state.transcriptText.trim();
      if (!transcript) {
        await this.setState({ ...state, phase: "sending", summary: "" });
        await this.queue("store");
        return;
      }

      const model = this.env.AI_MODEL || DEFAULT_MODEL;
      const completion = await this.env.TELNYX.ai.openai.chat.createCompletion({
        model,
        messages: [
          { role: "system", content: SUMMARY_SYSTEM_PROMPT },
          { role: "user", content: transcript },
        ],
        max_tokens: 200,
        temperature: 0.3,
      });
      const summary = completion.choices[0]?.message?.content?.trim() || "";
      await this.setState({ ...state, summary, phase: "sending" });
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      const current = await this.getState();
      await this.setState({ ...current, phase: "error", error: `summarize: ${msg}` });
    }
    await this.queue("store");
  }

  /** Pipeline stage 2: persist the transcript + summary to per-call SQL + registry actor. */
  async store(): Promise<void> {
    const state = await this.getState();
    try {
      this.ctx.storage.sql.exec(
        `UPDATE transcript
         SET transcript = ?,
             summary    = ?,
             ended_at   = ?,
             turn_count = ?,
             status     = ?
         WHERE call_control_id = ?`,
        state.transcriptText,
        state.summary || "",
        state.endedAt || Date.now(),
        state.turnCount,
        state.phase === "error" ? "error" : "stored",
        state.callControlId,
      );
      // Push to the shared registry actor so /transcripts can list across calls.
      const record: TranscriptRecord = {
        call_control_id: state.callControlId,
        from_number: state.from,
        to_number: state.to,
        transcript: state.transcriptText,
        summary: state.summary || "",
        started_at: state.startedAt,
        ended_at: state.endedAt,
        turn_count: state.turnCount,
        status: state.phase === "error" ? "error" : "stored",
      };
      try {
        await this.env.REGISTRY.idFromName("global").record(record);
      } catch {
        // best-effort — per-call SQL is the source of truth for this call
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      const current = await this.getState();
      await this.setState({ ...current, phase: "error", error: `store: ${msg}` });
    }
    // If summarization already errored, skip SMS send
    if (state.phase === "error") {
      const current = await this.getState();
      await this.setState({ ...current, phase: "done" });
      return;
    }
    await this.queue("notify");
  }

  /** Pipeline stage 3: text the summary via SMS (zero-credential binding). */
  async notify(): Promise<void> {
    const state = await this.getState();
    try {
      if (state.summary && this.env.SMS_TO && this.env.SMS_FROM) {
        await this.env.TELNYX.messages.send({
          from: this.env.SMS_FROM,
          to: this.env.SMS_TO,
          text: state.summary,
        });
      }
      await this.setState({ ...state, phase: "done" });
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      await this.setState({ ...state, phase: "error", error: `notify: ${msg}` });
    }
  }

  /** Debug helper — return current state for inspection. */
  async getDebugState(): Promise<TranscribeState> {
    return await this.getState();
  }

  /** Return the persisted per-call transcript row (SQL). */
  async getStoredTranscript(): Promise<unknown> {
    this.ensureTables();
    const state = await this.getState();
    if (!state.callControlId) return null;
    const cursor = this.ctx.storage.sql.exec<{
      call_control_id: string;
      from_number: string;
      to_number: string;
      transcript: string;
      summary: string;
      started_at: number;
      ended_at: number;
      turn_count: number;
      status: string;
    }>("SELECT * FROM transcript WHERE call_control_id = ?", state.callControlId);
    return cursor.toArray()[0] || null;
  }

  private ensureTables(): void {
    this.ctx.storage.sql.exec(
      `CREATE TABLE IF NOT EXISTS transcript(
         call_control_id TEXT PRIMARY KEY,
         from_number     TEXT NOT NULL,
         to_number       TEXT NOT NULL,
         transcript      TEXT NOT NULL DEFAULT '',
         summary         TEXT NOT NULL DEFAULT '',
         started_at      INTEGER NOT NULL,
         ended_at        INTEGER,
         turn_count     INTEGER NOT NULL DEFAULT 0,
         status         TEXT NOT NULL DEFAULT 'transcribing'
       )`,
    );
  }
}

/**
 * TranscriptRegistry — a single shared actor instance (keyed "global") that
 * stores a record for every call's final transcript + summary so /transcripts
 * can list across calls.
 */
export class TranscriptRegistry extends Agent<Record<string, unknown>, Record<string, unknown>> {
  protected override initialState(): Record<string, unknown> {
    return {};
  }

  async record(row: TranscriptRecord): Promise<void> {
    this.ensureTables();
    this.ctx.storage.sql.exec(
      `INSERT OR REPLACE INTO transcripts
       (call_control_id, from_number, to_number, transcript, summary, started_at, ended_at, turn_count, status)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
      row.call_control_id,
      row.from_number,
      row.to_number,
      row.transcript,
      row.summary,
      row.started_at,
      row.ended_at,
      row.turn_count,
      row.status,
    );
  }

  async list(limit = 50): Promise<TranscriptRecord[]> {
    this.ensureTables();
    const cursor = this.ctx.storage.sql.exec<TranscriptRecord>(
      "SELECT * FROM transcripts ORDER BY started_at DESC LIMIT ?",
      Math.max(1, Math.min(200, limit)),
    );
    return cursor.toArray();
  }

  async get(callControlId: string): Promise<TranscriptRecord | null> {
    this.ensureTables();
    const cursor = this.ctx.storage.sql.exec<TranscriptRecord>(
      "SELECT * FROM transcripts WHERE call_control_id = ?",
      callControlId,
    );
    return cursor.toArray()[0] || null;
  }

  private ensureTables(): void {
    this.ctx.storage.sql.exec(
      `CREATE TABLE IF NOT EXISTS transcripts(
         call_control_id TEXT PRIMARY KEY,
         from_number     TEXT NOT NULL,
         to_number       TEXT NOT NULL,
         transcript      TEXT NOT NULL,
         summary         TEXT NOT NULL,
         started_at      INTEGER NOT NULL,
         ended_at        INTEGER,
         turn_count     INTEGER NOT NULL,
         status         TEXT NOT NULL
       )`,
    );
    this.ctx.storage.sql.exec(
      "CREATE INDEX IF NOT EXISTS idx_transcripts_started_at ON transcripts(started_at DESC)",
    );
  }
}
