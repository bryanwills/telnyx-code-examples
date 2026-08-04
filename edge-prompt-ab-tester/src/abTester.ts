import { StatefulActor } from "@telnyx/edge-runtime";

export interface Experiment {
  id: string;
  task: string;
  variant_a: { prompt: string; response: string };
  variant_b: { prompt: string; response: string };
  votes_a: number;
  votes_b: number;
  status: "open" | "closed";
  created_at: string;
}

export interface Stats {
  total_experiments: number;
  open_experiments: number;
  closed_experiments: number;
  total_votes: number;
  leader: string | null;
  leader_votes: number;
}

/**
 * ABTester — one actor instance per experiment collection.
 *
 * Tracks prompt variants, responses, and vote counts in durable storage.
 */
export class ABTester extends StatefulActor {
  private async getExperiments(): Promise<Record<string, Experiment>> {
    return (await this.ctx.storage.get<Record<string, Experiment>>("experiments")) ?? {};
  }

  private async saveExperiments(experiments: Record<string, Experiment>): Promise<void> {
    await this.ctx.storage.put("experiments", experiments);
  }

  private async getVotes(): Promise<{ a: number; b: number; experiment_votes: Record<string, { a: number; b: number }> }> {
    return (
      (await this.ctx.storage.get<{ a: number; b: number; experiment_votes: Record<string, { a: number; b: number }> }>("votes")) ?? {
        a: 0,
        b: 0,
        experiment_votes: {},
      }
    );
  }

  private async saveVotes(votes: { a: number; b: number; experiment_votes: Record<string, { a: number; b: number }> }): Promise<void> {
    await this.ctx.storage.put("votes", votes);
  }

  /** Create a new experiment with A/B responses. */
  async createExperiment(experiment: Experiment): Promise<void> {
    const experiments = await this.getExperiments();
    experiments[experiment.id] = experiment;
    await this.saveExperiments(experiments);
  }

  /** Record a vote for a variant. */
  async vote(experimentId: string, variant: "a" | "b"): Promise<Experiment | null> {
    const experiments = await this.getExperiments();
    const experiment = experiments[experimentId];
    if (!experiment || experiment.status === "closed") return null;

    if (variant === "a") experiment.votes_a += 1;
    else experiment.votes_b += 1;
    await this.saveExperiments(experiments);

    const votes = await this.getVotes();
    votes.experiment_votes[experimentId] = votes.experiment_votes[experimentId] ?? { a: 0, b: 0 };
    if (variant === "a") votes.a += 1; else votes.b += 1;
    if (variant === "a") votes.experiment_votes[experimentId].a += 1;
    else votes.experiment_votes[experimentId].b += 1;
    await this.saveVotes(votes);

    return experiment;
  }

  /** Close an experiment (no more votes). */
  async closeExperiment(experimentId: string): Promise<Experiment | null> {
    const experiments = await this.getExperiments();
    const experiment = experiments[experimentId];
    if (!experiment) return null;
    experiment.status = "closed";
    await this.saveExperiments(experiments);
    return experiment;
  }

  /** Get a specific experiment. */
  async getExperiment(experimentId: string): Promise<Experiment | undefined> {
    const experiments = await this.getExperiments();
    return experiments[experimentId];
  }

  /** List experiments. */
  async listExperiments(limit = 20): Promise<Experiment[]> {
    const experiments = await this.getExperiments();
    return Object.values(experiments)
      .sort((a, b) => (a.created_at < b.created_at ? 1 : -1))
      .slice(0, limit);
  }

  /** Get cumulative stats. */
  async getStats(): Promise<Stats> {
    const experiments = await this.getExperiments();
    const votes = await this.getVotes();
    const list = Object.values(experiments);
    const open = list.filter((e) => e.status === "open").length;
    const closed = list.filter((e) => e.status === "closed").length;

    let totalA = 0;
    let totalB = 0;
    for (const v of Object.values(votes.experiment_votes)) {
      totalA += v.a;
      totalB += v.b;
    }

    let leader: string | null = null;
    let leaderVotes = -1;
    if (totalA >= totalB && totalA > 0) {
      leader = "variant_a";
      leaderVotes = totalA;
    } else if (totalB > 0) {
      leader = "variant_b";
      leaderVotes = totalB;
    }

    return {
      total_experiments: list.length,
      open_experiments: open,
      closed_experiments: closed,
      total_votes: totalA + totalB,
      leader,
      leader_votes: leaderVotes,
    };
  }
}
