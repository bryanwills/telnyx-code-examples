import type { TelnyxAIAgentConstructorParams } from "@telnyx/ai-agent-lib";

type TelnyxEnvironment = NonNullable<TelnyxAIAgentConstructorParams["environment"]>;

function parseEnvironment(value: string | undefined): TelnyxEnvironment {
  return value === "development" ? "development" : "production";
}

function parseTimeout(value: string | undefined): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : 15_000;
}

export const telnyxConfig = {
  agentId: process.env.NEXT_PUBLIC_TELNYX_AGENT_ID ?? "",
  versionId: process.env.NEXT_PUBLIC_TELNYX_AGENT_VERSION_ID || "main",
  environment: parseEnvironment(process.env.NEXT_PUBLIC_TELNYX_ENVIRONMENT),
  widgetVersion: process.env.NEXT_PUBLIC_TELNYX_WIDGET_VERSION || "polarforge-ai-demo",
  debug: process.env.NEXT_PUBLIC_TELNYX_DEBUG === "true",
  clientToolTimeoutMs: parseTimeout(
    process.env.NEXT_PUBLIC_TELNYX_CLIENT_TOOL_TIMEOUT_MS,
  ),
  demoControlsEnabled: process.env.NEXT_PUBLIC_ENABLE_DEMO_CONTROLS !== "false",
};

export const telnyxConfigStatus = {
  isConfigured: telnyxConfig.agentId.trim().length > 0,
  missing: telnyxConfig.agentId.trim().length > 0 ? [] : ["NEXT_PUBLIC_TELNYX_AGENT_ID"],
};
