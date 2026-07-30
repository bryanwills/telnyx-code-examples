# Build An AI Assistant Client-Side Tools Demo With Next.js

This guide walks through a browser-based Telnyx AI Assistant demo where the user clicks **Call agent** on a website and the assistant invokes JavaScript functions directly in the page.

The demo is a fictional SaaS dashboard called PolarForge AI. It proves the client-side tools pattern without backend webhooks or database persistence.

## Flow

1. User opens the Next.js dashboard in a browser.
2. User clicks **Call agent** in the website voice-agent panel.
3. `@telnyx/ai-agent-lib` starts a WebRTC voice/chat session with the configured Telnyx AI Assistant.
4. The app registers five client-side tools with `useClient().registerClientTool(...)`.
5. The assistant calls those tools during the conversation.
6. Tool handlers run in the browser, update React state, and log each invocation in the activity panel.

## Setup

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/ai-assistant-client-side-tools-nextjs
cp .env.example .env.local
npm install
npm run dev
```

Open the local URL printed by Next.js.

## Required Environment

Set this value in `.env.local`:

```bash
NEXT_PUBLIC_TELNYX_AGENT_ID=assistant-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

Optional values:

```bash
NEXT_PUBLIC_TELNYX_AGENT_VERSION_ID=main
NEXT_PUBLIC_TELNYX_ENVIRONMENT=production
NEXT_PUBLIC_TELNYX_WIDGET_VERSION=polarforge-ai-demo
NEXT_PUBLIC_TELNYX_CLIENT_TOOL_TIMEOUT_MS=15000
NEXT_PUBLIC_TELNYX_DEBUG=false
NEXT_PUBLIC_ENABLE_DEMO_CONTROLS=true
```

Do not put a Telnyx API key in `.env.local`. This is browser code, so only browser-safe public configuration belongs here.

## Portal Configuration

In the Telnyx Portal:

1. Create or open an AI Assistant.
2. Configure the assistant for web voice/chat through the Telnyx widget or AI Agent Lib.
3. Enable unauthenticated web calls so visitors can call the assistant from the browser without a separate login.
4. Add the five matching client-side tools from `API.md`.
5. Make sure each Portal tool name exactly matches the browser registration name.
6. Use the prompt in `README.md`.
7. Copy the assistant ID into `NEXT_PUBLIC_TELNYX_AGENT_ID`.

## Manual Test Without The Assistant

Keep this enabled:

```bash
NEXT_PUBLIC_ENABLE_DEMO_CONTROLS=true
```

Then use the Demo Controls panel:

1. Click **Dark** and **Light** to test `set_theme`.
2. Click each section button to test `navigate_to_section`.
3. Click **Open modal** to test `open_create_assistant_modal`.
4. Change fields in the modal and click **Read form** to test `get_form_state`.
5. Keep the modal open, choose a field/value, and click **Update form** to test `update_assistant_form`.
6. Close the modal and click **Update form** again to confirm the failed `modal_closed` path appears in the activity panel.

Every invocation should show:

- timestamp
- tool name
- input arguments
- running, completed, or failed status
- returned result or error

## Voice Test

After the assistant ID is configured:

1. Restart `npm run dev`.
2. Open the dashboard.
3. Click **Call agent**.
4. Allow microphone access.
5. Say: "switch to dark mode."
6. Say: "take me to AI Assistants."
7. Say: "create an assistant named Enterprise Concierge with the Atlas voice in English."
8. Watch the page navigate, open the modal, update the visible form, and log every tool call.

The user does not need to call a separate phone number. This example is for browser WebRTC voice/chat.

## Production Notes

- Hide Demo Controls in production with `NEXT_PUBLIC_ENABLE_DEMO_CONTROLS=false`.
- Keep client-side tools scoped to actions the browser is allowed to perform.
- Never expose a Telnyx API key in frontend code.
- Add consent and recording notices according to your legal requirements before shipping a real voice experience.
- Persist real assistant records through your own backend if needed; this demo only uses local React state.
