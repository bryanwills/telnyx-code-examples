export const sections = ["overview", "assistants", "analytics", "settings"] as const;
export const themes = ["light", "dark"] as const;
export const assistantFields = ["name", "voice", "language"] as const;
export const voices = ["Nova", "Cedar", "Luna", "Atlas"] as const;
export const languages = ["English", "Spanish", "French", "German"] as const;

export type DashboardSection = (typeof sections)[number];
export type DashboardTheme = (typeof themes)[number];
export type AssistantField = (typeof assistantFields)[number];
export type AssistantVoice = (typeof voices)[number];
export type AssistantLanguage = (typeof languages)[number];

export type AssistantFormState = {
  name: string;
  voice: AssistantVoice;
  language: AssistantLanguage;
  isModalOpen: boolean;
};

export type ClientToolName =
  | "set_theme"
  | "navigate_to_section"
  | "open_create_assistant_modal"
  | "get_form_state"
  | "update_assistant_form";

export type ToolStatus = "running" | "completed" | "failed";

export type ActivityEntry = {
  id: string;
  timestamp: string;
  toolName: ClientToolName;
  input: unknown;
  status: ToolStatus;
  result?: unknown;
  error?: string;
};

export const clientToolSchemas = [
  {
    name: "set_theme",
    description:
      "Change the PolarForge AI dashboard theme. Use this when the user asks for light mode or dark mode.",
    parameters: {
      type: "object",
      additionalProperties: false,
      required: ["theme"],
      properties: {
        theme: {
          type: "string",
          enum: themes,
          description: "The visual theme to apply to the dashboard.",
        },
      },
    },
  },
  {
    name: "navigate_to_section",
    description:
      "Navigate the PolarForge AI dashboard to a section without reloading the page.",
    parameters: {
      type: "object",
      additionalProperties: false,
      required: ["section"],
      properties: {
        section: {
          type: "string",
          enum: sections,
          description: "The dashboard section to show.",
        },
      },
    },
  },
  {
    name: "open_create_assistant_modal",
    description:
      "Open the Create Assistant modal so the user can review or edit assistant details.",
    parameters: {
      type: "object",
      additionalProperties: false,
      properties: {},
    },
  },
  {
    name: "get_form_state",
    description:
      "Read the current Create Assistant form state from the browser, including whether the modal is open.",
    parameters: {
      type: "object",
      additionalProperties: false,
      properties: {},
    },
  },
  {
    name: "update_assistant_form",
    description:
      "Update one visible field in the Create Assistant modal. The modal must be open before this tool is used.",
    parameters: {
      type: "object",
      additionalProperties: false,
      required: ["field", "value"],
      properties: {
        field: {
          type: "string",
          enum: assistantFields,
          description: "The form field to update.",
        },
        value: {
          type: "string",
          description:
            "The new field value. Voice must be Nova, Cedar, Luna, or Atlas. Language must be English, Spanish, French, or German.",
        },
      },
    },
  },
] as const;

export function isSection(value: unknown): value is DashboardSection {
  return typeof value === "string" && sections.includes(value as DashboardSection);
}

export function isTheme(value: unknown): value is DashboardTheme {
  return typeof value === "string" && themes.includes(value as DashboardTheme);
}

export function isAssistantField(value: unknown): value is AssistantField {
  return (
    typeof value === "string" && assistantFields.includes(value as AssistantField)
  );
}

export function isVoice(value: unknown): value is AssistantVoice {
  return typeof value === "string" && voices.includes(value as AssistantVoice);
}

export function isLanguage(value: unknown): value is AssistantLanguage {
  return typeof value === "string" && languages.includes(value as AssistantLanguage);
}
