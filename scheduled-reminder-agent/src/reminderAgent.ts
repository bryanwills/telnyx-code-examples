import { Agent } from "@telnyx/edge-runtime";

export type ReminderStatus = "scheduled" | "sent" | "snoozed" | "done" | "cancelled";

export interface Reminder {
  id: string;
  message: string;
  remindAt: number;
  status: ReminderStatus;
  sentAt?: number;
  snoozeCount: number;
}

export interface ReminderState extends Record<string, unknown> {
  phoneNumber: string;
  fromNumber: string;
  reminders: Reminder[];
  currentReminderId: string | null;
  awaitingReply: boolean;
  totalSnoozes: number;
  totalReminders: number;
  adaptiveBaseSeconds: number;
}

interface ReminderEnv {
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
const MAX_SNOOZES = 5;
const REPLY_WINDOW_SECONDS = 3600; // wait 1 hour for a reply before giving up

const SNOOZE_SYSTEM_PROMPT = `You are a snooze intent detector. Analyze the user's SMS reply to a reminder. Classify it as either "snooze" or "acknowledge".

- "snooze": the user wants to delay or postpone the reminder (e.g. "later", "snooze", "not now", "in an hour", "remind me later", "busy", "can't right now")
- "acknowledge": the user has seen the reminder and is not asking to delay (e.g. "thanks", "got it", "ok", "done", "will do", "on it")

Return JSON only: {"intent": "snooze"|"acknowledge", "delay_minutes": <number or null>}

If intent is "snooze" and the user specified a time (e.g. "in 2 hours"), set delay_minutes to that value. Otherwise set delay_minutes to null (the system will use adaptive timing).`;

/**
 * ReminderAgent — one actor instance per phone number.
 *
 * Lifecycle:
 *   1. scheduleReminder(message, delaySeconds) — creates a reminder, schedules sendReminder()
 *   2. sendReminder() — sends SMS via this.env.TELNYX.messages.send(), awaits reply
 *   3. receiveReply(text) — LLM detects snooze vs acknowledge
 *      - snooze → reschedule with adaptive delay → back to step 2
 *      - acknowledge → mark done
 *   4. Adaptive timing — each snooze increases the delay exponentially
 */
export class ReminderAgent extends Agent<ReminderEnv, ReminderState> {
  protected override initialState(): ReminderState {
    return {
      phoneNumber: "",
      fromNumber: "",
      reminders: [],
      currentReminderId: null,
      awaitingReply: false,
      totalSnoozes: 0,
      totalReminders: 0,
      adaptiveBaseSeconds: 1800, // 30 min base
    };
  }

  /**
   * Schedule a new reminder. Creates a reminder entry and uses this.schedule()
   * to fire sendReminder() after the specified delay.
   */
  async scheduleReminder(
    message: string,
    delaySeconds: number,
    fromNumber: string,
    phoneNumber: string,
  ): Promise<string> {
    const state = await this.getState();
    const id = `reminder-${Date.now()}`;
    const remindAt = Date.now() + delaySeconds * 1000;

    const reminder: Reminder = {
      id,
      message,
      remindAt,
      status: "scheduled",
      snoozeCount: 0,
    };

    await this.setState({
      ...state,
      phoneNumber,
      fromNumber,
      reminders: [...state.reminders, reminder],
      totalReminders: state.totalReminders + 1,
      currentReminderId: id,
    });

    await this.schedule(delaySeconds, "sendReminder", { id }, { id: `send-${id}` });

    return id;
  }

  /**
   * Send the reminder SMS. Called by the scheduler.
   * Uses this.env.TELNYX.messages.send() — zero-credential.
   */
  async sendReminder(data: { id: string }): Promise<void> {
    const state = await this.getState();
    const reminder = state.reminders.find((r) => r.id === data.id);
    if (!reminder || reminder.status === "cancelled" || reminder.status === "done") return;

    const smsText = `Reminder: ${reminder.message}\n\nReply "snooze" to delay, or any other message to acknowledge.`;

    try {
      await this.env.TELNYX.messages.send({
        from: state.fromNumber,
        to: state.phoneNumber,
        text: smsText,
      });

      reminder.status = "sent";
      reminder.sentAt = Date.now();
      await this.setState({
        ...state,
        currentReminderId: data.id,
        awaitingReply: true,
        reminders: state.reminders.map((r) => (r.id === data.id ? reminder : r)),
      });

      // Schedule a reply-window timeout — if no reply in 1 hour, mark done
      await this.schedule(
        REPLY_WINDOW_SECONDS,
        "replyTimeout",
        { id: data.id },
        { id: `timeout-${data.id}` },
      );
    } catch (e) {
      reminder.status = "done";
      await this.setState({
        ...state,
        reminders: state.reminders.map((r) => (r.id === data.id ? reminder : r)),
      });
    }
  }

  /**
   * Handle an inbound SMS reply. Uses LLM to detect snooze intent.
   * If snooze: reschedule with adaptive delay.
   * If acknowledge: mark reminder as done.
   */
  async receiveReply(text: string): Promise<{ action: string; snoozed: boolean }> {
    const state = await this.getState();
    if (!state.awaitingReply || !state.currentReminderId) {
      return { action: "no_active_reminder", snoozed: false };
    }

    const reminder = state.reminders.find((r) => r.id === state.currentReminderId);
    if (!reminder) {
      return { action: "reminder_not_found", snoozed: false };
    }

    // Detect snooze intent via LLM
    let intent = "acknowledge";
    let delayMinutes: number | null = null;

    try {
      const completion = await this.env.TELNYX.ai.openai.chat.createCompletion({
        model: this.env.AI_MODEL || DEFAULT_MODEL,
        messages: [
          { role: "system", content: SNOOZE_SYSTEM_PROMPT },
          { role: "user", content: `User reply: "${text}"` },
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
      intent = parsed.intent || "acknowledge";
      delayMinutes = parsed.delay_minutes ?? null;
    } catch {
      // If LLM fails, default to acknowledge
      intent = "acknowledge";
    }

    if (intent === "snooze" && reminder.snoozeCount < MAX_SNOOZES) {
      // Adaptive delay: exponential backoff from base, or user-specified delay
      let delaySeconds: number;
      if (delayMinutes && delayMinutes > 0) {
        delaySeconds = delayMinutes * 60;
      } else {
        // Exponential backoff: base * 2^snoozeCount
        delaySeconds = state.adaptiveBaseSeconds * Math.pow(2, reminder.snoozeCount);
      }

      reminder.snoozeCount += 1;
      reminder.status = "snoozed";
      reminder.remindAt = Date.now() + delaySeconds * 1000;

      await this.setState({
        ...state,
        reminders: state.reminders.map((r) => (r.id === reminder.id ? reminder : r)),
        awaitingReply: false,
        totalSnoozes: state.totalSnoozes + 1,
      });

      // Schedule the next reminder
      await this.schedule(delaySeconds, "sendReminder", { id: reminder.id }, { id: `snooze-${reminder.id}-${reminder.snoozeCount}` });

      return { action: "snoozed", snoozed: true };
    }

    // Acknowledge or max snoozes reached — mark done
    reminder.status = "done";
    await this.setState({
      ...state,
      reminders: state.reminders.map((r) => (r.id === reminder.id ? reminder : r)),
      awaitingReply: false,
      currentReminderId: null,
    });

    return { action: "acknowledged", snoozed: false };
  }

  /**
   * Reply window timeout — if no reply received, mark reminder as done.
   */
  async replyTimeout(data: { id: string }): Promise<void> {
    const state = await this.getState();
    if (state.currentReminderId !== data.id || !state.awaitingReply) return;

    const reminder = state.reminders.find((r) => r.id === data.id);
    if (!reminder || reminder.status === "done") return;

    reminder.status = "done";
    await this.setState({
      ...state,
      reminders: state.reminders.map((r) => (r.id === data.id ? reminder : r)),
      awaitingReply: false,
      currentReminderId: null,
    });
  }

  /**
   * Cancel a pending reminder.
   */
  async cancelReminder(id: string): Promise<boolean> {
    const state = await this.getState();
    const reminder = state.reminders.find((r) => r.id === id);
    if (!reminder) return false;

    reminder.status = "cancelled";
    await this.setState({
      ...state,
      reminders: state.reminders.map((r) => (r.id === id ? reminder : r)),
      currentReminderId: state.currentReminderId === id ? null : state.currentReminderId,
      awaitingReply: state.currentReminderId === id ? false : state.awaitingReply,
    });
    return true;
  }

  /**
   * Get debug state for inspection.
   */
  async getDebugState(): Promise<ReminderState> {
    return await this.getState();
  }
}
