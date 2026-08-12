export { ReminderAgent } from "./reminderAgent";
import type { ReminderAgent } from "./reminderAgent";

import {
  type ActorNamespace,
  type ActorStub,
  type IdFromNameOptions,
} from "@telnyx/edge-runtime";

type ReminderAgentStub = ActorStub &
  Pick<
    ReminderAgent,
    | "scheduleReminder"
    | "sendReminder"
    | "receiveReply"
    | "replyTimeout"
    | "cancelReminder"
    | "getDebugState"
  >;

interface ReminderAgentNamespace extends ActorNamespace {
  idFromName(name: string, options?: IdFromNameOptions): ReminderAgentStub;
}

interface Env {
  REMINDER: ReminderAgentNamespace;
}

function actorName(e164: string): string {
  return e164.replace(/[^0-9a-zA-Z.-]/g, "");
}

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url);

    if (url.pathname === "/health/liveness") return new Response("ok");
    if (url.pathname === "/health/readiness") return new Response("ok");

    // ── POST /remind — schedule a new reminder ──────────────────────
    if (url.pathname === "/remind" && req.method === "POST") {
      const body = (await req.json().catch(() => ({}))) as {
        to?: string;
        message?: string;
        delay_minutes?: number;
        from?: string;
      };

      const to = body.to?.trim();
      const message = body.message?.trim();
      const delayMinutes = body.delay_minutes ?? 5;
      const from = body.from?.trim() || "+16282564655";

      if (!to) return Response.json({ error: "to is required" }, { status: 400 });
      if (!message) return Response.json({ error: "message is required" }, { status: 400 });
      if (delayMinutes < 0) return Response.json({ error: "delay_minutes must be >= 0" }, { status: 400 });

      const stub = env.REMINDER.idFromName(actorName(to));
      const id = await stub.scheduleReminder(message, delayMinutes * 60, from, to);
      return Response.json({ id, to, message, delay_minutes: delayMinutes }, { status: 201 });
    }

    // ── POST /webhooks/sms — inbound SMS reply ──────────────────────
    if (req.method === "POST" && (url.pathname === "/webhooks/sms" || url.pathname === "/")) {
      try {
        const body = (await req.json().catch(() => ({}))) as any;
        const evt = body?.data;
        if (!evt || evt.event_type !== "message.received") {
          return Response.json({ error: "unexpected event_type" }, { status: 400 });
        }
        const payload = evt.payload || {};
        const from = (payload.from?.phone_number || payload.from) as string;
        const to = (payload.to?.[0]?.phone_number || payload.to?.[0] || payload.to) as string;
        const text = (payload.text || "") as string;

        if (!from || !text.trim()) {
          return Response.json({ error: "missing from or text" }, { status: 400 });
        }

        const stub = env.REMINDER.idFromName(actorName(String(from)));
        const result = await stub.receiveReply(String(text));
        return Response.json({ action: result.action, from, text });
      } catch (e: any) {
        return Response.json({ error: e?.message || "bad request" }, { status: 400 });
      }
    }

    // ── POST /debug/remind — simulate a reminder without real SMS ──
    if (url.pathname === "/debug/remind" && req.method === "POST") {
      const body = (await req.json().catch(() => ({}))) as {
        to?: string;
        message?: string;
        delay_minutes?: number;
        from?: string;
      };

      const to = body.to?.trim() || "+17177247292";
      const message = body.message?.trim() || "Test reminder";
      const delayMinutes = body.delay_minutes ?? 0.1; // 6 seconds for testing
      const from = body.from?.trim() || "+16282564655";

      const stub = env.REMINDER.idFromName(actorName(to));
      const id = await stub.scheduleReminder(message, delayMinutes * 60, from, to);
      return Response.json({ id, to, message, delay_minutes: delayMinutes, note: "debug — no real SMS" }, { status: 201 });
    }

    // ── POST /debug/reply — simulate an inbound SMS reply ──────────
    if (url.pathname === "/debug/reply" && req.method === "POST") {
      const body = (await req.json().catch(() => ({}))) as { from?: string; text?: string };
      const from = body.from?.trim() || "+17177247292";
      const text = body.text?.trim() || "snooze";

      const stub = env.REMINDER.idFromName(actorName(from));
      const result = await stub.receiveReply(text);
      return Response.json({ action: result.action, snoozed: result.snoozed, from, text });
    }

    // ── POST /debug/send — manually trigger sendReminder ───────────
    if (url.pathname === "/debug/send" && req.method === "POST") {
      const body = (await req.json().catch(() => ({}))) as { to?: string; id?: string };
      const to = body.to?.trim() || "+17177247292";
      const id = body.id;

      if (!id) return Response.json({ error: "id is required" }, { status: 400 });

      const stub = env.REMINDER.idFromName(actorName(to));
      await stub.sendReminder({ id });
      return Response.json({ action: "sent", id });
    }

    // ── GET /debug/state — inspect actor state ─────────────────────
    if (url.pathname === "/debug/state" && req.method === "GET") {
      const from = url.searchParams.get("from") || "+17177247292";
      const stub = env.REMINDER.idFromName(actorName(from));
      try {
        const state = await stub.getDebugState();
        return Response.json(state);
      } catch (e: any) {
        return Response.json({ error: e?.message || "failed to get state" }, { status: 500 });
      }
    }

    // ── POST /cancel — cancel a reminder ───────────────────────────
    if (url.pathname === "/cancel" && req.method === "POST") {
      const body = (await req.json().catch(() => ({}))) as { to?: string; id?: string };
      const to = body.to?.trim();
      const id = body.id?.trim();

      if (!to || !id) return Response.json({ error: "to and id are required" }, { status: 400 });

      const stub = env.REMINDER.idFromName(actorName(to));
      const cancelled = await stub.cancelReminder(id);
      return Response.json({ cancelled, id });
    }

    return new Response("not found", { status: 404 });
  },
};
