## `POST /quiz/generate`

Generate a multiple-choice quiz from text.

### Request

```json
{
  "text": "Any article or text content...",
  "num_questions": 5,
  "difficulty": "medium"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | `string` | **yes** | The text to generate a quiz from (max 6000 chars) |
| `num_questions` | `integer` | no | Number of questions (default 5, max 20) |
| `difficulty` | `string` | no | `easy`, `medium`, or `hard` (default `medium`) |
| `title` | `string` | no | Custom quiz title |

### Response `201`

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
      "choices": {"A": "...", "B": "...", "C": "...", "D": "..."},
      "correct_answer": "A",
      "explanation": "You need a phone number assigned to a Call Control Application."
    }
  ],
  "generated_at": "2026-07-29T10:02:29Z",
  "text_length": 723
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/quiz/generate \
  -H "Content-Type: application/json" \
  -d '{"text":"Python is a programming language...","num_questions":3}'
```

---

## `GET /quizzes`

List all generated quizzes (most recent 50).

### Response `200`

```json
{
  "quizzes": [
    {
      "id": "quiz-1750280400",
      "title": "Telnyx Call Control API Fundamentals",
      "description": "Test your understanding...",
      "difficulty": "medium",
      "question_count": 5,
      "generated_at": "2026-07-29T10:02:29Z"
    }
  ]
}
```

**Try it:**

```bash
curl http://localhost:5000/quizzes
```

---

## `GET /quizzes/<id>`

Fetch a specific quiz by ID.

### Response `200`

```json
{
  "id": "quiz-1750280400",
  "title": "Telnyx Call Control API Fundamentals",
  "questions": [
    {"id": 1, "question": "...", "choices": {"A": "...", "B": "..."}, "correct_answer": "A", "explanation": "..."}
  ]
}
```

### Response `404`

```json
{"error": "quiz not found"}
```

**Try it:**

```bash
curl http://localhost:5000/quizzes/quiz-1750280400
```

---

## `GET /quizzes/<id>/answers`

Fetch just the answer key with explanations (no questions or choices).

### Response `200`

```json
{
  "quiz_id": "quiz-1750280400",
  "answers": [
    {"id": 1, "correct_answer": "A", "explanation": "You need a phone number assigned to a Call Control Application."},
    {"id": 2, "correct_answer": "B", "explanation": "Outbound calls use POST /calls endpoint."}
  ]
}
```

**Try it:**

```bash
curl http://localhost:5000/quizzes/quiz-1750280400/answers
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "quizzes": 0,
  "version": "1.0.0"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Error Handling

All endpoints return JSON. On error:

```json
{
  "error": "invalid request body"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `201` | Quiz created |
| `400` | Bad request — missing or invalid fields |
| `404` | Quiz not found |
| `500` | Server error |
