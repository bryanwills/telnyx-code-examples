import { describe, it, expect, vi, beforeEach } from "vitest";
import { HumanMessage } from "@langchain/core/messages";

// Mock the TelnyxBoundChatModel so graph tests focus on routing, not LLM
vi.mock("../src/telnyx-bound-chat-model.js", () => {
  return {
    TelnyxBoundChatModel: vi.fn().mockImplementation((opts: { env: unknown; model: string }) => ({
      invoke: vi.fn(async (messages: Array<{ _getType: () => string; content: unknown }>) => {
        const systemMsg = messages.find((m) => m._getType() === "system");
        const systemContent = typeof systemMsg?.content === "string" ? systemMsg.content : "";
        if (systemContent.toLowerCase().includes("classify")) {
          return { content: "order" };
        }
        return { content: "Your order ORD-10042 is shipped, arriving Friday." };
      }),
      _llmType: () => "telnyx-bound-mock",
    })),
  };
});

import { buildGraph } from "../src/graph.js";
import type { Env } from "../src/types.js";

function makeMockEnv(): Env {
  return {
    TELNYX: {
      ai: {
        openai: {
          chat: {
            createCompletion: vi.fn(),
          },
        },
      },
    },
  } as unknown as Env;
}

describe("LangGraph StateGraph routing", () => {
  it("routes 'order' intent through the action node", async () => {
    const env = makeMockEnv();
    const graph = buildGraph(env, "zai-org/GLM-5.2");

    const result = await graph.invoke({
      messages: [new HumanMessage("where is my order ORD-10042?")],
    });

    expect(result.intentLabel).toBe("order");
    expect(result.actionResult).toContain("ORD-10042");
    expect(result.actionResult).toContain("shipped");
    expect(result.replyText).toBeTruthy();
  });

  it("routes 'smalltalk' intent directly to response (skips action)", async () => {
    const env = makeMockEnv();
    const graph = buildGraph(env, "zai-org/GLM-5.2");

    // Override the mock to classify as smalltalk
    const { TelnyxBoundChatModel } = await import("../src/telnyx-bound-chat-model.js");
    vi.mocked(TelnyxBoundChatModel).mockImplementationOnce(() => ({
      invoke: vi.fn(async (messages: Array<{ _getType: () => string; content: unknown }>) => {
        const systemMsg = messages.find((m) => m._getType() === "system");
        const systemContent = typeof systemMsg?.content === "string" ? systemMsg.content : "";
        if (systemContent.toLowerCase().includes("classify")) {
          return { content: "smalltalk" };
        }
        return { content: "Hi there! How can I help with your order?" };
      }),
      _llmType: () => "telnyx-bound-mock",
    }) as never);

    const graph2 = buildGraph(env, "zai-org/GLM-5.2");
    const result = await graph2.invoke({
      messages: [new HumanMessage("hi there")],
    });

    expect(result.intentLabel).toBe("smalltalk");
    expect(result.actionResult).toBeUndefined();
    expect(result.replyText).toBeTruthy();
  });

  it("action node extracts order ID from the user message", async () => {
    const env = makeMockEnv();
    const graph = buildGraph(env, "zai-org/GLM-5.2");

    const result = await graph.invoke({
      messages: [new HumanMessage("what is the status of ORD-10043?")],
    });

    expect(result.intentLabel).toBe("order");
    expect(result.actionResult).toContain("ORD-10043");
    expect(result.actionResult).toContain("processing");
  });

  it("action node returns 'not_found' for unknown order IDs", async () => {
    const env = makeMockEnv();
    const graph = buildGraph(env, "zai-org/GLM-5.2");

    const result = await graph.invoke({
      messages: [new HumanMessage("where is order ORD-99999?")],
    });

    expect(result.intentLabel).toBe("order");
    expect(result.actionResult).toContain("not_found");
  });
});
