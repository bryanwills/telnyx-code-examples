import type { ToolAgent } from "./tool-agent.js";
import type { ActorNamespace } from "@telnyx/edge-runtime";
import type Telnyx from "telnyx";

export type ToolName = "send_sms" | "make_call" | "check_status";
export type SmsTransport = "demo" | "production";

export interface Env {
  TOOLS: ActorNamespace<ToolAgent>;
  TELNYX: Telnyx;
  DEMO_MODE?: string;
  SMS_TRANSPORT?: SmsTransport;
  DEMO_FROM_NUMBER?: string;
  DEMO_SENDER_NUMBER?: string;
  CALL_CONTROL_APP_ID?: string;
  MAX_TOOL_ITERATIONS?: string;
  MODEL?: string;
  SECRETS?: {
    get(binding: "TELNYX_PUBLIC_KEY"): Promise<string>;
  };
}

export interface ToolState extends Record<string, unknown> {
  from: string;
  to: string;
  iterations: number;
  lastReply: string;
  updatedAt: number;
}

export interface ReceiveMessageInput {
  text: string;
  from: string;
  to: string;
  eventId: string;
}

export interface ToolLogRow {
  [key: string]: string | number;
  id: number;
  tool_call_id: string;
  tool: ToolName;
  args: string;
  result: string;
  status: string;
  at: number;
}

export interface ConversationEvent {
  id: number;
  role: "user" | "assistant";
  content: string;
  at: number;
}

export interface ProcessLogRow {
  [key: string]: string | number | null;
  id: number;
  iteration: number;
  phase: string;
  tool_choice: string;
  finish_reason: string | null;
  tool_calls: string;
  note: string;
  at: number;
}

export interface ProcessLogEvent {
  id: number;
  iteration: number;
  phase: string;
  tool_choice: string;
  finish_reason: string | null;
  tool_calls: unknown;
  note: string;
  at: number;
}

export interface ToolEvent {
  id: number;
  tool_call_id: string;
  tool: ToolName;
  args: unknown;
  result: unknown;
  status: string;
  at: number;
}

export interface EventsResponse {
  toolEvents: ToolEvent[];
  conversation: ConversationEvent[];
  processLog: ProcessLogEvent[];
}

export interface TelnyxMessageWebhook {
  data: {
    id: string;
    event_type: string;
    occurred_at?: string;
    payload: {
      from: { phone_number: string };
      to: Array<{ phone_number: string }>;
      text: string;
    };
  };
}

export interface ChatToolCall {
  id: string;
  type: "function";
  function: {
    name: string;
    arguments: string;
  };
}

export interface ChatCompletionResponse {
  choices: Array<{
    message: {
      content: string | null;
      tool_calls?: ChatToolCall[];
    };
    finish_reason?: string;
  }>;
}

export interface TelnyxEdgeClient {
  messages: {
    send(message: { from: string; to: string; text: string }): Promise<{ data?: { id?: string } }>;
  };
  calls: {
    dial(call: {
      connection_id: string;
      from: string;
      to: string;
      command_id?: string;
    }): Promise<{
      data: {
        call_control_id?: string;
        call_leg_id?: string;
        call_session_id?: string;
        status?: string;
      };
    }>;
  };
  ai: {
    openai: {
      chat: {
        createCompletion(request: {
          model: string;
          messages: unknown[];
          tools?: unknown[];
          tool_choice?: "auto" | "none" | "required";
        }): Promise<ChatCompletionResponse>;
      };
    };
  };
}
