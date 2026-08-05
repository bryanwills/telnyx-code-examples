---
name: ai-multilingual-code-switching-agent
title: "Multilingual Code-Switching Voice Agent"
description: "A phone-based Voice AI agent that detects the caller's language on every turn and replies in the same language. Switch mid-conversation and the agent follows. One assistant, five languages, no stitching separate STT, LLM, and TTS vendors."
language: python
framework: flask
telnyx_products: [Voice AI, AI Inference, Text-to-Speech]
channel: [voice]
---

# Multilingual Code-Switching Voice Agent

A phone-based Voice AI agent that fluidly code-switches between languages mid-conversation. The caller can speak English, Spanish, Portuguese, Hindi, or Mandarin, switch language mid-sentence, or mix two languages across turns — the agent detects the active language, replies in kind, and stays natural throughout.

Pure Voice AI Assistant — the built-in STT (Deepgram nova-3), LLM (Kimi-K2.6), and TTS (voice ultra katie) handle the entire conversation. No manual Call Control pipeline, no application-layer STT/LLM/TTS stitching.

## Telnyx API Endpoints Used

- **AI Assistants — Create**: `POST /v2/ai/assistants` — [API reference](https://developers.telnyx.com/api/ai/create-assistant)
- **AI Assistants — Update**: `POST /v2/ai/assistants/{assistant_id}` — for updating instructions, transcription, telephony settings
- **TeXML AI Calls**: `POST /v2/texml/ai_calls/{texml_app_id}` — trigger outbound calls with `AIAssistantId`
- **Phone Numbers — List available / Create order**: `GET /v2/available_phone_numbers`, `POST /v2/number_orders`
- **TeXML Applications — Create**: `POST /v2/texml_applications` (provides `connection_id` for phone assignment)
- **Phone Numbers — Update**: `PATCH /v2/phone_numbers/{phone_number}` (assign to TeXML app)
- **Outbound Voice Profiles — Update**: `PATCH /v2/outbound_voice_profiles/{id}` (whitelist destination countries if testing outbound)

## Architecture

```
  Inbound phone call  ──►  Telnyx Voice AI Assistant
                                │
                                ▼
                       ┌────────────────────────┐
                       │ STT (deepgram/nova-3)   │  → detects spoken language
                       │ LLM (instructions)       │  → replies in same language,
                       │                          │     switches on caller's switch
                       │ TTS (voice ultra katie) │  → speaks reply in target language
                       └────────┬───────────────┘
                                │
                                ▼
                          Caller hears reply
                          in their language

  Flask app:
    provision_assistant.py  → creates/reuses the assistant
    app.py                  → /assistant/create, /call/trigger, /webhooks/call, /health, GET /
    GET /                   → browser UI with "Call me" button
```

The code-switching behavior lives entirely in the assistant's `instructions` — there is no manual STT/LLM/TTS pipeline. The Flask app handles provisioning and triggering calls; the actual conversation runs on Telnyx.

## How It Works

1. `provision_assistant.py` creates a Telnyx AI Assistant with `voice ultra katie` in the instructions, `deepgram/nova-3` transcription with `language: "multi"` for multilingual support, and telephony settings pointing to a TeXML application.
2. The caller dials the purchased Telnyx number (inbound) or the Flask app triggers an outbound call via `POST /v2/texml/ai_calls/<texml_app_id>`.
3. The assistant's STT (Deepgram nova-3) transcribes the caller's speech in whatever language they use.
4. The LLM follows the instructions: "detect the language they are speaking on every turn. reply in the same language the caller is using right now. if the caller switches language mid-conversation or mid-sentence, switch with them."
5. The TTS renders the reply in the detected language using `voice ultra katie`.
6. The Flask webhook endpoint logs events for observability but does not intervene in the conversation.

## Why Telnyx

Telnyx AI Communications Infrastructure lets one Voice AI Assistant combine telephony, STT, LLM, and TTS behind a single phone number. Deepgram nova-3 handles multilingual transcription. The LLM follows instructions to reply in the caller's current language. Ultra TTS renders the reply in that language automatically. No stitching separate STT, LLM, and TTS vendors in application code — the entire conversation runs on Telnyx.

## Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Type | Example | Required | Description | Where to get it |
|----------|------|---------|----------|-------------|-----------------|
| `TELNYX_API_KEY` | `string` | `KEY0123456789ABCDEF` | **yes** | Telnyx API v2 key | [Portal](https://portal.telnyx.com/api-keys) |
| `TELNYX_ASSISTANT_ID` | `string` | `assistant-xxxx-xxxx` | after provision | Created by `provision_assistant.py` | Run the script, copy output |
| `TELNYX_PHONE_NUMBER` | `string` | `+18005551234` | **yes** | Purchased Telnyx number | [Portal](https://portal.telnyx.com/numbers) |
| `TELNYX_CONNECTION_ID` | `string` | `1234-5678-...` | **yes** | TeXML application ID | [Portal](https://portal.telnyx.com/applications) |
| `AI_MODEL` | `string` | `moonshotai/Kimi-K2.6` | no | LLM model (native Telnyx, no external key) | [Models](https://developers.telnyx.com/docs/inference/models) |
| `TELNYX_PUBLIC_KEY` | `string` | | no | For webhook signature verification | [Portal](https://portal.telnyx.com/public-key) |
| `PORT` | `int` | `5050` | no | Flask port (default 5050) | — |

## Setup

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/ai-multilingual-code-switching-agent-python
cp .env.example .env    # ← fill in your credentials
pip install -r requirements.txt

# Step 1: Provision a phone number and TeXML app (see GUIDE.md)
# Step 2: Set TELNYX_CONNECTION_ID in .env
# Step 3: Create the assistant
python provision_assistant.py
# Copy the TELNYX_ASSISTANT_ID output into .env

# Step 4: Start the app
python app.py           # starts on http://127.0.0.1:5050
```

<details>
<summary>Programmatic / CLI setup</summary>

```bash
# Install CLI — https://developers.telnyx.com/development/cli
go install github.com/team-telnyx/telnyx-cli/cmd/telnyx@latest
telnyx auth login

# Provision resources
telnyx available-phone-numbers list --country US --features voice
telnyx number-orders create --phone-number +15551234567
```

For full API discovery, point your agent at [`llms-full.txt`](https://developers.telnyx.com/llms-full.txt).

</details>

## API Reference

See [`API.md`](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/ai-multilingual-code-switching-agent-python/API.md) for the full typed endpoint reference. Quick start:

```bash
# Create the assistant
curl -X POST http://localhost:5050/assistant/create

# Trigger an outbound call
curl -X POST http://localhost:5050/call/trigger \
  -H "Content-Type: application/json" \
  -d '{"to": "+13125550001"}'
```

## How to Test Code-Switching

1. Trigger a call (or dial the inbound number).
2. Say "Hola, ¿cómo estás?" → agent replies in Spanish.
3. Say "Now let's switch to English." → agent replies in English.
4. Say "Namaste, kaise ho?" → agent replies in Hindi.
5. Mix: "Hola, can you help me with my order?" → agent replies in the dominant language.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `401 Unauthorized` | Missing or invalid `TELNYX_API_KEY` | Set `TELNYX_API_KEY` in `.env` |
| `400` from `/call/trigger` | `TELNYX_ASSISTANT_ID` not set | Run `python provision_assistant.py` first, copy the ID into `.env` |
| `400` from `/call/trigger` | Phone number not in E.164 format | Use `+` prefix and country code (e.g. `+13125550001`) |
| `403` with code `D13` | Destination country not whitelisted | Add the country to your outbound voice profile's `whitelisted_destinations` |
| Agent does not switch languages | STT model not set to `deepgram/nova-3` | Verify `provision_assistant.py` sets `transcription.model = "deepgram/nova-3"` and `language = "multi"` |
| Agent replies in wrong language | LLM not following instructions | Keep instructions short and explicit. Test with clear single-language turns first |
| Voice sounds wrong in one language | `voice ultra katie` may not support all languages well | Test each language by calling and speaking. Ultra supports 36+ languages |
| Port 5000 already in use | macOS AirPlay Receiver holds port 5000 | App defaults to `PORT=5050` env var |

## Related Examples

- [`ai-language-learning-phone-tutor-python`](https://github.com/team-telnyx/telnyx-code-examples/tree/main/ai-language-learning-phone-tutor-python) — phone-based conversational AI tutor
- [`ai-real-time-translation-bridge-python`](https://github.com/team-telnyx/telnyx-code-examples/tree/main/ai-real-time-translation-bridge-python) — two-caller interpreter (different problem: translation between two people)
- [`three-way-ai-interpreter-python`](https://github.com/team-telnyx/telnyx-code-examples/tree/main/three-way-ai-interpreter-python) — three-way interpreter
- [`webrtc-ai-interpreter-live-calls-python`](https://github.com/team-telnyx/telnyx-code-examples/tree/main/webrtc-ai-interpreter-live-calls-python) — browser interpreter
- [`ai-assistant-phone-setup-python`](https://github.com/team-telnyx/telnyx-code-examples/tree/main/ai-assistant-phone-setup-python) — phone provisioning baseline
- [`ai-lab-results-notification-voice-python`](https://github.com/team-telnyx/telnyx-code-examples/tree/main/ai-lab-results-notification-voice-python) — reference for `voice ultra katie` + `provision_assistant.py` pattern

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

- AI Assistants API: [developers.telnyx.com/api-reference/assistants/create-an-assistant](https://developers.telnyx.com/api-reference/assistants/create-an-assistant)
- AI Assistants docs: [developers.telnyx.com/docs/inference/ai-assistants/no-code-voice-assistant](https://developers.telnyx.com/docs/inference/ai-assistants/no-code-voice-assistant)
- Transcription settings: [developers.telnyx.com/docs/inference/ai-assistants/transcription-settings](https://developers.telnyx.com/docs/inference/ai-assistants/transcription-settings)
- Telnyx Ultra TTS: [developers.telnyx.com/docs/voice/tts/providers/telnyx/ultra](https://developers.telnyx.com/docs/voice/tts/providers/telnyx/ultra)
- Ultra SSML emotions: [developers.telnyx.com/docs/voice/tts/providers/telnyx/ultra#ssml-emotions](https://developers.telnyx.com/docs/voice/tts/providers/telnyx/ultra#ssml-emotions)
- Repo CONTRIBUTING.md: [github.com/team-telnyx/telnyx-code-examples/blob/main/CONTRIBUTING.md](https://github.com/team-telnyx/telnyx-code-examples/blob/main/CONTRIBUTING.md)
