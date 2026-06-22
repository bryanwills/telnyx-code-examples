# Run LLM Inference with Telnyx and Node.js

Run large language model inference through the Telnyx Inference API using an OpenAI-compatible chat completions interface from Node.js. Works as both an HTTP server and a CLI tool.

## How It Works

```
  HTTP request / CLI arg
        │
        ▼
  ┌────────────────────┐
  │  Express app        │
  │  /inference/chat    │
  │  /inference/ask     │
  └─────────┬──────────┘
            │  POST /v2/ai/chat/completions
            ▼
  ┌────────────────────┐
  │  Telnyx Inference   │
  └─────────┬──────────┘
            │
            └──► completion text
```

## Telnyx Products Used

- **Inference** — run chat completions on Telnyx-hosted open models with an OpenAI-compatible API

## API Endpoints

- **Chat Completions**: `POST /v2/ai/chat/completions` -- [API reference](https://developers.telnyx.com/api/inference/inference-embedding/post-chat-completions)

## Prerequisites

- Node.js 18 or higher (the code uses the built-in global `fetch`)
- [Telnyx account](https://portal.telnyx.com/sign-up) with a funded balance
- [API key](https://portal.telnyx.com/api-keys)

## Step 1: Set Up the Project

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/run-llm-inference-nodejs
cp .env.example .env
npm install
```

Edit `.env` with your Telnyx credentials:

| Variable | Required | Description |
|----------|----------|-------------|
| `TELNYX_API_KEY` | **yes** | Your Telnyx API v2 key, used as the Bearer token |
| `AI_MODEL` | no | Default model slug (defaults to `meta-llama/Llama-3.3-70B-Instruct`) |
| `PORT` | no | HTTP port for server mode (defaults to `5000`) |

## Step 2: Understand the Code

Everything lives in `server.js`. Here's what each piece does.

### Configuration

The app loads `.env` via `dotenv`, reads `TELNYX_API_KEY`, `AI_MODEL`, and `PORT`, and points at the inference endpoint `https://api.telnyx.com/v2/ai/chat/completions`.

### Helper Functions

- **`chatCompletion(messages, options)`** — Posts to the Telnyx Inference API with the `model`, `messages`, `max_tokens` (default `500`), and `temperature` (default `0.7`). Throws `Inference API error: <status>` on a non-OK response, otherwise returns the parsed JSON.
- **`simpleAsk(question, systemPrompt)`** — Builds a `messages` array (optional system prompt first, then the question), calls `chatCompletion`, and returns `result.choices[0].message.content`.

### All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/inference/chat` | Full chat completion; returns the raw Telnyx response |
| `POST` | `/inference/ask` | Single question; returns just the answer text |
| `GET` | `/health` | Liveness check; returns the default model |

### Server vs. CLI mode

At the bottom of `server.js`, the app inspects `process.argv`. If you pass arguments other than `--serve`, it joins them into a question, runs `simpleAsk`, prints the answer, and exits. Otherwise it starts the Express server:

```js
if (process.argv.length > 2 && process.argv[2] !== "--serve") {
  const question = process.argv.slice(2).join(" ");
  simpleAsk(question)
    .then((answer) => console.log(`Answer: ${answer}`))
    .catch((err) => { console.error("Error:", err.message); process.exit(1); });
} else {
  app.listen(PORT, () => {
    console.log(`Inference server listening on port ${PORT}`);
  });
}
```

## Step 3: Run It

### As a server

```bash
node server.js
```

The server starts on `http://localhost:5000` (or your `PORT`).

### As a CLI tool

```bash
node server.js "What is the capital of France?"
```

This prints the model, the question, and the answer, then exits — no server needed.

## Step 4: Test It

**Health check:**

```bash
curl http://localhost:5000/health
```

**Ask a single question:**

```bash
curl -X POST http://localhost:5000/inference/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the capital of France?"}'
```

**Run a full chat completion:**

```bash
curl -X POST http://localhost:5000/inference/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Write a haiku about the ocean."}
    ],
    "max_tokens": 200,
    "temperature": 0.7
  }'
```

## Going to Production

- **Authentication** — add API key validation on your endpoints; do not expose them unauthenticated.
- **Timeouts and retries** — wrap the upstream `fetch` with a timeout and retry/backoff for transient failures.
- **Streaming** — for long completions, stream tokens to the client instead of buffering the full response.
- **Monitoring** — add structured logging and alert on `/health` and on `Inference API error` rates.
- **Rate limiting** — protect your endpoints from abuse and runaway token spend.

## Run

```bash
npm install
node server.js
```

Or as a one-off CLI question:

```bash
node server.js "Your question here"
```

## Resources

- [Source code and reference](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/run-llm-inference-nodejs/README.md)
- [Typed endpoint reference](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/run-llm-inference-nodejs/API.md)
- [Telnyx Inference Docs](https://developers.telnyx.com/docs/inference)
- [Chat Completions API reference](https://developers.telnyx.com/api/inference/inference-embedding/post-chat-completions)
- [Node.js SDK](https://developers.telnyx.com/development/sdk/node)
- [Telnyx Portal](https://portal.telnyx.com)
