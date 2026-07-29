---
name: quiz-generator
title: "AI Quiz Generator"
description: "AI Quiz Generator — turn any article or text into a multiple-choice quiz with answer key and explanations via Telnyx AI Inference."
language: python
framework: flask
telnyx_products: [AI Inference]
---

# AI Quiz Generator

AI Quiz Generator — turn any article, blog post, or documentation page into a multiple-choice quiz with answer key and explanations via Telnyx AI Inference.

## Telnyx API Endpoints Used

- **AI Inference**: `POST /v2/ai/chat/completions` — [API reference](https://developers.telnyx.com/api/inference/chat-completions)

## Architecture

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

## Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Type | Example | Required | Description | Where to get it |
|----------|------|---------|----------|-------------|-----------------|
| `TELNYX_API_KEY` | `string` | `KEY0123456789ABCDEF` | **yes** | Telnyx API v2 key | [Portal](https://portal.telnyx.com/api-keys) |
| `AI_MODEL` | `string` | `moonshotai/Kimi-K2.6` | no | Telnyx AI Inference model name | [Portal](https://developers.telnyx.com/docs/inference/models) |
| `PORT` | `integer` | `5000` | no | HTTP server port | — |

## Setup

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/quiz-generator-python
cp .env.example .env    # ← fill in your credentials
pip install -r requirements.txt
python app.py           # starts on http://localhost:5000
```

## API Reference

### `POST /quiz/generate`

Generate a multiple-choice quiz from text.

```bash
curl -X POST http://localhost:5000/quiz/generate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "The Telnyx Call Control API allows developers to programmatically control phone calls...",
    "num_questions": 5,
    "difficulty": "medium"
  }'
```

**Response:**

```json
{
  "id": "quiz-1750280400",
  "title": "Telnyx Call Control API Fundamentals",
  "description": "Test your understanding of the Telnyx Call Control API.",
  "difficulty": "medium",
  "questions": [
    {
      "id": 1,
      "question": "What setup is required to receive event notifications?",
      "choices": {"A": "Assign number to Call Control App", "B": "Enable SMS", "C": "Install softphone", "D": "Register with SIP"},
      "correct_answer": "A",
      "explanation": "You need a phone number assigned to a Call Control Application with a webhook URL."
    }
  ],
  "generated_at": "2026-07-29T10:02:29Z",
  "text_length": 723
}
```

### `GET /quizzes`

List all generated quizzes.

```bash
curl http://localhost:5000/quizzes
```

### `GET /quizzes/<id>`

Fetch a specific quiz.

```bash
curl http://localhost:5000/quizzes/quiz-1750280400
```

### `GET /quizzes/<id>/answers`

Fetch just the answer key with explanations.

```bash
curl http://localhost:5000/quizzes/quiz-1750280400/answers
```

**Response:**

```json
{
  "quiz_id": "quiz-1750280400",
  "answers": [
    {"id": 1, "correct_answer": "A", "explanation": "You need a phone number assigned to a Call Control Application."},
    {"id": 2, "correct_answer": "B", "explanation": "Outbound calls use POST /calls endpoint."}
  ]
}
```

### `GET /health`

Returns service health.

```bash
curl http://localhost:5000/health
```

**Response:**

```json
{
  "status": "ok",
  "quizzes": 0,
  "version": "1.0.0"
}
```

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Invalid or missing API key | Verify `TELNYX_API_KEY` in `.env` matches your key in the [Portal](https://portal.telnyx.com/api-keys) |
| `422 Unprocessable Entity` | Missing or malformed request fields | Check the request body against the API Reference above |
| Slow / empty response | Wrong model name | Verify `AI_MODEL` at [developers.telnyx.com](https://developers.telnyx.com/docs/inference/models) |
| `raw` returned instead of JSON | Model didn't return parseable JSON | Retry with shorter text or pin a stronger model |
| Timeout | Reasoning model needs more tokens | 5 questions can take 60-90s with Kimi-K2.6; be patient |

## Related Examples

- [AI Changelog Generator (Python)](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/changelog-generator-python/README.md)
- [AI Error Explainer (Python)](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/error-explainer-python/README.md)
- [AI SQL Natural Language (Python)](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/sql-natural-language-python/README.md)
- [Semantic Search for Support Tickets (Python)](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/semantic-search-python/README.md)

## Agent Discovery

This example is part of the [Telnyx Code Examples](https://github.com/team-telnyx/telnyx-code-examples) catalog.

- **Agent signup**: [telnyx.com/agent-signup.md](https://telnyx.com/agent-signup.md) — automated account provisioning via agent mail; get an API key with no human intervention
- **Agent CLI**: [github.com/team-telnyx/ai/tree/main/cli](https://github.com/team-telnyx/ai/tree/main/cli) — composite commands for agents ([commands reference](https://github.com/team-telnyx/ai/tree/main/cli/src/commands))
- **Agent skills**: [github.com/team-telnyx/ai/tree/main/skills](https://github.com/team-telnyx/ai/tree/main/skills)
- **Telnyx AI repo**: [github.com/team-telnyx/ai](https://github.com/team-telnyx/ai)
- **LLM-optimized docs**: [`llms-full.txt`](https://developers.telnyx.com/llms-full.txt)
- **Example index**: [`llms.txt`](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/llms.txt)
- **Telnyx CLI (human)**: [developers.telnyx.com/development/cli](https://developers.telnyx.com/development/cli) — `go install github.com/team-telnyx/telnyx-cli/cmd/telnyx@latest`

## Resources

- [AI Inference Guide](https://developers.telnyx.com/docs/inference)
- [Chat Completions API Reference](https://developers.telnyx.com/api/inference/chat-completions)
- [Available Inference Models](https://developers.telnyx.com/docs/inference/models)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Telnyx Portal](https://portal.telnyx.com)

## Why Telnyx

Telnyx is an **AI Communications Infrastructure** platform — voice, messaging, SIP, AI, and IoT on one private, global network.
