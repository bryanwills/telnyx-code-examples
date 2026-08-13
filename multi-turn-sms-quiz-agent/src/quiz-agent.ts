import { Agent } from "@telnyx/edge-runtime";
import type {
  Difficulty,
  Env,
  QuizEvent,
  QuizRole,
  QuizState,
  ReceiveMessageInput,
} from "./types";

const QUESTION_PROMPT = (difficulty: Difficulty) => `You are writing a clear, friendly quiz for beginners learning Telnyx Edge Compute, the Agent SDK, StatefulActors, durable state, SQL storage, Telnyx Messaging, and Telnyx Inference.

Generate exactly one ${difficulty} multiple-choice question.

Return only valid JSON:
{"question":"Question text\\nA) first choice\\nB) second choice\\nC) third choice","answer":"correct letter and short answer","hint":"one short hint"}

Rules:
- Keep the question SMS-friendly and easy to read.
- Use simple, concrete real-world examples that are easy to visualize.
- Good analogy themes: storage units, moving boxes, lockers, mail and delivery, keys, filing systems, rooms or spaces, saving and retrieving items.
- Keep analogies short. Do not turn the question into a long story.
- Keep the reading level simple without sounding childish or corporate.
- Still teach the real concept accurately.
- Avoid jargon unless the answer choice explains it plainly.
- Avoid childish analogies involving kids, toys, games, or backpacks.
- Avoid corporate analogies involving coworkers, meetings, project boards, office workflows, or customer profiles.
- Make incorrect answers plausible. They should test understanding, not be obviously silly.
- Make easy questions concrete, medium questions compare two ideas, and hard questions ask what happens in a small scenario.
- Put each answer choice on its own line.
- Use uppercase A), B), and C) labels.
- Make the correct answer unambiguous.
- Do not include markdown fences or extra text.`;

const GRADE_PROMPT = (question: string, correctAnswer: string, userAnswer: string) => `You are grading one quiz answer.

Question:
${question}

Correct answer:
${correctAnswer}

User answer:
${userAnswer}

Return only valid JSON:
{"correct":true,"explanation":"one SMS-friendly sentence"}

Rules:
- Accept either the correct letter or an equivalent short phrase.
- Be strict if the answer is unrelated.
- Explain the answer in plain language using a short concrete analogy when helpful.
- Do not sound childish or corporate.
- Do not include markdown fences or extra text.`;

const BUMP: Record<Difficulty, Difficulty> = {
  easy: "medium",
  medium: "hard",
  hard: "hard",
};

const DROP: Record<Difficulty, Difficulty> = {
  easy: "easy",
  medium: "easy",
  hard: "medium",
};

interface GeneratedQuestion {
  question: string;
  answer: string;
  hint: string;
}

interface GradeResult {
  correct: boolean;
  explanation: string;
}

type ChatMessage = { role: "system" | "user" | "assistant"; content: string };
type TelnyxEdgeClient = {
  messages: {
    send(message: { from: string; to: string; text: string }): Promise<unknown>;
  };
  ai: {
    openai: {
      chat: {
        createCompletion(request: {
          model: string;
          messages: ChatMessage[];
        }): Promise<{ choices: Array<{ message: { content: string } }> }>;
      };
    };
  };
};

const DEFAULT_QUESTION: GeneratedQuestion = {
  question: "A StatefulActor is like a storage unit for one texter. What can the quiz leave there and find again later?\nA) Score and current question\nB) A message for every other texter\nC) A temporary reply that disappears after sending",
  answer: "A) Your score and current question",
  hint: "Durable state is saved information you can come back to.",
};

function shouldSendSms(env: Env): boolean {
  return env.SMS_TRANSPORT !== "demo";
}

function maxQuestions(env: Env): number {
  const parsed = Number(env.MAX_QUESTIONS || "5");
  if (!Number.isFinite(parsed)) return 5;
  return Math.max(1, Math.min(10, Math.floor(parsed)));
}

function extractJsonObject(raw: string): string {
  const trimmed = raw.trim();
  if (trimmed.startsWith("{") && trimmed.endsWith("}")) return trimmed;
  return trimmed.match(/\{[\s\S]*\}/)?.[0] || "{}";
}

function parseQuestion(raw: string): GeneratedQuestion {
  try {
    const parsed = JSON.parse(extractJsonObject(raw)) as Partial<GeneratedQuestion>;
    const question = typeof parsed.question === "string" ? parsed.question.trim() : "";
    const answer = typeof parsed.answer === "string" ? parsed.answer.trim() : "";
    const hint = typeof parsed.hint === "string" ? parsed.hint.trim() : "";
    if (!question || !answer) return DEFAULT_QUESTION;
    return {
      question: normalizeChoices(question).slice(0, 1200),
      answer: answer.slice(0, 240),
      hint: hint.slice(0, 240),
    };
  } catch {
    return DEFAULT_QUESTION;
  }
}

function normalizeChoices(text: string): string {
  return text
    .replace(/\s+([abc])\)\s*/gi, (_, letter: string) => `\n${letter.toUpperCase()}) `)
    .replace(/^([abc])\)/gim, (_, letter: string) => `${letter.toUpperCase()})`)
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function parseGrade(raw: string): GradeResult {
  try {
    const parsed = JSON.parse(extractJsonObject(raw)) as Partial<GradeResult>;
    return {
      correct: parsed.correct === true,
      explanation: typeof parsed.explanation === "string" && parsed.explanation.trim()
        ? parsed.explanation.trim().slice(0, 240)
        : "The stored answer did not match that response.",
    };
  } catch {
    return {
      correct: false,
      explanation: "I could not confidently grade that one, so I marked it incorrect.",
    };
  }
}

function isChatRole(role: string): role is ChatMessage["role"] {
  return role === "system" || role === "user" || role === "assistant";
}

function toChatMessages(messages: Array<{ role: string; content: string }>): ChatMessage[] {
  return messages
    .filter((message): message is ChatMessage => isChatRole(message.role))
    .map((message) => ({ role: message.role, content: message.content }));
}

function telnyx(env: Env): TelnyxEdgeClient {
  return env.TELNYX as unknown as TelnyxEdgeClient;
}

function startMessage(total: number): string {
  return `Welcome to the Edge Compute quiz. ${total} questions. The quiz adjusts difficulty as you answer.`;
}

function gradeText(grade: GradeResult, score: number, turn: number, total: number, nextDifficulty: Difficulty): string {
  const prefix = grade.correct ? "Nice, you got it." : "Almost, try this idea.";
  const next = turn >= total ? "" : ` Next difficulty: ${nextDifficulty}.`;
  return `${prefix} ${grade.explanation} Score: ${score}/${turn}.${next}`;
}

function finalText(score: number, total: number, difficulty: Difficulty): string {
  return `Quiz complete. Final score: ${score}/${total}. Final difficulty: ${difficulty}. Text "start" to play again.`;
}

export class QuizAgent extends Agent<Env, QuizState> {
  protected override initialState(): QuizState {
    return {
      phase: "idle",
      score: 0,
      difficulty: "easy",
      turn: 0,
      currentQuestion: "",
      currentAnswer: "",
      from: "",
      to: "",
      startedAt: 0,
      updatedAt: 0,
    };
  }

  async receive({ text, from, to, eventId }: ReceiveMessageInput): Promise<void> {
    this.ensureTables();

    try {
      this.ctx.storage.sql.exec(
        "INSERT INTO webhook_events(event_id, at) VALUES (?, ?)",
        eventId,
        Date.now(),
      );
    } catch {
      return;
    }

    const state = await this.getState();
    const normalized = text.trim().toLowerCase();
    const isStart = normalized === "start" || normalized === "start quiz";
    const now = Date.now();

    if (isStart || state.phase === "idle" || state.phase === "done") {
      await this.setState({
        phase: "asking",
        score: 0,
        difficulty: "easy",
        turn: 0,
        currentQuestion: "",
        currentAnswer: "",
        from,
        to,
        startedAt: now,
        updatedAt: now,
      });
      await this.logEvent(from, 0, "system", startMessage(maxQuestions(this.env)), 0, "easy", 0, now);
    } else if (state.phase === "answering" && state.currentQuestion) {
      await this.setState({ phase: "answering", from, to, updatedAt: now });
      await this.logEvent(from, state.turn, "answer", text.trim(), state.score, state.difficulty, 0, now);
    } else {
      await this.setState({ phase: "asking", from, to, updatedAt: now });
    }

    await this.messages.add("user", text);
    await this.queue("process");
  }

  async process(): Promise<void> {
    this.ensureTables();

    const state = await this.getState();
    if (!state.from || !state.to) return;

    if (state.phase === "asking") {
      await this.askQuestion(state);
      return;
    }

    if (state.phase === "answering") {
      const last = await this.messages.last();
      if (!last || last.role !== "user" || !state.currentQuestion || !state.currentAnswer) return;
      await this.gradeAnswer(state, last.content);
    }
  }

  async getEvents(limit = 50): Promise<QuizEvent[]> {
    this.ensureTables();

    return this.ctx.storage.sql
      .exec<{
        id: number;
        sender: string;
        turn: number;
        role: QuizRole;
        text: string;
        score: number;
        difficulty: Difficulty;
        correct: number;
        at: number;
      }>(
        `SELECT id, sender, turn, role, text, score, difficulty, correct, at
         FROM quiz_log
         ORDER BY id DESC
         LIMIT ?`,
        Math.max(1, Math.min(100, limit)),
      )
      .toArray()
      .map((row) => ({ ...row, correct: row.correct === 1 }));
  }

  async getStatus(): Promise<QuizState> {
    return this.getState();
  }

  private async askQuestion(state: QuizState): Promise<void> {
    const response = await telnyx(this.env).ai.openai.chat.createCompletion({
      model: this.env.MODEL || "zai-org/GLM-5.2",
      messages: [
        { role: "system", content: QUESTION_PROMPT(state.difficulty) },
        ...toChatMessages(await this.messages.toOpenAI()),
      ],
    });

    const raw = response.choices[0]?.message?.content || "{}";
    const generated = parseQuestion(raw);
    const turn = state.turn + 1;
    const total = maxQuestions(this.env);
    const questionText = `Q${turn}/${total} (${state.difficulty})\n${generated.question}`;
    const now = Date.now();

    await this.setState({
      phase: "answering",
      turn,
      currentQuestion: generated.question,
      currentAnswer: generated.answer,
      updatedAt: now,
    });

    await this.logEvent(state.from, turn, "question", questionText, state.score, state.difficulty, 0, now);
    await this.messages.add("assistant", questionText);

    if (shouldSendSms(this.env)) {
      await telnyx(this.env).messages.send({ from: state.to, to: state.from, text: questionText });
    }
  }

  private async gradeAnswer(state: QuizState, userAnswer: string): Promise<void> {
    const response = await telnyx(this.env).ai.openai.chat.createCompletion({
      model: this.env.MODEL || "zai-org/GLM-5.2",
      messages: [
        {
          role: "system",
          content: GRADE_PROMPT(state.currentQuestion, state.currentAnswer, userAnswer),
        },
      ],
    });

    const grade = parseGrade(response.choices[0]?.message?.content || "{}");
    const total = maxQuestions(this.env);
    const score = state.score + (grade.correct ? 1 : 0);
    const difficulty = grade.correct ? BUMP[state.difficulty] : DROP[state.difficulty];
    const text = gradeText(grade, score, state.turn, total, difficulty);
    const now = Date.now();

    await this.logEvent(state.from, state.turn, "grade", text, score, difficulty, grade.correct ? 1 : 0, now);
    await this.messages.add("assistant", text);

    if (shouldSendSms(this.env)) {
      await telnyx(this.env).messages.send({ from: state.to, to: state.from, text });
    }

    if (state.turn >= total) {
      const done = finalText(score, total, difficulty);
      await this.setState({
        phase: "done",
        score,
        difficulty,
        currentQuestion: "",
        currentAnswer: "",
        updatedAt: now,
      });
      await this.logEvent(state.from, state.turn, "final", done, score, difficulty, 0, now);
      await this.messages.add("assistant", done);

      if (shouldSendSms(this.env)) {
        await telnyx(this.env).messages.send({ from: state.to, to: state.from, text: done });
      }
      return;
    }

    await this.setState({
      phase: "asking",
      score,
      difficulty,
      currentQuestion: "",
      currentAnswer: "",
      updatedAt: now,
    });
    await this.queue("process");
  }

  private async logEvent(
    sender: string,
    turn: number,
    role: QuizRole,
    text: string,
    score: number,
    difficulty: Difficulty,
    correct: number,
    at: number,
  ): Promise<void> {
    this.ctx.storage.sql.exec(
      `INSERT INTO quiz_log(sender, turn, role, text, score, difficulty, correct, at)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
      sender,
      turn,
      role,
      text,
      score,
      difficulty,
      correct,
      at,
    );
  }

  private ensureTables(): void {
    this.ctx.storage.sql.exec(
      `CREATE TABLE IF NOT EXISTS webhook_events(
         event_id TEXT PRIMARY KEY,
         at INTEGER NOT NULL
       )`,
    );
    this.ctx.storage.sql.exec(
      `CREATE TABLE IF NOT EXISTS quiz_log(
         id INTEGER PRIMARY KEY AUTOINCREMENT,
         sender TEXT NOT NULL,
         turn INTEGER NOT NULL,
         role TEXT NOT NULL,
         text TEXT NOT NULL,
         score INTEGER NOT NULL,
         difficulty TEXT NOT NULL,
         correct INTEGER NOT NULL,
         at INTEGER NOT NULL
       )`,
    );
  }
}
