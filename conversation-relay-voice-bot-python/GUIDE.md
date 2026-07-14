# Conversation Relay Voice Bot — Build Guide

Forward live phone calls to any existing text-in/text-out AI chatbot
using Telnyx Conversation Relay. Your chatbot needs no changes — Telnyx
handles the telephony audio (STT + TTS + call control), and this bridge
app exchanges only text with your bot over an OpenAI-compatible API.

## What It Does

A caller dials your Telnyx number. Telnyx answers, transcribes their
speech to text, and sends the text to this bridge over a WebSocket. The
bridge forwards the text to your existing chatbot
(`/v1/chat/completions`). The chatbot's text reply goes back through
the bridge to Telnyx, which speaks it to the caller.

The chatbot doesn't know the input came from a phone. Its logic,
personality, tools, and knowledge base stay exactly the same.

## How It Works

```
  Caller speaks into phone
        │
        ▼
  ┌─────────────────────────────┐
  │ Telnyx (Conversation Relay) │  STT + TTS + call control
  │  transcribes speech → text   │
  └──────────────┬──────────────┘
                 │  WebSocket text frame
                 ▼
  ┌─────────────────────────────┐
  │  This bridge app (app.py)    │  ~140 lines of glue
  │  forwards text to your bot   │
  └──────────────┬──────────────┘
                 │  POST /v1/chat/completions
                 ▼
  ┌─────────────────────────────┐
  │  Your existing AI chatbot    │  ← NO CHANGES
  │  returns a text reply        │
  └──────────────┬──────────────┘
                 │  text reply
                 ▼
  ┌─────────────────────────────┐
  │  Bridge sends text frame     │
  └──────────────┬──────────────┘
                 │
                 ▼
  Telnyx TTS speaks the reply to the caller
```

## Telnyx Products Used

- **Conversation Relay** — text-over-WebSocket bridge between a phone call and your app. [Docs](https://developers.telnyx.com/docs/conversation-relay) | [WebSocket API](https://telnyx.mintlify.app/api-reference/websockets/conversationrelay-websocket-channel)
- **Voice** — answers the inbound call and hands it to Conversation Relay via TeXML `<Connect><ConversationRelay>`

## API Endpoints

- **TeXML Voice**: `GET|POST /texml/inbound` returns the TeXML that connects the call to Conversation Relay
- **Conversation Relay WebSocket**: `WS /ws/conversation-relay` — Telnyx connects and exchanges text frames
- **Conversation Relay callback**: `GET|POST /callbacks/conversation-relay` — logged, returns 204
- **Health**: `GET /health` — service status + active sessions
- **State**: `GET /api/state` — in-memory session map (debug only)
- **Events**: `GET /events` — SSE stream for live debugging

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)
- [Phone number](https://portal.telnyx.com/numbers/my-numbers) with voice enabled
- [TeXML Application](https://portal.telnyx.com/voice/texml-apps) pointing at your public `/texml/inbound` URL
- An existing OpenAI-compatible chatbot endpoint (e.g. Clawdbot/Nyx gateway, OpenAI API, vLLM, Ollama)
- [ngrok](https://ngrok.com) for exposing your local server

## Step 1: Set Up the Project

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/conversation-relay-voice-bot-python
cp .env.example .env
pip install -r requirements.txt
```

Edit `.env` with:
- `TELNYX_API_KEY` — your Telnyx API key
- `CHATBOT_BASE_URL` — your chatbot's OpenAI-compatible endpoint (e.g. `http://localhost:18789`)
- `CHATBOT_TOKEN` — auth token for your chatbot gateway (if any)
- `CHATBOT_MODEL` — model name your chatbot expects (e.g. `openclaw`)
- `TELNYX_PUBLIC_BASE_URL` — your ngrok HTTPS URL (leave blank to auto-detect)
- `VOICE` — Telnyx TTS voice (default `Telnyx.Natural.abbie`)
- `LANGUAGE` — BCP-47 language tag (default `en`)

## Step 2: Understand the Code

Everything lives in `app.py` (~140 lines). The interesting bits:

### `/texml/inbound`

Returns the TeXML that hands the call to Conversation Relay. The
`<ConversationRelay url=".../ws/conversation-relay"/>` element tells
Telnyx where to open the WebSocket.

### `/ws/conversation-relay`

The WebSocket handler. Receives `setup`/`prompt`/`dtmf`/`interrupt`
frames from Telnyx, forwards each prompt to the chatbot, and streams
the reply back as `text` frames. Maintains per-call session state so
the chatbot sees the full conversation history.

### Chatbot forwarding

Each prompt is sent to `${CHATBOT_BASE_URL}/v1/chat/completions` with
the session's accumulated message history. The reply is streamed token
by token back to Telnyx as Conversation Relay `text` frames, so the
caller hears the reply as it's generated.

## Step 3: Run It

```bash
python app.py
```

Server starts on `http://0.0.0.0:8000`.

Expose it:

```bash
ngrok http 8000
```

Set the TeXML Application voice URL to `https://<id>.ngrok.app/texml/inbound`.

Set `TELNYX_PUBLIC_BASE_URL=https://<id>.ngrok.app` in `.env` so the
TeXML response points at the right WebSocket URL.

## Step 4: Test It

**Health check:**

```bash
curl http://localhost:8000/health
```

**Call the Telnyx number** and talk to it. The chatbot's text replies
get spoken back to you by Telnyx TTS.

**Inspect state:**

```bash
curl http://localhost:8000/api/state | python3 -m json.tool
```

**Watch events:**

```bash
curl -N http://localhost:8000/events
```

## Going to Production

This example keeps sessions in memory. For production:

- **Persistent sessions** — store chat history in Redis or Postgres so
  calls survive restarts
- **Auth on the WebSocket** — verify the inbound WebSocket is from
  Telnyx (Conversation Relay sends a signed header)
- **Rate limiting** — cap prompts per call and per number
- **Streaming** — if your chatbot supports streaming, stream tokens to
  Telnyx as they arrive so the caller hears the reply in real time
- **Multi-model** — route different callers to different chatbot models
  based on the called number or caller ID

## Run

```bash
pip install -r requirements.txt
python app.py
```

## Resources

- [Source code and reference](https://github.com/team-telnyx/telnyx-code-examples/tree/main/conversation-relay-voice-bot-python)
- [Conversation Relay docs](https://developers.telnyx.com/docs/conversation-relay)
- [Conversation Relay WebSocket API](https://telnyx.mintlify.app/api-reference/websockets/conversationrelay-websocket-channel)
- [TeXML docs](https://developers.telnyx.com/docs/voice/texml)
- [Telnyx Portal](https://portal.telnyx.com)
