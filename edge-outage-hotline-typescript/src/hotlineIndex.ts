import { StatefulActor } from "@telnyx/edge-runtime";

// ─────────────────────────────────────────────────────────────────────────
// HotlineIndex — one shared actor ("global") that every RegionAgent
// registers itself into on its first report.
//
// WHY this exists: per-actor SQL and KV are private by design, so the HTTP
// layer cannot enumerate "which regions have data" by querying actors —
// there is no cross-actor listing. The index is the only shared surface:
// a KV-backed set of region IDs. This is the same pattern used by
// edge-call-transcription-agent's TranscriptRegistry.
// ─────────────────────────────────────────────────────────────────────────

export class HotlineIndex extends StatefulActor {
  async register(region: string): Promise<void> {
    const regions = (await this.ctx.storage.get<string[]>("regions")) ?? [];
    if (!regions.includes(region)) {
      regions.push(region);
      await this.ctx.storage.put("regions", regions);
    }
  }

  async list(): Promise<string[]> {
    return (await this.ctx.storage.get<string[]>("regions")) ?? [];
  }
}
