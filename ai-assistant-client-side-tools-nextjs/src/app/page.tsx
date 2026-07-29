"use client";

import {
  Activity,
  BarChart3,
  Bot,
  Check,
  ChevronRight,
  CircleDot,
  Moon,
  PanelLeft,
  PhoneCall,
  PhoneOff,
  Plus,
  Settings,
  Sparkles,
  Sun,
  X,
} from "lucide-react";
import {
  TelnyxAIAgentProvider,
  useAgentState,
  useClient,
  useConnectionState,
  useConversation,
  useTranscript,
} from "@telnyx/ai-agent-lib";
import type { ClientSideToolContext, ClientSideToolHandler } from "@telnyx/ai-agent-lib";
import { useEffect, useMemo, useRef, useState } from "react";
import {
  ActivityEntry,
  AssistantField,
  AssistantFormState,
  ClientToolName,
  DashboardSection,
  DashboardTheme,
  clientToolSchemas,
  isAssistantField,
  isLanguage,
  isSection,
  isTheme,
  isVoice,
  languages,
  sections,
  voices,
} from "@/lib/dashboard-tools";
import { telnyxConfig, telnyxConfigStatus } from "@/lib/telnyx-config";

type AssistantRecord = {
  id: string;
  name: string;
  voice: string;
  language: string;
  status: "Draft" | "Live";
};

type ToolExecutor = (
  toolName: ClientToolName,
  input?: unknown,
  context?: ClientSideToolContext,
) => Promise<unknown>;

const initialFormState: AssistantFormState = {
  name: "Revenue Concierge",
  voice: "Nova",
  language: "English",
  isModalOpen: false,
};

const navItems: Array<{
  section: DashboardSection;
  label: string;
  icon: typeof PanelLeft;
}> = [
  { section: "overview", label: "Overview", icon: PanelLeft },
  { section: "assistants", label: "AI Assistants", icon: Bot },
  { section: "analytics", label: "Analytics", icon: BarChart3 },
  { section: "settings", label: "Settings", icon: Settings },
];

function nowStamp() {
  return new Intl.DateTimeFormat("en", {
    hour: "numeric",
    minute: "2-digit",
    second: "2-digit",
  }).format(new Date());
}

function hasValue(input: unknown, key: string) {
  return typeof input === "object" && input !== null && key in input;
}

function getInputValue(input: unknown, key: string) {
  return hasValue(input, key) ? (input as Record<string, unknown>)[key] : undefined;
}

function DashboardShell() {
  const [theme, setThemeState] = useState<DashboardTheme>("light");
  const [activeSection, setActiveSection] =
    useState<DashboardSection>("overview");
  const [formState, setFormState] =
    useState<AssistantFormState>(initialFormState);
  const [activity, setActivity] = useState<ActivityEntry[]>([]);
  const [toast, setToast] = useState<string | null>(null);
  const [assistants, setAssistants] = useState<AssistantRecord[]>([
    {
      id: "assistant-1",
      name: "Onboarding Guide",
      voice: "Cedar",
      language: "English",
      status: "Live",
    },
    {
      id: "assistant-2",
      name: "Billing Navigator",
      voice: "Luna",
      language: "Spanish",
      status: "Draft",
    },
  ]);

  const stateRef = useRef({
    theme,
    activeSection,
    formState,
  });

  useEffect(() => {
    stateRef.current = { theme, activeSection, formState };
  }, [theme, activeSection, formState]);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
  }, [theme]);

  useEffect(() => {
    if (!toast) return;
    const timer = window.setTimeout(() => setToast(null), 2600);
    return () => window.clearTimeout(timer);
  }, [toast]);

  const addActivity = (
    toolName: ClientToolName,
    input: unknown,
    context?: ClientSideToolContext,
  ) => {
    const id =
      context?.callId ?? `${toolName}-${Date.now()}-${Math.random().toString(16).slice(2)}`;
    const entry: ActivityEntry = {
      id,
      timestamp: nowStamp(),
      toolName,
      input: input ?? {},
      status: "running",
    };
    setActivity((current) => [entry, ...current].slice(0, 24));
    return id;
  };

  const updateActivity = (
    id: string,
    patch: Partial<Pick<ActivityEntry, "status" | "result" | "error">>,
  ) => {
    setActivity((current) =>
      current.map((entry) => (entry.id === id ? { ...entry, ...patch } : entry)),
    );
  };

  const getLiveFormState = () => ({ ...stateRef.current.formState });

  const applyTheme = (nextTheme: DashboardTheme) => {
    stateRef.current = { ...stateRef.current, theme: nextTheme };
    setThemeState(nextTheme);
  };

  const applySection = (nextSection: DashboardSection) => {
    stateRef.current = { ...stateRef.current, activeSection: nextSection };
    setActiveSection(nextSection);
  };

  const applyFormState = (nextFormState: AssistantFormState) => {
    stateRef.current = { ...stateRef.current, formState: nextFormState };
    setFormState(nextFormState);
  };

  const updateForm = (field: AssistantField, value: string) => {
    const nextState = { ...getLiveFormState() };
    if (field === "name") {
      nextState.name = value.trim();
    }
    if (field === "voice" && isVoice(value)) {
      nextState.voice = value;
    }
    if (field === "language" && isLanguage(value)) {
      nextState.language = value;
    }
    applyFormState(nextState);
    return nextState;
  };

  const executeTool: ToolExecutor = async (toolName, input, context) => {
    const activityId = addActivity(toolName, input, context);

    try {
      const work = async () => {
        if (toolName === "set_theme") {
          const requestedTheme = getInputValue(input, "theme");
          if (!isTheme(requestedTheme)) {
            return { success: false, error: "invalid_theme", accepted: ["light", "dark"] };
          }
          applyTheme(requestedTheme);
          return { success: true, theme: requestedTheme };
        }

        if (toolName === "navigate_to_section") {
          const section = getInputValue(input, "section");
          if (!isSection(section)) {
            return {
              success: false,
              error: "unknown_section",
              accepted: sections,
            };
          }
          applySection(section);
          return { success: true, section };
        }

        if (toolName === "open_create_assistant_modal") {
          applySection("assistants");
          applyFormState({ ...getLiveFormState(), isModalOpen: true });
          return { success: true, modal: "create_assistant" };
        }

        if (toolName === "get_form_state") {
          return getLiveFormState();
        }

        if (toolName === "update_assistant_form") {
          if (!stateRef.current.formState.isModalOpen) {
            return {
              success: false,
              error: "modal_closed",
              message: "Open the Create Assistant modal before updating the form.",
              formState: getLiveFormState(),
            };
          }

          const field = getInputValue(input, "field");
          const value = getInputValue(input, "value");
          if (!isAssistantField(field)) {
            return {
              success: false,
              error: "unknown_form_field",
              accepted: ["name", "voice", "language"],
              formState: getLiveFormState(),
            };
          }
          if (typeof value !== "string" || value.trim().length === 0) {
            return {
              success: false,
              error: "invalid_value",
              message: "Value must be a non-empty string.",
              formState: getLiveFormState(),
            };
          }
          if (field === "name" && value.trim().length > 60) {
            return {
              success: false,
              error: "invalid_value",
              message: "Name must be 60 characters or fewer.",
              formState: getLiveFormState(),
            };
          }
          if (field === "voice" && !isVoice(value)) {
            return {
              success: false,
              error: "invalid_value",
              accepted: voices,
              formState: getLiveFormState(),
            };
          }
          if (field === "language" && !isLanguage(value)) {
            return {
              success: false,
              error: "invalid_value",
              accepted: languages,
              formState: getLiveFormState(),
            };
          }

          const resultingState = updateForm(field, value);
          return { success: true, formState: resultingState };
        }

        return { success: false, error: "unknown_tool" };
      };

      const timeout = new Promise((resolve) => {
        window.setTimeout(
          () => resolve({ success: false, error: "timeout" }),
          telnyxConfig.clientToolTimeoutMs,
        );
      });
      const result = await Promise.race([work(), timeout]);
      const failed =
        typeof result === "object" &&
        result !== null &&
        "success" in result &&
        (result as { success?: boolean }).success === false;
      updateActivity(activityId, {
        status: failed ? "failed" : "completed",
        result,
      });
      return result;
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unknown tool error";
      updateActivity(activityId, { status: "failed", error: message });
      return { success: false, error: "handler_error", message };
    }
  };

  const saveAssistant = () => {
    const current = getLiveFormState();
    if (current.name.trim().length === 0) {
      setToast("Assistant name is required.");
      return;
    }
    setAssistants((existing) => [
      {
        id: `assistant-${Date.now()}`,
        name: current.name,
        voice: current.voice,
        language: current.language,
        status: "Draft",
      },
      ...existing,
    ]);
    applyFormState({ ...current, isModalOpen: false });
    setToast("Fake assistant saved locally.");
  };

  return (
    <div className="min-h-screen bg-[#f6f7f3] text-slate-950 transition-colors dark:bg-[#101111] dark:text-slate-100">
      <div className="flex min-h-screen">
        <Sidebar
          activeSection={activeSection}
          onNavigate={(section) => void executeTool("navigate_to_section", { section })}
        />
        <main className="flex min-w-0 flex-1 flex-col">
          <Header
            theme={theme}
            activeSection={activeSection}
            onTheme={(nextTheme) => void executeTool("set_theme", { theme: nextTheme })}
          />
          <div className="grid flex-1 grid-cols-1 gap-5 p-4 lg:grid-cols-[minmax(0,1fr)_390px] lg:p-6">
            <section className="min-w-0">
              <SectionContent
                section={activeSection}
                assistants={assistants}
                onOpenCreate={() => void executeTool("open_create_assistant_modal", {})}
              />
            </section>
            <aside className="flex min-h-0 flex-col gap-5">
              <WidgetPanel executeTool={executeTool} />
              {telnyxConfig.demoControlsEnabled ? (
                <DemoControls executeTool={executeTool} formState={formState} />
              ) : null}
              <ActivityPanel activity={activity} />
            </aside>
          </div>
        </main>
      </div>
      {formState.isModalOpen ? (
        <CreateAssistantModal
          formState={formState}
          setFormState={setFormState}
          onClose={() => applyFormState({ ...getLiveFormState(), isModalOpen: false })}
          onSave={saveAssistant}
        />
      ) : null}
      {toast ? (
        <div className="fixed bottom-5 left-1/2 z-50 flex -translate-x-1/2 items-center gap-2 rounded-md border border-emerald-300 bg-white px-4 py-3 text-sm font-medium text-emerald-800 shadow-lg dark:border-emerald-800 dark:bg-[#141816] dark:text-emerald-200">
          <Check size={16} />
          {toast}
        </div>
      ) : null}
    </div>
  );
}

function Sidebar({
  activeSection,
  onNavigate,
}: {
  activeSection: DashboardSection;
  onNavigate: (section: DashboardSection) => void;
}) {
  return (
    <aside className="hidden w-72 shrink-0 border-r border-slate-200 bg-white/80 p-4 backdrop-blur dark:border-white/10 dark:bg-[#151717]/90 md:block">
      <div className="mb-8 flex items-center gap-3 px-2">
        <div className="flex size-10 items-center justify-center rounded-md bg-[#00e3aa] text-slate-950">
          <Sparkles size={20} />
        </div>
        <div>
          <div className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">
            PolarForge AI
          </div>
          <div className="text-lg font-semibold">Control Center</div>
        </div>
      </div>
      <nav className="space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeSection === item.section;
          return (
            <button
              key={item.section}
              type="button"
              onClick={() => onNavigate(item.section)}
              className={`flex h-11 w-full items-center justify-between rounded-md px-3 text-sm font-medium transition ${
                isActive
                  ? "bg-slate-950 text-white dark:bg-white dark:text-slate-950"
                  : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-white/8"
              }`}
            >
              <span className="flex items-center gap-3">
                <Icon size={18} />
                {item.label}
              </span>
              {isActive ? <ChevronRight size={16} /> : null}
            </button>
          );
        })}
      </nav>
      <div className="mt-8 rounded-md border border-slate-200 bg-[#f7f8f4] p-4 dark:border-white/10 dark:bg-white/5">
        <div className="text-sm font-semibold">Client-side tools</div>
        <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-400">
          Browser actions are executed locally and logged in the activity panel.
        </p>
      </div>
    </aside>
  );
}

function Header({
  theme,
  activeSection,
  onTheme,
}: {
  theme: DashboardTheme;
  activeSection: DashboardSection;
  onTheme: (theme: DashboardTheme) => void;
}) {
  const title =
    activeSection === "assistants"
      ? "AI Assistants"
      : activeSection.charAt(0).toUpperCase() + activeSection.slice(1);

  return (
    <header className="border-b border-slate-200 bg-white/70 px-4 py-4 backdrop-blur dark:border-white/10 dark:bg-[#151717]/70 lg:px-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">
            Browser-executed AI actions
          </div>
          <h1 className="mt-1 text-2xl font-semibold tracking-normal">{title}</h1>
        </div>
        <div className="flex items-center gap-2 rounded-md border border-slate-200 bg-white p-1 dark:border-white/10 dark:bg-[#101111]">
          <button
            type="button"
            aria-label="Use light theme"
            title="Light theme"
            onClick={() => onTheme("light")}
            className={`flex size-9 items-center justify-center rounded-md ${
              theme === "light"
                ? "bg-[#00e3aa] text-slate-950"
                : "text-slate-500 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-white/8"
            }`}
          >
            <Sun size={17} />
          </button>
          <button
            type="button"
            aria-label="Use dark theme"
            title="Dark theme"
            onClick={() => onTheme("dark")}
            className={`flex size-9 items-center justify-center rounded-md ${
              theme === "dark"
                ? "bg-[#00e3aa] text-slate-950"
                : "text-slate-500 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-white/8"
            }`}
          >
            <Moon size={17} />
          </button>
        </div>
      </div>
    </header>
  );
}

function SectionContent({
  section,
  assistants,
  onOpenCreate,
}: {
  section: DashboardSection;
  assistants: AssistantRecord[];
  onOpenCreate: () => void;
}) {
  if (section === "assistants") {
    return (
      <div className="space-y-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-xl font-semibold">Assistant workspace</h2>
            <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
              Local assistant records for demonstrating browser-side state changes.
            </p>
          </div>
          <button
            type="button"
            onClick={onOpenCreate}
            className="inline-flex h-10 items-center gap-2 rounded-md bg-slate-950 px-4 text-sm font-semibold text-white hover:bg-slate-800 dark:bg-[#00e3aa] dark:text-slate-950"
          >
            <Plus size={17} />
            Create Assistant
          </button>
        </div>
        <div className="grid gap-4 xl:grid-cols-2">
          {assistants.map((assistant) => (
            <div
              key={assistant.id}
              className="rounded-md border border-slate-200 bg-white p-5 shadow-sm dark:border-white/10 dark:bg-[#151717]"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="text-lg font-semibold">{assistant.name}</div>
                  <div className="mt-2 flex flex-wrap gap-2 text-xs font-medium text-slate-600 dark:text-slate-300">
                    <span className="rounded-md bg-slate-100 px-2 py-1 dark:bg-white/8">
                      Voice: {assistant.voice}
                    </span>
                    <span className="rounded-md bg-slate-100 px-2 py-1 dark:bg-white/8">
                      {assistant.language}
                    </span>
                  </div>
                </div>
                <span className="rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-700 dark:border-emerald-800 dark:bg-emerald-950/30 dark:text-emerald-300">
                  {assistant.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (section === "analytics") {
    return (
      <Panel title="Analytics">
        <div className="grid gap-4 lg:grid-cols-3">
          <Metric label="Sessions" value="18.4k" />
          <Metric label="Tool calls" value="7,832" />
          <Metric label="Conversion assist" value="21%" />
        </div>
        <div className="mt-5 h-72 rounded-md border border-dashed border-slate-300 bg-[linear-gradient(180deg,rgba(0,227,170,0.16),transparent)] p-5 dark:border-white/10 dark:bg-[linear-gradient(180deg,rgba(0,227,170,0.12),transparent)]">
          <div className="flex h-full items-end gap-3">
            {[48, 64, 38, 76, 58, 88, 72, 94, 68, 82, 90, 74].map((height, index) => (
              <div
                key={index}
                className="flex-1 rounded-t bg-slate-900 dark:bg-[#00e3aa]"
                style={{ height: `${height}%` }}
              />
            ))}
          </div>
        </div>
      </Panel>
    );
  }

  if (section === "settings") {
    return (
      <Panel title="Settings">
        <div className="grid gap-4 lg:grid-cols-2">
          <SettingRow title="Client tool timeout" value={`${telnyxConfig.clientToolTimeoutMs} ms`} />
          <SettingRow
            title="Telnyx config"
            value={telnyxConfigStatus.isConfigured ? "Configured" : "Missing agent ID"}
          />
          <SettingRow title="Environment" value={telnyxConfig.environment} />
          <SettingRow title="Demo controls" value={telnyxConfig.demoControlsEnabled ? "Enabled" : "Hidden"} />
        </div>
      </Panel>
    );
  }

  return (
    <div className="space-y-5">
      <div className="rounded-md border border-slate-200 bg-white p-6 shadow-sm dark:border-white/10 dark:bg-[#151717]">
        <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full bg-[#00e3aa]/20 px-3 py-1 text-xs font-semibold text-slate-800 dark:text-[#a6ffe6]">
              <CircleDot size={14} />
              Live browser tool demo
            </div>
            <h2 className="mt-5 max-w-2xl text-4xl font-semibold tracking-normal">
              PolarForge AI shows assistant actions happening inside the client.
            </h2>
            <p className="mt-4 max-w-2xl text-base leading-7 text-slate-600 dark:text-slate-300">
              Ask the embedded assistant to change theme, navigate sections, open the create flow,
              inspect form state, or fill fields. Each call runs JavaScript in this browser.
            </p>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
            <Metric label="Registered tools" value={String(clientToolSchemas.length)} />
            <Metric label="Execution path" value="Client" />
            <Metric label="Persistence" value="Local state" />
          </div>
        </div>
      </div>
      <div className="grid gap-4 lg:grid-cols-3">
        <Metric label="Active assistants" value="2" />
        <Metric label="Avg response" value="780ms" />
        <Metric label="Tool success" value="99.1%" />
      </div>
    </div>
  );
}

function WidgetPanel({ executeTool }: { executeTool: ToolExecutor }) {
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    const timer = window.setTimeout(() => setIsMounted(true), 0);
    return () => window.clearTimeout(timer);
  }, []);

  if (!telnyxConfigStatus.isConfigured) {
    return <VoiceAgentPreview status="Setup needed" />;
  }

  if (!isMounted) {
    return <VoiceAgentPreview status="Loading" />;
  }

  return (
    <TelnyxAIAgentProvider
      agentId={telnyxConfig.agentId}
      versionId={telnyxConfig.versionId}
      widgetVersion={telnyxConfig.widgetVersion}
      environment={telnyxConfig.environment}
      debug={telnyxConfig.debug}
      clientToolTimeoutMs={telnyxConfig.clientToolTimeoutMs}
    >
      <ToolRegistrar executeTool={executeTool} />
      <TelnyxWidget />
    </TelnyxAIAgentProvider>
  );
}

function VoiceAgentPreview({ status }: { status: "Setup needed" | "Loading" }) {
  return (
    <div className="rounded-md border border-slate-200 bg-white p-4 shadow-sm dark:border-white/10 dark:bg-[#151717]">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-sm font-semibold">Website voice agent</div>
          <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            Browser call surface
          </div>
        </div>
        <span className="rounded-full bg-slate-100 px-2 py-1 text-[11px] font-semibold text-slate-600 dark:bg-white/8 dark:text-slate-300">
          {status}
        </span>
      </div>
      <button
        type="button"
        disabled
        className="mt-4 inline-flex h-11 w-full cursor-not-allowed items-center justify-center gap-2 rounded-md bg-slate-200 text-sm font-semibold text-slate-500 dark:bg-white/10 dark:text-slate-400"
      >
        <PhoneCall size={17} />
        Call agent
      </button>
      <div className="mt-4 rounded-md bg-slate-100 p-3 text-sm leading-6 text-slate-600 dark:bg-black/30 dark:text-slate-300">
        {status === "Loading"
          ? "Preparing the in-browser voice session."
          : "Once connected to a Telnyx AI Assistant, this button starts the in-browser voice session. The assistant then calls the registered client-side tools to navigate and update this page."}
      </div>
    </div>
  );
}

function ToolRegistrar({ executeTool }: { executeTool: ToolExecutor }) {
  const client = useClient();

  useEffect(() => {
    const handlers: Record<ClientToolName, ClientSideToolHandler> = {
      set_theme: (args, context) => executeTool("set_theme", args, context),
      navigate_to_section: (args, context) =>
        executeTool("navigate_to_section", args, context),
      open_create_assistant_modal: (args, context) =>
        executeTool("open_create_assistant_modal", args, context),
      get_form_state: (args, context) => executeTool("get_form_state", args, context),
      update_assistant_form: (args, context) =>
        executeTool("update_assistant_form", args, context),
    };

    Object.entries(handlers).forEach(([name, handler]) => {
      client.registerClientTool(name, handler);
    });

    return () => {
      Object.keys(handlers).forEach((name) => {
        client.unregisterClientTool(name);
      });
    };
  }, [client, executeTool]);

  return null;
}

function TelnyxWidget() {
  const client = useClient();
  const connectionState = useConnectionState();
  const conversation = useConversation();
  const agentState = useAgentState();
  const transcript = useTranscript();
  const audioRef = useRef<HTMLAudioElement>(null);
  const [message, setMessage] = useState("");
  const [callError, setCallError] = useState<string | null>(null);
  const [isCalling, setIsCalling] = useState(false);
  const isCallActive = conversation?.call?.state === "active";

  useEffect(() => {
    if (conversation?.call?.remoteStream && audioRef.current) {
      audioRef.current.srcObject = conversation.call.remoteStream;
      void audioRef.current.play().catch(() => {
        setCallError("Audio playback was blocked. Press Call agent again or use the audio controls.");
      });
    }
  }, [conversation?.call?.remoteStream]);

  const transcriptGroups = useMemo(() => {
    return transcript.reduce<Array<{ id: string; role: string; content: string }>>(
      (groups, item) => {
        const previous = groups.at(-1);
        if (previous?.role === item.role) {
          previous.content = `${previous.content} ${item.content}`.replace(/\s+/g, " ");
          return groups;
        }
        groups.push({ id: item.id, role: item.role, content: item.content });
        return groups;
      },
      [],
    );
  }, [transcript]);

  const waitForAgentLogin = () => {
    if (client.isAuthenticated && client.sessionId) {
      return Promise.resolve();
    }

    return new Promise<void>((resolve, reject) => {
      const timeout = window.setTimeout(() => {
        cleanup();
        reject(new Error("Timed out while connecting to the website voice agent."));
      }, telnyxConfig.clientToolTimeoutMs);

      const cleanup = () => {
        window.clearTimeout(timeout);
        client.removeListener("agent.login.success", handleReady);
        client.removeListener("agent.connected", handleReady);
        client.removeListener("agent.error", handleError);
      };

      const handleReady = () => {
        if (!client.isAuthenticated || !client.sessionId) return;
        cleanup();
        resolve();
      };

      const handleError = (error: Error) => {
        cleanup();
        reject(error);
      };

      client.on("agent.login.success", handleReady);
      client.on("agent.connected", handleReady);
      client.on("agent.error", handleError);
      void client.connect();
    });
  };

  const handleCall = async () => {
    setCallError(null);
    setIsCalling(true);
    try {
      if (isCallActive) {
        await client.endConversation();
        return;
      }
      await waitForAgentLogin();
      await client.startConversation({ callerName: "PolarForge Demo User" });
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Unable to start the browser call.";
      setCallError(
        message.includes("before login is complete")
          ? "The website voice agent is still connecting. Try again in a moment."
          : message,
      );
    } finally {
      setIsCalling(false);
    }
  };

  return (
    <div className="rounded-md border border-slate-200 bg-white p-4 shadow-sm dark:border-white/10 dark:bg-[#151717]">
      <div className="flex items-center justify-between gap-3">
        <div>
          <div className="text-sm font-semibold">Website voice agent</div>
          <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            Connection: {connectionState} · Agent: {agentState?.state ?? "idle"}
          </div>
        </div>
        <button
          type="button"
          onClick={() => void handleCall()}
          disabled={isCalling}
          className={`inline-flex h-10 items-center gap-2 rounded-md px-3 text-xs font-semibold disabled:cursor-not-allowed disabled:opacity-60 ${
            isCallActive
              ? "bg-rose-600 text-white hover:bg-rose-700"
              : "bg-slate-950 text-white hover:bg-slate-800 dark:bg-[#00e3aa] dark:text-slate-950"
          }`}
        >
          {isCallActive ? <PhoneOff size={14} /> : <PhoneCall size={14} />}
          {isCalling ? "Calling..." : isCallActive ? "End call" : "Call agent"}
        </button>
      </div>
      {callError ? (
        <div className="mt-3 rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-xs font-medium text-rose-700 dark:border-rose-800 dark:bg-rose-950/30 dark:text-rose-200">
          {callError}
        </div>
      ) : null}
      <div className="mt-4 rounded-md bg-slate-100 p-3 dark:bg-black/30">
        <audio
          ref={audioRef}
          autoPlay
          playsInline
          controls
          className="mb-3 h-9 w-full"
        />
        <div className="max-h-36 space-y-2 overflow-auto text-xs">
          {transcriptGroups.length === 0 ? (
            <p className="text-slate-500 dark:text-slate-400">
              Transcript appears here after a conversation starts.
            </p>
          ) : (
            transcriptGroups.slice(-5).map((item) => (
              <div key={item.id}>
                <span className="font-semibold">{item.role}: </span>
                {item.content}
              </div>
            ))
          )}
        </div>
        <div className="mt-3 flex gap-2">
          <input
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            placeholder="Send a chat message"
            className="h-9 min-w-0 flex-1 rounded-md border border-slate-200 bg-white px-3 text-sm outline-none focus:border-[#00b887] dark:border-white/10 dark:bg-[#101111]"
          />
          <button
            type="button"
            disabled={!isCallActive || message.trim().length === 0}
            onClick={() => {
              client.sendConversationMessage(message);
              setMessage("");
            }}
            className="rounded-md bg-slate-950 px-3 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50 dark:bg-[#00e3aa] dark:text-slate-950"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}

function DemoControls({
  executeTool,
  formState,
}: {
  executeTool: ToolExecutor;
  formState: AssistantFormState;
}) {
  const [field, setField] = useState<AssistantField>("name");
  const [value, setValue] = useState("Enterprise Concierge");

  return (
    <div className="rounded-md border border-slate-200 bg-white p-4 shadow-sm dark:border-white/10 dark:bg-[#151717]">
      <div className="flex items-center justify-between gap-3">
        <div>
          <div className="text-sm font-semibold">Demo Controls</div>
          <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            Development toggle for manual tool testing.
          </div>
        </div>
        <Activity size={18} className="text-slate-500" />
      </div>
      <div className="mt-4 grid grid-cols-2 gap-2">
        <button className="demo-button" onClick={() => void executeTool("set_theme", { theme: "light" })}>
          Light
        </button>
        <button className="demo-button" onClick={() => void executeTool("set_theme", { theme: "dark" })}>
          Dark
        </button>
        {sections.map((section) => (
          <button
            key={section}
            className="demo-button capitalize"
            onClick={() => void executeTool("navigate_to_section", { section })}
          >
            {section}
          </button>
        ))}
      </div>
      <div className="mt-3 grid grid-cols-2 gap-2">
        <button
          className="demo-button"
          onClick={() => void executeTool("open_create_assistant_modal", {})}
        >
          Open modal
        </button>
        <button className="demo-button" onClick={() => void executeTool("get_form_state", {})}>
          Read form
        </button>
      </div>
      <div className="mt-4 rounded-md border border-slate-200 p-3 dark:border-white/10">
        <div className="grid gap-2 sm:grid-cols-[120px_1fr]">
          <select
            value={field}
            onChange={(event) => setField(event.target.value as AssistantField)}
            className="h-9 rounded-md border border-slate-200 bg-white px-2 text-sm dark:border-white/10 dark:bg-[#101111]"
          >
            <option value="name">name</option>
            <option value="voice">voice</option>
            <option value="language">language</option>
          </select>
          <input
            value={value}
            onChange={(event) => setValue(event.target.value)}
            className="h-9 min-w-0 rounded-md border border-slate-200 bg-white px-3 text-sm dark:border-white/10 dark:bg-[#101111]"
          />
        </div>
        <button
          className="mt-2 h-9 w-full rounded-md bg-[#00e3aa] text-sm font-semibold text-slate-950"
          onClick={() =>
            void executeTool("update_assistant_form", {
              field,
              value,
            })
          }
        >
          Update form
        </button>
        <div className="mt-2 text-xs text-slate-500 dark:text-slate-400">
          Modal: {formState.isModalOpen ? "open" : "closed"}
        </div>
      </div>
    </div>
  );
}

function ActivityPanel({ activity }: { activity: ActivityEntry[] }) {
  return (
    <div className="flex min-h-[360px] flex-1 flex-col rounded-md border border-slate-200 bg-white shadow-sm dark:border-white/10 dark:bg-[#151717]">
      <div className="border-b border-slate-200 p-4 dark:border-white/10">
        <div className="text-sm font-semibold">Client-tool activity</div>
        <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
          Every manual or assistant-triggered invocation appears here.
        </p>
      </div>
      <div className="min-h-0 flex-1 overflow-auto p-3">
        {activity.length === 0 ? (
          <div className="flex h-40 items-center justify-center rounded-md border border-dashed border-slate-300 text-sm text-slate-500 dark:border-white/10 dark:text-slate-400">
            Waiting for tool calls
          </div>
        ) : (
          <div className="space-y-3">
            {activity.map((entry) => (
              <div
                key={entry.id}
                className="rounded-md border border-slate-200 bg-[#f8f9f5] p-3 dark:border-white/10 dark:bg-black/20"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="font-mono text-xs font-semibold">{entry.toolName}</div>
                    <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                      {entry.timestamp}
                    </div>
                  </div>
                  <span
                    className={`rounded-full px-2 py-1 text-[11px] font-semibold ${
                      entry.status === "completed"
                        ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300"
                        : entry.status === "failed"
                          ? "bg-rose-100 text-rose-700 dark:bg-rose-950 dark:text-rose-300"
                          : "bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300"
                    }`}
                  >
                    {entry.status}
                  </span>
                </div>
                <JsonBlock label="Input" value={entry.input} />
                {entry.result !== undefined ? (
                  <JsonBlock label="Result" value={entry.result} />
                ) : null}
                {entry.error ? <JsonBlock label="Error" value={entry.error} /> : null}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function CreateAssistantModal({
  formState,
  setFormState,
  onClose,
  onSave,
}: {
  formState: AssistantFormState;
  setFormState: React.Dispatch<React.SetStateAction<AssistantFormState>>;
  onClose: () => void;
  onSave: () => void;
}) {
  return (
    <div className="pointer-events-none fixed inset-0 z-40 flex items-center justify-center bg-black/45 p-4">
      <div className="pointer-events-auto w-full max-w-lg rounded-md border border-slate-200 bg-white shadow-2xl dark:border-white/10 dark:bg-[#151717]">
        <div className="flex items-center justify-between border-b border-slate-200 p-5 dark:border-white/10">
          <div>
            <div className="text-lg font-semibold">Create Assistant</div>
            <div className="mt-1 text-sm text-slate-500 dark:text-slate-400">
              This form is local React state.
            </div>
          </div>
          <button
            type="button"
            aria-label="Close modal"
            title="Close"
            onClick={onClose}
            className="flex size-9 items-center justify-center rounded-md text-slate-500 hover:bg-slate-100 dark:hover:bg-white/8"
          >
            <X size={18} />
          </button>
        </div>
        <div className="space-y-4 p-5">
          <label className="block">
            <span className="text-sm font-semibold">Name</span>
            <input
              value={formState.name}
              onChange={(event) =>
                setFormState((current) => ({ ...current, name: event.target.value }))
              }
              className="mt-2 h-11 w-full rounded-md border border-slate-200 bg-white px-3 outline-none focus:border-[#00b887] dark:border-white/10 dark:bg-[#101111]"
            />
          </label>
          <label className="block">
            <span className="text-sm font-semibold">Voice</span>
            <select
              value={formState.voice}
              onChange={(event) =>
                setFormState((current) => ({
                  ...current,
                  voice: event.target.value as AssistantFormState["voice"],
                }))
              }
              className="mt-2 h-11 w-full rounded-md border border-slate-200 bg-white px-3 outline-none focus:border-[#00b887] dark:border-white/10 dark:bg-[#101111]"
            >
              {voices.map((voice) => (
                <option key={voice}>{voice}</option>
              ))}
            </select>
          </label>
          <label className="block">
            <span className="text-sm font-semibold">Language</span>
            <select
              value={formState.language}
              onChange={(event) =>
                setFormState((current) => ({
                  ...current,
                  language: event.target.value as AssistantFormState["language"],
                }))
              }
              className="mt-2 h-11 w-full rounded-md border border-slate-200 bg-white px-3 outline-none focus:border-[#00b887] dark:border-white/10 dark:bg-[#101111]"
            >
              {languages.map((language) => (
                <option key={language}>{language}</option>
              ))}
            </select>
          </label>
        </div>
        <div className="flex justify-end gap-2 border-t border-slate-200 p-5 dark:border-white/10">
          <button
            type="button"
            onClick={onClose}
            className="h-10 rounded-md border border-slate-200 px-4 text-sm font-semibold hover:bg-slate-100 dark:border-white/10 dark:hover:bg-white/8"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={onSave}
            className="h-10 rounded-md bg-slate-950 px-4 text-sm font-semibold text-white dark:bg-[#00e3aa] dark:text-slate-950"
          >
            Save fake assistant
          </button>
        </div>
      </div>
    </div>
  );
}

function Panel({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-md border border-slate-200 bg-white p-6 shadow-sm dark:border-white/10 dark:bg-[#151717]">
      <h2 className="text-xl font-semibold">{title}</h2>
      <div className="mt-5">{children}</div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-slate-200 bg-white p-4 dark:border-white/10 dark:bg-[#151717]">
      <div className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500 dark:text-slate-400">
        {label}
      </div>
      <div className="mt-2 text-2xl font-semibold">{value}</div>
    </div>
  );
}

function SettingRow({ title, value }: { title: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-md border border-slate-200 p-4 dark:border-white/10">
      <span className="text-sm font-medium">{title}</span>
      <span className="rounded-md bg-slate-100 px-2 py-1 text-sm text-slate-700 dark:bg-white/8 dark:text-slate-200">
        {value}
      </span>
    </div>
  );
}

function JsonBlock({ label, value }: { label: string; value: unknown }) {
  return (
    <div className="mt-2">
      <div className="mb-1 text-[11px] font-semibold uppercase tracking-[0.12em] text-slate-500 dark:text-slate-400">
        {label}
      </div>
      <pre className="max-h-28 overflow-auto rounded-md bg-slate-950 p-2 text-[11px] leading-5 text-slate-100">
        {JSON.stringify(value, null, 2)}
      </pre>
    </div>
  );
}

export default function Home() {
  return <DashboardShell />;
}
