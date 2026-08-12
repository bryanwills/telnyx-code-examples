import type { QuizAgent } from "./quiz-agent";
import type { ActorNamespace } from "@telnyx/edge-runtime";
import type Telnyx from "telnyx";

export type Difficulty = "easy" | "medium" | "hard";
export type QuizPhase = "idle" | "asking" | "answering" | "done";
export type QuizRole = "question" | "answer" | "grade" | "final" | "system";

export interface Env {
  QUIZ: ActorNamespace<QuizAgent>;
  TELNYX: Telnyx;
  DEMO_MODE?: string;
  PRODUCTION_MODE?: string;
  SMS_TRANSPORT?: string;
  DEMO_FROM_NUMBER?: string;
  DEMO_SENDER_NUMBER?: string;
  MAX_QUESTIONS?: string;
  MODEL?: string;
  SECRETS: {
    get(binding: "TELNYX_PUBLIC_KEY"): Promise<string>;
  };
}

export interface QuizState extends Record<string, unknown> {
  phase: QuizPhase;
  score: number;
  difficulty: Difficulty;
  turn: number;
  currentQuestion: string;
  currentAnswer: string;
  from: string;
  to: string;
  startedAt: number;
  updatedAt: number;
}

export interface ReceiveMessageInput {
  text: string;
  from: string;
  to: string;
  eventId: string;
}

export interface QuizEvent {
  id: number;
  sender: string;
  turn: number;
  role: QuizRole;
  text: string;
  score: number;
  difficulty: Difficulty;
  correct: boolean;
  at: number;
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
