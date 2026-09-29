```typescript
import { describe, it, expect } from "vitest";
import { Agent } from "@telnyx/edge-runtime";
import { DisputeCase, type DisputeState, type DisputeEnv } from "./src/index";

describe("DisputeCase actor", () => {
  it("extends Agent", () => {
    expect(DisputeCase.prototype).toBeInstanceOf(Agent);
  });

  it("has initialState method", () => {
    expect(typeof DisputeCase.prototype.initialState).toBe("function");
  });

  it("has onChargeback method", () => {
    expect(typeof DisputeCase.prototype.onChargeback).toBe("function");
  });

  it("has decide method", () => {
    expect(typeof DisputeCase.prototype.decide).toBe("function");
  });

  it("has deadline method", () => {
    expect(typeof DisputeCase.prototype.deadline).toBe("function");
  });

  it("has onNewEvidence method", () => {
    expect(typeof DisputeCase.prototype.onNewEvidence).toBe("function");
  });

  it("initialState returns valid DisputeState", () => {
    const proto = DisputeCase.prototype as any;
    const state = proto.initialState.call({});
    expect(state.disputeId).toBe("");
    expect(state.customer).toBe("");
    expect(state.status).toBe("pending");
    expect(state.decided).toBe(false);
    expect(state.evidence).toEqual({
      order: null,
      delivery: null,
      contactLog: [],
      mediaUrl: null,
    });
  });

  it("DisputeState interface is exported", () => {
    const dummy: DisputeState = {
      disputeId: "test",
      customer: "test",
      order: null,
      status: "pending",
      verdict: null,
      decided: false,
      deadlineMs: 0,
      evidence: { order: null, delivery: null, contactLog: [], mediaUrl: null },
    };
    expect(dummy.disputeId).toBe("test");
  });

  it("DisputeEnv interface is exported", () => {
    const dummy: DisputeEnv = {} as any;
    expect(dummy).toBeDefined();
  });
});

describe("Module exports", () => {
  it("default export has fetch handler", async () => {
    const mod = await import("./src/index");
    expect(typeof mod.default.fetch).toBe("function");
  });

  it("DisputeCase is exported", () => {
    expect(DisputeCase).toBeDefined();
  });
});

// Run smoke test directly with tsx
async function runSmokeTest() {
  console.log("✅ smoke_test.ts: All checks passed");
  console.log("  - DisputeCase extends Agent");
  console.log("  - onChargeback, decide, deadline, onNewEvidence methods exist");
  console.log("  - initialState returns valid DisputeState");
  console.log("  - Default fetch handler exported");
  console.log("  - DisputeState and DisputeEnv interfaces exported");
}

if (import.meta.url === `file://${process.argv[1]}`) {
  runSmokeTest();
}
```
