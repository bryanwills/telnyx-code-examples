import type { Conversation } from "./conversation.js";
import type { ActorNamespace } from "@telnyx/edge-runtime";
import type Telnyx from "telnyx";

export type SmsTransport = "demo" | "production";
export type Intent = "order" | "smalltalk" | "unknown";

export interface Env {
  CONVOS: ActorNamespace<Conversation>;
  TELNYX: Telnyx;
  DEMO_MODE?: string;
  SMS_TRANSPORT?: SmsTransport;
  DEMO_FROM_NUMBER?: string;
  DEMO_SENDER_NUMBER?: string;
  MODEL?: string;
  SECRETS?: {
    get(binding: "TELNYX_PUBLIC_KEY"): Promise<string>;
  };
}

export interface PendingOutbound {
  turn: number;
  reply: string;
  clientRef: string;
}

export interface ConvState extends Record<string, unknown> {
  from: string;
  to: string;
  turn: number;
  queuedTurn: number;
  processingTurn: number;
  lastSentTurn: number;
  pendingOutbound: PendingOutbound | null;
  lastIntent: Intent;
  at: number;
}

export interface ReceiveMessageInput {
  text: string;
  from: string;
  to: string;
  eventId: string;
}

export interface WebhookEventRow {
  event_id: string;
  at: number;
}

export interface ConversationRow {
  id: number;
  role: "user" | "assistant";
  content: string;
  at: number;
}

export interface ProcessLogRow {
  [key: string]: string | number;
  id: number;
  turn: number;
  phase: string;
  intent: string;
  note: string;
  at: number;
}

export interface ProcessLogEvent {
  id: number;
  turn: number;
  phase: string;
  intent: string;
  note: string;
  at: number;
}

export interface ConversationEvent {
  [key: string]: string | number;
  id: number;
  role: "user" | "assistant";
  content: string;
  at: number;
}

export interface EventsResponse {
  conversation: ConversationEvent[];
  processLog: ProcessLogEvent[];
  turnState: {
    turn: number;
    queuedTurn: number;
    processingTurn: number;
    lastSentTurn: number;
    pendingOutbound: PendingOutbound | null;
  };
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

export interface ChatCompletionResponse {
  choices: Array<{
    message: {
      content: string | null;
    };
    finish_reason?: string;
  }>;
}

export interface TelnyxEdgeClient {
  messages: {
    send(message: { from: string; to: string; text: string }): Promise<{ data?: { id?: string } }>;
  };
  ai: {
    openai: {
      chat: {
        createCompletion(request: {
          model: string;
          messages: Array<{ role: string; content: string }>;
        }): Promise<ChatCompletionResponse>;
      };
    };
  };
}
