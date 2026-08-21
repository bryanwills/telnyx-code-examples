import { Agent } from "@telnyx/edge-runtime";

// ── State ────────────────────────────────────────────────────────────────
export interface RateLimitAgentState extends Record<string, unknown> {
  key: string;
  status: "checking" | "allowed" | "rejected" | "alerting" | "done" | "error";
  currentCount: number;
  limit: number;
  windowSeconds: number;
  alertThreshold: number;
  alertTriggered: boolean;
  rejectionCount: number;
  totalRequests: number;
  allowedRequests: number;
  rejectedRequests: number;
  startedAt: number;
  lastRequestAt: number;
  error: string;
}

// ── Env: [telnyx] binding + KV ────────────────────────────────────────────
interface RateLimitAgentEnv {
  TELNYX: {
    messages: {
      send(m: { from: string; to: string; text: string }): Promise<unknown>;
    };
  };
  RATE_KV: KvNamespace;
  ALERT_PHONE: string;
  SENDER_PHONE: string;
  RATE_LIMIT: string;
  WINDOW_SECONDS: string;
  ALERT_THRESHOLD: string;
}

const RATE_LIMIT_DEFAULT = 100;
const WINDOW_DEFAULT_SEC = 60;
const ALERT_THRESHOLD_DEFAULT = 10; // number of rejections before SMS alert

/**
 * RateLimitAgent — one actor instance per rate-limited key (phone, IP, tenant).
 *
 * Pipeline (each stage queued for non-blocking execution):
 *   1. checkLimit()    — KV get current window count → compare against limit
 *   2. allow()         — increment counter, update stats
 *   3. reject()        — increment rejection counter, check if alert threshold hit
 *   4. sendAlert()    — send SMS via zero-credential [telnyx] binding
 */
export class RateLimitAgent extends Agent<RateLimitAgentEnv, RateLimitAgentState> {
  protected override initialState(): RateLimitAgentState {
    return {
      key: "",
      status: "checking",
      currentCount: 0,
      limit: 0,
      windowSeconds: 0,
      alertThreshold: 0,
      alertTriggered: false,
      rejectionCount: 0,
      totalRequests: 0,
      allowedRequests: 0,
      rejectedRequests: 0,
      startedAt: 0,
      lastRequestAt: 0,
      error: "",
    };
  }

  /** Entry point — check a request against the rate limit. */
  async checkRequest(params: { key: string }): Promise<void> {
    const limit = parseInt(this.env.RATE_LIMIT, 10) || RATE_LIMIT_DEFAULT;
    const windowSeconds = parseInt(this.env.WINDOW_SECONDS, 10) || WINDOW_DEFAULT_SEC;
    const alertThreshold = parseInt(this.env.ALERT_THRESHOLD, 10) || ALERT_THRESHOLD_DEFAULT;

    await this.setState({
      key: params.key,
      limit,
      windowSeconds,
      alertThreshold,
      status: "checking",
      startedAt: Date.now(),
      lastRequestAt: Date.now(),
    });
    await this.queue("checkLimit");
  }

  /** Stage 1: Check the current window count in KV against the limit. */
  async checkLimit(): Promise<void> {
    const state = await this.getState();
    try {
      const windowStart = Math.floor(Date.now() / 1000 / state.windowSeconds) * state.windowSeconds;
      const kvKey = `rate:${state.key}:${windowStart}`;
      const currentStr = await this.env.RATE_KV.get(kvKey);
      const currentCount = currentStr ? parseInt(currentStr, 10) : 0;

      await this.setState({
        ...state,
        currentCount,
        totalRequests: state.totalRequests + 1,
        lastRequestAt: Date.now(),
      });

      if (currentCount < state.limit) {
        await this.queue("allow");
      } else {
        await this.queue("reject");
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      await this.setState({ ...state, status: "error", error: `checkLimit: ${msg}` });
    }
  }

  /** Stage 2a: Allow the request — increment the counter. */
  async allow(): Promise<void> {
    const state = await this.getState();
    try {
      const windowStart = Math.floor(Date.now() / 1000 / state.windowSeconds) * state.windowSeconds;
      const kvKey = `rate:${state.key}:${windowStart}`;
      const newCount = state.currentCount + 1;
      await this.env.RATE_KV.put(kvKey, String(newCount), {
        expirationTtl: state.windowSeconds,
      });

      await this.setState({
        ...state,
        currentCount: newCount,
        allowedRequests: state.allowedRequests + 1,
        status: "allowed",
      });
      await this.queue("finalize");
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      await this.setState({ ...state, status: "error", error: `allow: ${msg}` });
    }
  }

  /** Stage 2b: Reject the request — increment rejection counter, check alert. */
  async reject(): Promise<void> {
    const state = await this.getState();
    try {
      const newRejectionCount = state.rejectionCount + 1;

      await this.setState({
        ...state,
        rejectedRequests: state.rejectedRequests + 1,
        rejectionCount: newRejectionCount,
        status: newRejectionCount >= state.alertThreshold ? "alerting" : "rejected",
      });

      if (newRejectionCount >= state.alertThreshold && !state.alertTriggered) {
        await this.queue("sendAlert");
      } else {
        await this.queue("finalize");
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      await this.setState({ ...state, status: "error", error: `reject: ${msg}` });
    }
  }

  /** Stage 3: Send SMS alert on sustained threshold breach (zero-credential binding). */
  async sendAlert(): Promise<void> {
    const state = await this.getState();
    try {
      const smsText =
        `Rate limit alert: key "${state.key}" has been rejected ${state.rejectionCount} times. ` +
        `Limit is ${state.limit} requests per ${state.windowSeconds}s window. ` +
        `Total requests: ${state.totalRequests}. Allowed: ${state.allowedRequests}. Rejected: ${state.rejectedRequests}.`;

      await this.env.TELNYX.messages.send({
        from: this.env.SENDER_PHONE,
        to: this.env.ALERT_PHONE,
        text: smsText,
      });

      await this.setState({
        ...state,
        alertTriggered: true,
        status: "done",
      });
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      await this.setState({ ...state, status: "error", error: `sendAlert: ${msg}` });
    }
  }

  /** Finalize — mark as done. */
  async finalize(): Promise<void> {
    const state = await this.getState();
    await this.setState({ ...state, status: "done" });
  }

  /** Debug helper — return current agent state. */
  async getStatus(): Promise<RateLimitAgentState> {
    return await this.getState();
  }

  /** Get a summary for the HTTP API. */
  async getSummary(): Promise<{
    key: string;
    status: string;
    currentCount: number;
    limit: number;
    windowSeconds: number;
    totalRequests: number;
    allowedRequests: number;
    rejectedRequests: number;
    alertTriggered: boolean;
    lastRequestAt: number;
  }> {
    const state = await this.getState();
    return {
      key: state.key,
      status: state.status,
      currentCount: state.currentCount,
      limit: state.limit,
      windowSeconds: state.windowSeconds,
      totalRequests: state.totalRequests,
      allowedRequests: state.allowedRequests,
      rejectedRequests: state.rejectedRequests,
      alertTriggered: state.alertTriggered,
      lastRequestAt: state.lastRequestAt,
    };
  }

  /** Get the current window count for a key (for the stats endpoint). */
  async getWindowCount(key: string): Promise<{ key: string; count: number; windowStart: number; limit: number }> {
    const state = await this.getState();
    const windowStart = Math.floor(Date.now() / 1000 / state.windowSeconds) * state.windowSeconds;
    const kvKey = `rate:${key}:${windowStart}`;
    const countStr = await this.env.RATE_KV.get(kvKey);
    return {
      key,
      count: countStr ? parseInt(countStr, 10) : 0,
      windowStart,
      limit: state.limit,
    };
  }

  /** Reset the counter for a key (for the reset endpoint). */
  async resetKey(key: string): Promise<{ key: string; reset: boolean }> {
    const windowStart = Math.floor(Date.now() / 1000 / this.getWindowSeconds()) * this.getWindowSeconds();
    const kvKey = `rate:${key}:${windowStart}`;
    await this.env.RATE_KV.delete(kvKey);
    return { key, reset: true };
  }

  private getWindowSeconds(): number {
    return parseInt(this.env.WINDOW_SECONDS, 10) || WINDOW_DEFAULT_SEC;
  }
}

// ── Registry actor: aggregate stats across all keys ──────────────────────
export interface KeyStats {
  key: string;
  totalRequests: number;
  allowedRequests: number;
  rejectedRequests: number;
  alertTriggered: boolean;
  lastRequestAt: number;
}

export class RateLimitRegistry extends Agent<Record<string, unknown>, Record<string, unknown>> {
  protected override initialState(): Record<string, unknown> {
    return { keys: {} as Record<string, KeyStats> };
  }

  async record(stats: KeyStats): Promise<void> {
    const state = await this.getState();
    const keys = (state.keys as Record<string, KeyStats>) || {};
    keys[stats.key] = stats;
    await this.setState({ keys });
  }

  async listKeys(): Promise<KeyStats[]> {
    const state = await this.getState();
    const keys = (state.keys as Record<string, KeyStats>) || {};
    return Object.values(keys).sort((a, b) => b.lastRequestAt - a.lastRequestAt);
  }

  async getKey(key: string): Promise<KeyStats | null> {
    const state = await this.getState();
    const keys = (state.keys as Record<string, KeyStats>) || {};
    return keys[key] || null;
  }
}
