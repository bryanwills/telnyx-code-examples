# Build a Multilingual Code-Switching Voice Agent with Telnyx

A phone-based Voice AI agent that detects the caller's language on every turn and replies in the same language. Switch mid-conversation and the agent follows. One assistant, five languages, no stitching separate STT, LLM, and TTS vendors.

## How It Works

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
```

The code-switching behavior lives entirely in the assistant's `instructions`. There is no manual STT/LLM/TTS pipeline — the entire conversation runs on Telnyx.

## Telnyx Products Used

- **Voice AI** — AI Assistant with telephony, multilingual STT, LLM, and TTS on one platform
- **AI Inference** — LLM inference via `moonshotai/Kimi-K2.6` (native Telnyx model, no external API key)
- **Text-to-Speech** — `voice ultra katie` renders replies in the caller's language

## API Endpoints

- **AI Assistants — Create**: `POST /v2/ai/assistants` — [API reference](https://developers.telnyx.com/api-reference/assistants/create-an-assistant)
- **TeXML AI Calls**: `POST /v2/texml/ai_calls/{texml_app_id}` — trigger outbound calls with `AIAssistantId`
- **Transcription settings**: `deepgram/nova-3` with `language: "multi"` for multilingual support — [docs](https://developers.telnyx.com/docs/inference/ai-assistants/transcription-settings)

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- A Telnyx API v2 key from the [Portal](https://portal.telnyx.com/api-keys)

## Step 1 — Provision a phone number and TeXML app

This example requires a purchased Telnyx phone number assigned to a TeXML application. You can do this in the [Portal](https://portal.telnyx.com) or via CLI:

```bash
# Install CLI — https://developers.telnyx.com/development/cli
go install github.com/team-telnyx/telnyx-cli/cmd/telnyx@latest
telnyx auth login

# Buy a number
telnyx available-phone-numbers list --country US --features voice
telnyx number-orders create --phone-number +15551234567

# Create a TeXML application (voice_url placeholder is fine)
# Note the connection_id — you need it for .env
```

Assign the phone number to the TeXML application in the Portal, or via API:

```bash
curl -X PATCH "https://api.telnyx.com/v2/phone_numbers/+15551234567" \
  -H "Authorization: Bearer $TELNYX_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"connection_id": "your_texml_app_id"}'
```

If testing outbound calls, whitelist the destination countries on your outbound voice profile:

```bash
curl -X PATCH "https://api.telnyx.com/v2/outbound_voice_profiles/{ovp_id}" \
  -H "Authorization: Bearer $TELNYX_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"whitelisted_destinations": ["US", "CA"]}'
```

## Step 2 — Configure environment

```bash
cp .env.example .env
# Edit .env:
#   TELNYX_API_KEY=your_key
#   TELNYX_PHONE_NUMBER=+1xxxxxxxxxx
#   TELNYX_CONNECTION_ID=your_texml_app_id
```

## Step 3 — Create the assistant

```bash
python provision_assistant.py
# Output:
#   TELNYX_ASSISTANT_ID=assistant-xxxx-xxxx-xxxx
#   ASSISTANT_NAME=multilingual code-switching voice agent
#   AI_MODEL=moonshotai/Kimi-K2.6
```

Copy the `TELNYX_ASSISTANT_ID` into your `.env`.

## Step 4 — Install dependencies and run

```bash
pip install -r requirements.txt
python app.py
# * Running on http://127.0.0.1:5050
```

## Step 5 — Test the agent

### Option A: Outbound call (recommended for demos)

Open `http://127.0.0.1:5050/` in your browser, enter your phone number, and click "Call me".

Or via curl:

```bash
curl -X POST http://localhost:5050/call/trigger \
  -H "Content-Type: application/json" \
  -d '{"to": "+13125550001"}'
```

Pick up the phone. The agent greets you and asks you to speak in any supported language.

### Option B: Inbound call

Dial your purchased Telnyx phone number directly. The agent answers and greets you.

### Test code-switching

1. Say "Hola, ¿cómo estás?" → agent replies in Spanish.
2. Say "Now let's switch to English." → agent replies in English.
3. Say "Namaste, kaise ho?" → agent replies in Hindi.
4. Mix: "Hola, can you help me with my order?" → agent replies in the dominant language.

## How the code-switching works

The assistant's instructions contain the code-switching logic:

```
voice: voice ultra katie

you are a friendly multilingual voice agent for a global customer support line.
you can speak english, spanish, portuguese, hindi, and mandarin.

listen carefully to the caller. detect the language they are speaking on every turn.
reply in the same language the caller is using right now.
if the caller switches language mid-conversation or mid-sentence, switch with them.
if you are unsure which language to use, ask in english "which language would you prefer".

keep replies short and natural. this is a phone call.
do not translate unless the caller asks. you are not an interpreter — you are the agent.
if a caller mixes two languages in one sentence, reply in the dominant language.
never say the name of the language out loud unless asked.
```

The STT (Deepgram nova-3 with `language: "multi"`) transcribes the caller's speech in whatever language they use. The LLM follows the instructions to reply in the same language. The TTS (`voice ultra katie`) renders the reply in that language. No application-layer language detection or routing.

## Key configuration choices

### Why `deepgram/nova-3` with `language: "multi"`

Per the AI Assistants docs: "To enable a multilingual agent, set the transcription model to `deepgram/nova-3`." The `language: "multi"` setting lets nova-3 auto-detect the spoken language on every turn, which is what makes mid-conversation code-switching possible.

### Why `voice ultra katie` in the instructions

The existing phone assistant examples in this repo (`ai-lab-results-notification-voice-python`, `ai-pci-protected-payment-collection-python`) use `voice: voice ultra katie` in the instructions text, not as a `voice_settings.voice` field. This is the verified pattern for Voice AI Assistants. Ultra voices support 36+ languages, so one voice handles all five demo languages.

### Why `moonshotai/Kimi-K2.6`

A native Telnyx model — no external API key required. Available out of the box.

### Why the Flask app is minimal

Since the Voice AI Assistant handles the entire conversation (STT, LLM, TTS, telephony), the Flask app only needs to:
- Create/reuse the assistant (`provision_assistant.py`)
- Trigger outbound calls (`/call/trigger`)
- Log webhook events (`/webhooks/call`)
- Serve a small browser UI (`GET /`)

There is no call-control logic, no application-layer STT, no manual TTS. The conversation runs entirely on Telnyx.

## Notes and caveats

- **Webhook is for logging only.** The assistant handles the conversation. Flask logs events for observability but does not intervene.
- **Language count.** Ultra TTS supports 36+ languages. The demo covers 5 (EN, ES, PT, Hindi, Mandarin). Add more by updating the instructions.
- **Ultra is REST-only for direct TTS.** This example uses the AI Assistant voice settings, not the REST TTS endpoint, so the WebSocket restriction does not apply.
- **Expressive Mode.** Ultra voices support inline SSML emotion tags (`<emotion value="excited" />`) and nonverbal cues (`[laughter]`). This is optional for the code-switching demo. The assistant can use them in its replies for more expressive delivery.

## Next steps

- Add more languages by updating the instructions (e.g. Arabic, French, German, Japanese).
- Add a dynamic variables webhook to personalize the greeting based on the caller's number.
- Add a Handoff tool to transfer to a human agent when the caller asks for one.
- Enable conversation insights to analyze language usage across calls.
