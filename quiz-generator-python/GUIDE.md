# Build an AI Quiz Generator

AI Quiz Generator — turn any article, blog post, or documentation page into a multiple-choice quiz with answer key and explanations via Telnyx AI Inference.

## How It Works

```
  Article / text
        │
        ▼
  ┌──────────────────┐
  │ Your App          │
  └────────┬─────────┘
           │
           ├──► Telnyx AI Inference
           │
           ├──► Quiz generation (5 questions)
           │
           ▼
     Structured JSON (questions, choices, answers, explanations)
```

## Telnyx Products Used

- **AI Inference** — LLM inference with OpenAI-compatible API, runs on Telnyx infrastructure

## API Endpoints

- **AI Inference**: `POST /v2/ai/chat/completions` — [API reference](https://developers.telnyx.com/api/inference/chat-completions)

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)

## Step 1: Set Up the Project

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/quiz-generator-python
cp .env.example .env
pip install -r requirements.txt
```

Edit `.env` with your Telnyx credentials. Each variable links to where you find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Understand the Code

Everything lives in `app.py`. Here's what each piece does.

### Helper Functions

- **`call_inference()`** — Sends the quiz prompt to Telnyx AI Inference and returns the model's response. Uses `max_tokens=6000` and `timeout=90` to accommodate reasoning models that emit many tokens before content. Strips markdown fences from the response.
- **`build_quiz_prompt()`** — Constructs the prompt that asks the LLM to generate N multiple-choice questions from the provided text at the specified difficulty.

### System Prompt

The system prompt enforces:
- Exactly 5 questions (configurable via `num_questions`)
- 4 choices per question (A, B, C, D)
- One correct answer per question
- 1-2 sentence explanations
- Plausible distractors

### All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/quiz/generate` | Generate a quiz from text |
| `GET` | `/quizzes` | List quizzes |
| `GET` | `/quizzes/<id>` | Get a specific quiz |
| `GET` | `/quizzes/<id>/answers` | Get just the answer key |
| `GET` | `/health` | Health check |

The generate endpoint creates a structured quiz:

```python
@app.route("/quiz/generate", methods=["POST"])
def generate_quiz():
    data = request.get_json()
    text = data.get("text", "").strip()
    num_questions = data.get("num_questions", 5)
    difficulty = data.get("difficulty", "medium")
    prompt = build_quiz_prompt(text, num_questions, difficulty)
    result = call_inference([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ])
    quiz = json.loads(result)
    quiz["id"] = f"quiz-{int(time.time())}"
    quizzes[quiz["id"]] = quiz
    return jsonify(quiz), 201
```

## Step 3: Run It

```bash
python app.py
```

Server starts on `http://localhost:5000`.

## Step 4: Test It

**Health check:**

```bash
curl http://localhost:5000/health
```

**Generate a quiz:**

```bash
curl -X POST http://localhost:5000/quiz/generate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "The Telnyx Call Control API allows developers to programmatically control phone calls. You can answer, hangup, transfer, bridge, and record calls. The API is event-driven, meaning you receive webhooks when call events happen.",
    "num_questions": 5,
    "difficulty": "medium"
  }' | python3 -m json.tool
```

**Fetch the answer key:**

```bash
curl http://localhost:5000/quizzes/quiz-<id>/answers | python3 -m json.tool
```

**List quizzes:**

```bash
curl http://localhost:5000/quizzes | python3 -m json.tool
```

## Going to Production

This example uses in-memory storage for simplicity. For production:

- **Database** — persist quizzes in PostgreSQL or Redis
- **Authentication** — add API key validation on your endpoints
- **Larger texts** — chunk long articles and generate questions per chunk
- **Question types** — add true/false, short answer, and fill-in-the-blank
- **Export** — export quizzes to JSON, CSV, or SCORM for LMS integration
- **Rate limiting** — protect your endpoints from abuse
- **Prompt engineering** — tune the prompt for specific subject domains

## Run

```bash
pip install -r requirements.txt
python app.py
```

## Resources

- [Source code and reference](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/quiz-generator-python/README.md)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [AI Inference docs](https://developers.telnyx.com/docs/inference)
- [Telnyx Portal](https://portal.telnyx.com)
