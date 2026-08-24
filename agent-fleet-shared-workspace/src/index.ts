export { FleetAgent, FleetRegistry } from "./fleetAgent";
import type { FleetAgent, FleetRegistry, AgentRecord, FileMetadata, FleetAgentState } from "./fleetAgent";
import type { ActorNamespace, ActorStub, IdFromNameOptions } from "@telnyx/edge-runtime";

type FleetStub = ActorStub & Pick<FleetAgent, "initialize" | "write" | "read" | "list" | "getStatus">;
interface FleetNamespace extends ActorNamespace {
  idFromName(name: string, options?: IdFromNameOptions): FleetStub;
}

type RegistryStub = ActorStub & Pick<FleetRegistry, "listAgents" | "listFiles">;
interface RegistryNamespace extends ActorNamespace {
  idFromName(name: string, options?: IdFromNameOptions): RegistryStub;
}

interface Env {
  FLEET_AGENT: FleetNamespace;
  REGISTRY: RegistryNamespace;
  CLOUDFS_MOUNT_PATH: string;
  CLOUDFS_WORKSPACE_DIR: string;
}

const DEMO_AGENTS = [
  { id: "agent-1", role: "writer" },
  { id: "agent-2", role: "analyst" },
  { id: "agent-3", role: "reviewer" },
  { id: "agent-4", role: "summarizer" },
  { id: "agent-5", role: "publisher" },
] as const;

function agent(env: Env, id: string): FleetStub {
  return env.FLEET_AGENT.idFromName(id);
}

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url);

    if (url.pathname === "/health/liveness" || url.pathname === "/health/readiness") {
      return new Response("ok");
    }

    if (req.method === "POST" && url.pathname === "/demo") {
      return runDemo(env);
    }

    if (req.method === "POST" && url.pathname === "/artifacts") {
      return writeArtifact(req, env);
    }

    if (req.method === "GET" && url.pathname.startsWith("/artifacts/")) {
      const path = decodeURIComponent(url.pathname.slice("/artifacts/".length));
      const agentId = url.searchParams.get("agent") || "agent-1";
      if (!path) return Response.json({ error: "missing artifact path" }, { status: 400 });
      try {
        const result = await agent(env, agentId).read({ path });
        return Response.json({ agentId, path, ...result });
      } catch (error: unknown) {
        return errorResponse(error, "failed to read artifact");
      }
    }

    if (req.method === "GET" && url.pathname === "/artifacts") {
      try {
        return Response.json({ artifacts: await agent(env, "agent-1").list() });
      } catch (error: unknown) {
        return errorResponse(error, "failed to list artifacts");
      }
    }

    if (req.method === "GET" && url.pathname.startsWith("/agents/")) {
      const agentId = url.pathname.slice("/agents/".length);
      if (!agentId) return Response.json({ error: "missing agent id" }, { status: 400 });
      try {
        return Response.json(await agent(env, agentId).getStatus());
      } catch (error: unknown) {
        return errorResponse(error, "failed to get agent status");
      }
    }

    if (req.method === "GET" && url.pathname === "/fleet") {
      try {
        const registry = env.REGISTRY.idFromName("shared");
        const [agents, files] = await Promise.all([registry.listAgents(), registry.listFiles(100)]);
        return Response.json({ agents, files });
      } catch (error: unknown) {
        return errorResponse(error, "failed to get fleet status");
      }
    }

    return Response.json(
      {
        name: "agent-fleet-shared-workspace",
        endpoints: ["POST /demo", "POST /artifacts", "GET /artifacts", "GET /artifacts/:path", "GET /agents/:id", "GET /fleet"],
      },
      { status: 404 },
    );
  },
};

async function writeArtifact(req: Request, env: Env): Promise<Response> {
  const body = (await req.json().catch(() => ({}))) as { agentId?: string; path?: string; content?: string; role?: string };
  if (!body.agentId || !body.path || typeof body.content !== "string") {
    return Response.json({ error: "agentId, path, and string content are required" }, { status: 400 });
  }
  try {
    const stub = agent(env, body.agentId);
    await stub.initialize({ agentId: body.agentId, role: body.role || "worker" });
    const metadata = await stub.write({ path: body.path, content: body.content });
    return Response.json({ metadata }, { status: 201 });
  } catch (error: unknown) {
    return errorResponse(error, "failed to write artifact");
  }
}

async function runDemo(env: Env): Promise<Response> {
  try {
    await Promise.all(DEMO_AGENTS.map((entry) => agent(env, entry.id).initialize({ agentId: entry.id, role: entry.role })));

    const writer = agent(env, "agent-1");
    const analyst = agent(env, "agent-2");
    const reviewer = agent(env, "agent-3");
    const summarizer = agent(env, "agent-4");
    const publisher = agent(env, "agent-5");

    await writer.write({
      path: "report.md",
      content: "# Fleet report\n\nFive agents are collaborating through one CloudFS workspace.\n",
    });
    const report = await analyst.read({ path: "report.md" });
    await analyst.write({
      path: "analysis.json",
      content: JSON.stringify({ source: "report.md", words: report.content.trim().split(/\s+/).length, finding: "shared workspace is reachable" }, null, 2),
    });
    const analysis = await reviewer.read({ path: "analysis.json" });
    await reviewer.write({ path: "review.md", content: `# Review\n\nValidated analysis:\n\n~~~json\n${analysis.content}\n~~~\n` });
    const review = await summarizer.read({ path: "review.md" });
    await summarizer.write({ path: "summary.md", content: `# Summary\n\nThe fleet completed a five-agent CloudFS handoff.\n\n${review.content}` });
    const summary = await publisher.read({ path: "summary.md" });
    await publisher.write({
      path: "manifest.json",
      content: JSON.stringify({ publishedAt: new Date().toISOString(), source: "summary.md", bytes: summary.content.length }, null, 2),
    });

    const registry = env.REGISTRY.idFromName("shared");
    const [agents, files] = await Promise.all([registry.listAgents(), registry.listFiles(100)]);
    return Response.json({ status: "complete", agents, files });
  } catch (error: unknown) {
    return errorResponse(error, "demo failed");
  }
}

function errorResponse(error: unknown, fallback: string): Response {
  const message = error instanceof Error ? error.message : fallback;
  const status = message.includes("escapes the shared workspace") ? 400 : message.includes("ENOENT") ? 404 : 500;
  return Response.json({ error: message || fallback }, { status });
}

export type FleetApiSnapshot = { agents: AgentRecord[]; files: FileMetadata[]; states?: FleetAgentState[] };
