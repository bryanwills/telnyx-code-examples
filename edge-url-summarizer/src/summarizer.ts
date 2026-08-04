import { StatefulActor } from "@telnyx/edge-runtime";

export interface CachedSummary {
  url: string;
  title?: string;
  bullets: string[];
  word_count: number;
  generated_at: string;
}

export interface Stats {
  total_requests: number;
  cache_hits: number;
  cache_misses: number;
  unique_urls: number;
  top_urls: string[];
}

/**
 * Summarizer — one actor instance per summarized URL collection.
 *
 * Stores:
 *  - summaries: map of URL → CachedSummary (persisted, survives restarts)
 *  - stats: hit/miss counters
 */
export class Summarizer extends StatefulActor {
  private async getMap(): Promise<Record<string, CachedSummary>> {
    return (await this.ctx.storage.get<Record<string, CachedSummary>>("summaries")) ?? {};
  }

  private async saveMap(map: Record<string, CachedSummary>): Promise<void> {
    await this.ctx.storage.put("summaries", map);
  }

  private async getStats(): Promise<Stats> {
    return (
      (await this.ctx.storage.get<Stats>("stats")) ?? {
        total_requests: 0,
        cache_hits: 0,
        cache_misses: 0,
        unique_urls: 0,
        top_urls: [],
      }
    );
  }

  private async saveStats(stats: Stats): Promise<void> {
    await this.ctx.storage.put("stats", stats);
  }

  /** Get a cached summary for a URL, or undefined if not cached. */
  async getSummary(url: string): Promise<CachedSummary | undefined> {
    const map = await this.getMap();
    return map[url];
  }

  /** Cache a summary for a URL. */
  async cacheSummary(url: string, summary: CachedSummary): Promise<void> {
    const map = await this.getMap();
    map[url] = summary;
    await this.saveMap(map);
    const stats = await this.getStats();
    stats.unique_urls = Object.keys(map).length;
    stats.top_urls = Object.keys(map).slice(0, 20);
    await this.saveStats(stats);
  }

  /** Record a cache hit. */
  async recordHit(): Promise<void> {
    const stats = await this.getStats();
    stats.total_requests += 1;
    stats.cache_hits += 1;
    await this.saveStats(stats);
  }

  /** Record a cache miss. */
  async recordMiss(): Promise<void> {
    const stats = await this.getStats();
    stats.total_requests += 1;
    stats.cache_misses += 1;
    await this.saveStats(stats);
  }

  /** Invalidate cache for a URL. */
  async invalidate(url: string): Promise<boolean> {
    const map = await this.getMap();
    if (!(url in map)) return false;
    delete map[url];
    await this.saveMap(map);
    return true;
  }

  /** Get cumulative stats. */
  async getSummaryStats(): Promise<Stats> {
    return this.getStats();
  }

  /** List all cached URLs. */
  async listCached(limit = 50): Promise<string[]> {
    const map = await this.getMap();
    return Object.keys(map).slice(0, limit);
  }
}
