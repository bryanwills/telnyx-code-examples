import { describe, it, expect, vi, beforeEach } from "vitest";

// vi.hoisted ensures these are available when vi.mock factories run (vitest hoists vi.mock calls)
const { mockState, mockMessages, mockCalls, mockFns, insertedEventIds } = vi.hoisted(() => {
  const insertedEventIds = new Set<string>();
  return {
    mockState: {} as Record<string, unknown>,
    mockMessages: [] as Array<{ role: string; content: string }>,
    mockCalls: {} as Record<string, unknown[]>,
    insertedEventIds,
    mockFns: {
      getState: vi.fn(() => Promise.resolve({ ...mockState })),
      setState: vi.fn((patch: Record<string, unknown>) => {
        Object.assign(mockState, patch);
        return Promise.resolve({ ...mockState });
      }),
      queue: vi.fn((_method: string) => Promise.resolve("queued")),
      schedule: vi.fn((_delay: number, _method: string) => Promise.resolve("scheduled")),
      messagesAdd: vi.fn(async (role: string, content: string) => {
        mockMessages.push({ role, content });
      }),
      toLangChain: vi.fn(async () =>
        mockMessages.map((m) => ({ role: m.role, content: m.content })),
      ),
      messagesLast: vi.fn(async () => mockMessages[mockMessages.length - 1] ?? null),
      sqlExec: vi.fn((query?: string, ...params: unknown[]) => {
        if (query && query.startsWith("INSERT INTO webhook_events")) {
          const eventId = params[0] as string;
          if (insertedEventIds.has(eventId)) {
            throw new Error("UNIQUE constraint failed: webhook_events.event_id");
          }
          insertedEventIds.add(eventId);
        }
        return { toArray: () => [] };
      }),
    },
  };
});

vi.mock("@telnyx/edge-runtime", () => {
  class MockAgent {
    env: Record<string, unknown>;
    ctx: { storage: { sql: { exec: typeof mockFns.sqlExec } } };

    constructor(_ctx: unknown, env: Record<string, unknown>) {
      this.env = env;
      this.ctx = { storage: { sql: { exec: mockFns.sqlExec } } };
    }

    protected getState() {
      return mockFns.getState();
    }
    protected setState(patch: Record<string, unknown>) {
      return mockFns.setState(patch);
    }
    protected queue(method: string) {
      (mockCalls.queue ??= []).push(method);
      return mockFns.queue(method);
    }
    protected schedule(delay: number, method: string) {
      (mockCalls.schedule ??= []).push({ delay, method });
      return mockFns.schedule(delay, method);
    }
    protected messages = {
      add: mockFns.messagesAdd,
      toLangChain: mockFns.toLangChain,
      last: mockFns.messagesLast,
      all: vi.fn(async () => [...mockMessages]),
    };
  }
  return { Agent: MockAgent, StatefulActor: MockAgent };
});

const mockGraphOutput = vi.hoisted(() => ({
  replyText: "Your order is shipped.",
  intentLabel: "order",
}));

vi.mock("../src/graph.js", () => ({
  buildGraph: vi.fn(() => ({
    invoke: vi.fn(async () => ({ replyText: mockGraphOutput.replyText, intentLabel: mockGraphOutput.intentLabel })),
  })),
}));

const { Conversation } = await import("../src/conversation.js");
import type { Env } from "../src/types.js";

function resetMocks() {
  for (const k of Object.keys(mockState)) delete mockState[k];
  mockState.from = "";
  mockState.to = "";
  mockState.turn = 0;
  mockState.queuedTurn = 0;
  mockState.processingTurn = 0;
  mockState.lastSentTurn = 0;
  mockState.pendingOutbound = null;
  mockState.lastIntent = "unknown";
  mockState.at = 0;
  mockMessages.length = 0;
  for (const k of Object.keys(mockCalls)) delete mockCalls[k];
  insertedEventIds.clear();
  mockGraphOutput.replyText = "Your order is shipped.";
  mockGraphOutput.intentLabel = "order";
  mockFns.getState.mockClear();
  mockFns.setState.mockClear();
  mockFns.queue.mockClear();
  mockFns.schedule.mockClear();
  mockFns.messagesAdd.mockClear();
  mockFns.toLangChain.mockClear();
  mockFns.messagesLast.mockClear();
  mockFns.sqlExec.mockClear();
}

function makeEnv(overrides: Partial<Env> = {}): Env {
  return { SMS_TRANSPORT: "demo", MODEL: "zai-org/GLM-5.2", ...overrides } as Env;
}

function makeConversation(env?: Env): InstanceType<typeof Conversation> {
  resetMocks();
  return new Conversation({ id: "test" } as never, env ?? makeEnv()) as InstanceType<typeof Conversation>;
}

describe("Conversation turn state machine", () => {
  beforeEach(() => resetMocks());

  describe("receive()", () => {
    it("adds user message, bumps turn, sets queuedTurn, and queues process", async () => {
      const conv = makeConversation();
      await conv.receive({ text: "where is my order?", from: "+15550001111", to: "+15557654321", eventId: "evt-1" });

      expect(mockMessages).toContainEqual({ role: "user", content: "where is my order?" });
      expect(mockState.turn).toBe(1);
      expect(mockState.queuedTurn).toBe(1);
      expect(mockState.from).toBe("+15550001111");
      expect(mockState.to).toBe("+15557654321");
      expect(mockCalls.queue).toEqual(["process"]);
    });

    it("deduplicates by eventId — second receive with same eventId is a no-op", async () => {
      const conv = makeConversation();
      await conv.receive({ text: "first", from: "+15550001111", to: "+15557654321", eventId: "evt-dup" });
      await conv.receive({ text: "second", from: "+15550001111", to: "+15557654321", eventId: "evt-dup" });

      expect(mockMessages).toHaveLength(1);
      expect(mockMessages[0].content).toBe("first");
      expect(mockState.turn).toBe(1);
    });
  });

  describe("process() — stale-task no-op", () => {
    it("returns immediately when queuedTurn <= lastSentTurn", async () => {
      const conv = makeConversation();
      mockState.from = "+15550001111";
      mockState.to = "+15557654321";
      mockState.turn = 2;
      mockState.queuedTurn = 2;
      mockState.lastSentTurn = 2;

      await conv.process();

      expect(mockMessages.filter((m) => m.role === "assistant")).toHaveLength(0);
    });
  });

  describe("process() — happy path", () => {
    it("runs graph, adds assistant reply, sets lastSentTurn", async () => {
      const conv = makeConversation();
      mockState.from = "+15550001111";
      mockState.to = "+15557654321";
      mockState.turn = 1;
      mockState.queuedTurn = 1;
      mockState.lastSentTurn = 0;
      mockMessages.push({ role: "user", content: "where is my order ORD-10042?" });

      await conv.process();

      expect(mockMessages).toContainEqual({ role: "assistant", content: "Your order is shipped." });
      expect(mockState.pendingOutbound).toBeNull();
      expect(mockState.lastSentTurn).toBe(1);
      expect(mockState.lastIntent).toBe("order");
    });

    it("schedules a 24h nudge", async () => {
      const conv = makeConversation();
      mockState.from = "+15550001111";
      mockState.to = "+15557654321";
      mockState.turn = 1;
      mockState.queuedTurn = 1;
      mockState.lastSentTurn = 0;
      mockMessages.push({ role: "user", content: "hi" });

      await conv.process();

      expect(mockCalls.schedule).toContainEqual({ delay: 86400, method: "nudge" });
    });
  });

  describe("process() — coalescing", () => {
    it("two inbound before first process → one reply for the latest turn", async () => {
      const conv = makeConversation();
      await conv.receive({ text: "first", from: "+15550001111", to: "+15557654321", eventId: "evt-1" });
      await conv.receive({ text: "second", from: "+15550001111", to: "+15557654321", eventId: "evt-2" });

      expect(mockState.queuedTurn).toBe(2);
      expect(mockMessages).toHaveLength(2);

      await conv.process();

      expect(mockState.lastSentTurn).toBe(2);
      expect(mockMessages.filter((m) => m.role === "assistant")).toHaveLength(1);

      // stale second process → no duplicate
      await conv.process();
      expect(mockMessages.filter((m) => m.role === "assistant")).toHaveLength(1);
    });
  });

  describe("process() — re-queue", () => {
    it("does not re-queue when queuedTurn == targetTurn", async () => {
      const conv = makeConversation();
      mockState.from = "+15550001111";
      mockState.to = "+15557654321";
      mockState.turn = 1;
      mockState.queuedTurn = 1;
      mockState.lastSentTurn = 0;
      mockMessages.push({ role: "user", content: "hi" });

      mockCalls.queue = [];
      await conv.process();

      expect(mockCalls.queue).not.toContain("process");
    });

    it("re-queues process when a newer turn arrives during processing", async () => {
      const conv = makeConversation();
      mockState.from = "+15550001111";
      mockState.to = "+15557654321";
      mockState.turn = 3;
      mockState.queuedTurn = 3;
      mockState.lastSentTurn = 0;
      mockMessages.push({ role: "user", content: "msg" });

      // Override getState so the second read (s2) sees a bumped queuedTurn,
      // simulating a new receive() during process()
      let callCount = 0;
      const originalGetState = mockFns.getState;
      mockFns.getState = vi.fn(() => {
        callCount++;
        const result = { ...mockState };
        // On the 4th+ call (the s2 read after commit), simulate a new inbound
        if (callCount >= 3) {
          result.queuedTurn = (mockState.queuedTurn as number) + 1;
        }
        return Promise.resolve(result);
      });

      mockCalls.queue = [];
      await conv.process();

      expect(mockState.lastSentTurn).toBe(3);
      expect(mockCalls.queue).toContain("process");

      mockFns.getState = originalGetState;
    });
  });

  describe("nudge()", () => {
    it("skips when last message is assistant (customer didn't reply)", async () => {
      const conv = makeConversation();
      mockState.from = "+15550001111";
      mockState.to = "+15557654321";
      mockState.turn = 1;
      mockMessages.push({ role: "user", content: "hi" });
      mockMessages.push({ role: "assistant", content: "hello" });

      await conv.nudge();

      expect(mockMessages).toHaveLength(2);
    });

    it("completes without error when last message is user (customer waiting)", async () => {
      const conv = makeConversation();
      mockState.from = "+15550001111";
      mockState.to = "+15557654321";
      mockState.turn = 1;
      mockMessages.push({ role: "user", content: "where is my order?" });

      await conv.nudge();

      expect(true).toBe(true);
    });
  });
});
