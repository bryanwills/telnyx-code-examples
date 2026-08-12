import type { SentimentAgent } from "./sentiment-agent.js";

export interface ActorNamespace<T> {
  idFromName(name: string): T;
}

export type SentimentLabel = "positive" | "neutral" | "negative";

export interface Env {
  SENTIMENT: ActorNamespace<SentimentAgent>;
  TELNYX: {
    messages: {
      send(message: { from: string; to: string; text: string }): Promise<unknown>;
    };
    ai: {
      openai: {
        chat: {
          createCompletion(request: {
            model: string;
            messages: Array<{ role: "system" | "user" | "assistant"; content: string }>;
          }): Promise<{ choices: Array<{ message: { content: string } }> }>;
        };
      };
    };
  };
  DEMO_MODE?: string;
  PRODUCTION_MODE?: string;
  DEMO_FROM_NUMBER?: string;
  DEMO_SENDER_NUMBER?: string;
  OPS_ALERT_PHONE?: string;
  MODEL?: string;
  SECRETS?: {
    get(binding: "TELNYX_PUBLIC_KEY"): Promise<string>;
  };
}

export interface SentimentState extends Record<string, unknown> {
  from: string;
  to: string;
  lastLabel: string;
  lastAt: number;
}

export interface SentimentRow {
  id: number;
  sender: string;
  message: string;
  label: SentimentLabel;
  score: number;
  escalated: boolean;
  reply: string;
  at: number;
}

export interface ReceiveMessageInput {
  text: string;
  from: string;
  to: string;
  eventId: string;
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
