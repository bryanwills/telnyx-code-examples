import { StatefulActor } from "@telnyx/edge-runtime";

export interface Advisory {
  id: string;
  farmer_description: string;
  source: string;
  crop_type: string;
  issue_type: "disease" | "pest" | "nutrient" | "water" | "weather" | "unknown";
  severity: "low" | "medium" | "high" | "critical";
  confidence: number;
  recommendation: string;
  escalate: boolean;
  escalated_to?: string;
  generated_at: string;
}

export interface Stats {
  total_advisories: number;
  by_issue_type: Record<string, number>;
  by_severity: Record<string, number>;
  escalations: number;
  recent_crop_types: string[];
}

/**
 * CropAdvisory — one actor instance per advisory registry.
 *
 * Stores advisories per stored id and cumulative stats in durable storage.
 */
export class CropAdvisory extends StatefulActor {
  private async getAdvisories(): Promise<Record<string, Advisory>> {
    return (await this.ctx.storage.get<Record<string, Advisory>>("advisories")) ?? {};
  }

  private async saveAdvisories(advisories: Record<string, Advisory>): Promise<void> {
    await this.ctx.storage.put("advisories", advisories);
  }

  private async getStats(): Promise<Stats> {
    return (
      (await this.ctx.storage.get<Stats>("stats")) ?? {
        total_advisories: 0,
        by_issue_type: {},
        by_severity: {},
        escalations: 0,
        recent_crop_types: [],
      }
    );
  }

  private async saveStats(stats: Stats): Promise<void> {
    await this.ctx.storage.put("stats", stats);
  }

  /** Store a new advisory and update stats. */
  async addAdvisory(advisory: Advisory): Promise<void> {
    const advisories = await this.getAdvisories();
    advisories[advisory.id] = advisory;
    await this.saveAdvisories(advisories);

    const stats = await this.getStats();
    stats.total_advisories += 1;
    stats.by_issue_type[advisory.issue_type] = (stats.by_issue_type[advisory.issue_type] ?? 0) + 1;
    stats.by_severity[advisory.severity] = (stats.by_severity[advisory.severity] ?? 0) + 1;
    if (advisory.escalate) stats.escalations += 1;
    if (advisory.crop_type && !stats.recent_crop_types.includes(advisory.crop_type)) {
      stats.recent_crop_types = [advisory.crop_type, ...stats.recent_crop_types].slice(0, 20);
    }
    await this.saveStats(stats);
  }

  /** Get a specific advisory. */
  async getAdvisory(id: string): Promise<Advisory | undefined> {
    const advisories = await this.getAdvisories();
    return advisories[id];
  }

  /** List recent advisories. */
  async listAdvisories(limit = 20): Promise<Advisory[]> {
    const advisories = await this.getAdvisories();
    return Object.values(advisories)
      .sort((a, b) => (a.generated_at < b.generated_at ? 1 : -1))
      .slice(0, limit);
  }

  /** Get cumulative stats. */
  async getCropStats(): Promise<Stats> {
    return this.getStats();
  }
}
