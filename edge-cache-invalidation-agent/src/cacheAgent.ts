import { Agent } from "@telnyx/edge-runtime";

// ── State ────────────────────────────────────────────────────────────────
export interface CacheAgentState extends Record<string, unknown> {
  contentId: string;          // what changed (URL, asset path, etc.)
  contentVersion: string;     // new version identifier
  locations: string[];         // edge locations to invalidate
  senderPhone: string;         // Telnyx number sending SMS
  alertPhone: string;          // ops phone to notify
  status: "pending" | "invalidating" | "updating_manifest" | "notifying" | "done" | "error";
  invalidatedLocations: string[];
  manifestUpdated: boolean;
  smsSent: boolean;
  error: string;
  createdAt: number;
  completedAt: number;
}

// ── Env: [telnyx] binding + KV + Cloud Storage ───────────────────────────
interface CacheAgentEnv {
  TELNYX: {
    messages: {
      send(m: { from: string; to: string; text: string }): Promise<unknown>;
    };
  };
  CACHE_KV: KvNamespace;
  CACHE_STORAGE: CloudStorageBucket;
  ALERT_PHONE: string;
  SENDER_PHONE: string;
}

const MANIFEST_KEY = "cache-manifest.json";

/**
 * CacheAgent — one actor instance per cache invalidation event.
 *
 * Pipeline (each stage queued for non-blocking execution):
 *   1. invalidate()  — mark cache dirty per edge location via KV
 *   2. updateManifest() — write updated manifest to Cloud Storage
 *   3. notify()      — send SMS to ops via this.env.TELNYX.messages.send()
 */
export class CacheAgent extends Agent<CacheAgentEnv, CacheAgentState> {
  protected override initialState(): CacheAgentState {
    return {
      contentId: "",
      contentVersion: "",
      locations: [],
      senderPhone: "",
      alertPhone: "",
      status: "pending",
      invalidatedLocations: [],
      manifestUpdated: false,
      smsSent: false,
      error: "",
      createdAt: 0,
      completedAt: 0,
    };
  }

  /** Entry point — called by the webhook handler after a content update arrives. */
  async start(params: {
    contentId: string;
    contentVersion: string;
    locations: string[];
  }): Promise<void> {
    await this.setState({
      contentId: params.contentId,
      contentVersion: params.contentVersion,
      locations: params.locations,
      senderPhone: this.env.SENDER_PHONE,
      alertPhone: this.env.ALERT_PHONE,
      status: "invalidating",
      createdAt: Date.now(),
    });
    await this.queue("invalidate");
  }

  /** Stage 1: Mark cache as dirty in each edge location via KV. */
  async invalidate(): Promise<void> {
    const state = await this.getState();
    try {
      const invalidated: string[] = [];

      for (const location of state.locations) {
        // Mark this location's cache as dirty
        const kvKey = `cache:${location}:${state.contentId}`;
        const value = JSON.stringify({
          dirty: true,
          contentVersion: state.contentVersion,
          invalidatedAt: Date.now(),
        });
        await this.env.CACHE_KV.put(kvKey, value, { expirationTtl: 3600 });
        invalidated.push(location);
      }

      await this.setState({
        invalidatedLocations: invalidated,
        status: "updating_manifest",
      });
      await this.queue("updateManifest");
    } catch (e: any) {
      await this.setState({
        status: "error",
        error: `invalidate: ${e?.message || String(e)}`,
        completedAt: Date.now(),
      });
    }
  }

  /** Stage 2: Update the shared cache manifest in Cloud Storage. */
  async updateManifest(): Promise<void> {
    const state = await this.getState();
    try {
      // Build the manifest entry for this content
      const manifestEntry = {
        contentId: state.contentId,
        contentVersion: state.contentVersion,
        invalidatedLocations: state.invalidatedLocations,
        updatedAt: Date.now(),
      };

      // Read the existing manifest (if any)
      let manifest: { entries: any[] } = { entries: [] };
      try {
        const existing = await this.env.CACHE_STORAGE.get(MANIFEST_KEY);
        if (existing) {
          const text = await existing.text();
          manifest = JSON.parse(text);
        }
      } catch {
        // No existing manifest — start fresh
      }

      // Append this invalidation to the manifest
      manifest.entries.push(manifestEntry);

      // Write the updated manifest back to Cloud Storage
      const manifestJson = JSON.stringify(manifest, null, 2);
      await this.env.CACHE_STORAGE.put(MANIFEST_KEY, manifestJson, {
        contentType: "application/json",
      });

      await this.setState({
        manifestUpdated: true,
        status: "notifying",
      });
      await this.queue("notify");
    } catch (e: any) {
      await this.setState({
        status: "error",
        error: `updateManifest: ${e?.message || String(e)}`,
        completedAt: Date.now(),
      });
    }
  }

  /** Stage 3: Send SMS notification to ops team (zero-credential binding). */
  async notify(): Promise<void> {
    const state = await this.getState();
    try {
      const locationCount = state.invalidatedLocations.length;
      const smsText = `Cache invalidated: ${state.contentId} v${state.contentVersion} — ${locationCount} location(s) updated. Manifest synced.`;

      await this.env.TELNYX.messages.send({
        from: state.senderPhone,
        to: state.alertPhone,
        text: smsText,
      });

      await this.setState({
        smsSent: true,
        status: "done",
        completedAt: Date.now(),
      });
    } catch (e: any) {
      await this.setState({
        status: "error",
        error: `notify: ${e?.message || String(e)}`,
        completedAt: Date.now(),
      });
    }
  }

  /** Debug helper — return current state for inspection. */
  async getStatus(): Promise<CacheAgentState> {
    return await this.getState();
  }

  /** Check if a location's cache is dirty for a given content ID. */
  async checkCacheStatus(location: string, contentId: string): Promise<{ dirty: boolean; contentVersion?: string }> {
    const kvKey = `cache:${location}:${contentId}`;
    const value = await this.env.CACHE_KV.get(kvKey, { type: "json" });
    if (!value) {
      return { dirty: false };
    }
    return value as { dirty: boolean; contentVersion?: string };
  }

  /** Clear the dirty flag for a location (simulates cache refresh). */
  async clearCacheFlag(location: string, contentId: string): Promise<void> {
    const kvKey = `cache:${location}:${contentId}`;
    await this.env.CACHE_KV.delete(kvKey);
  }
}
