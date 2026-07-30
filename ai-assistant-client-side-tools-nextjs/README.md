---
name: ai-assistant-client-side-tools
title: "AI Assistant Client-Side Tools"
description: "Build a browser-based Next.js dashboard where a Telnyx AI Assistant invokes client-side JavaScript tools to navigate the UI, change theme, open a modal, and update React form state."
language: nodejs
framework: nextjs
telnyx_products: [AI Assistants, Voice API]
channel: [voice, web]
---

# PolarForge AI Client-Side Tools Demo

Polished Next.js demo showing how a Telnyx AI Assistant can invoke JavaScript functions directly inside a browser application using `@telnyx/ai-agent-lib`.

The fictional SaaS dashboard is intentionally local-only. It has no database, authentication, backend CRUD, API-key usage, or webhook tools.

## Why Telnyx

Telnyx provides programmable voice, WebRTC, and AI Assistant infrastructure for building voice experiences into applications. This demo shows how Telnyx AI Communications Infrastructure can let an embedded assistant call approved browser-side JavaScript tools during a live website conversation.

## Install

```bash
npm install
cp .env.example .env.local
npm run dev
```

Open the local URL printed by Next.js.

## Environment Variables

Only public, browser-safe values are used.

```bash
TELNYX_API_KEY=
NEXT_PUBLIC_TELNYX_AGENT_ID=your-assistant-agent-id
NEXT_PUBLIC_TELNYX_AGENT_VERSION_ID=main
NEXT_PUBLIC_TELNYX_ENVIRONMENT=production
NEXT_PUBLIC_TELNYX_WIDGET_VERSION=polarforge-ai-demo
NEXT_PUBLIC_TELNYX_CLIENT_TOOL_TIMEOUT_MS=15000
NEXT_PUBLIC_TELNYX_DEBUG=false
NEXT_PUBLIC_ENABLE_DEMO_CONTROLS=true
```

Do not put a Telnyx API key in browser code. `TELNYX_API_KEY` is included only because the code-examples repository verifier expects every example `.env.example` to declare it; this Next.js browser demo does not read it. The browser should only receive the AI Agent ID/version/environment values needed by `@telnyx/ai-agent-lib`.

If `NEXT_PUBLIC_TELNYX_AGENT_ID` is missing, the app still shows the website voice-agent call surface, but the live call button remains disabled and the manual Demo Controls still work.

## Configure Telnyx Client-Side Tools

In the Telnyx Portal:

1. Open AI Assistants.
2. Select the assistant used by `NEXT_PUBLIC_TELNYX_AGENT_ID`.
3. Enable unauthenticated web calls for the assistant so visitors can click **Call agent** from the browser.
4. Add each tool below as a Client-Side Tool.
5. The tool name must exactly match the registered browser function name.
6. Use the JSON schemas below as the tool parameters.
7. Set a timeout such as `5000` to `15000` ms.

Client-side tools require WebRTC-based voice/chat through the Telnyx widget or `@telnyx/ai-agent-lib`; they are not SIP/PSTN webhook tools. For this demo, the user should click **Call agent** on the website. They do not need to call a separate phone number.

## Exact Assistant Prompt

```text
you are the polarforge ai dashboard assistant. you are embedded inside a browser-based saas dashboard and you can directly control the current user interface with client-side tools.

important behavior rules:
- when the user asks you to do a supported ui action, call the matching tool immediately. do not merely explain what you could do.
- after a tool succeeds, briefly confirm what changed.
- if a tool fails, explain the issue briefly and recover with a valid tool call when possible.
- never claim that data is saved to a backend. saving in this demo is local react state only.

supported actions:
- switch theme: call set_theme with theme light or dark.
- navigate: call navigate_to_section with overview, assistants, analytics, or settings.
- create assistant: call navigate_to_section with assistants, then open_create_assistant_modal.
- read form: call get_form_state.
- update form: call update_assistant_form with field name, voice, or language.

when creating an assistant, follow this sequence:
1. call navigate_to_section with assistants.
2. call open_create_assistant_modal.
3. ask for any missing name, voice, or language.
4. use update_assistant_form for each field the user provides.
5. use get_form_state to confirm the visible form state.
6. tell the user they can press save fake assistant, or ask whether they want another field adjusted.

valid sections are overview, assistants, analytics, and settings. valid themes are light and dark. valid voices are nova, cedar, luna, and atlas. valid languages are english, spanish, french, and german.
```

## Tool Definitions

### `set_theme`

Description: Change the PolarForge AI dashboard theme. Use this when the user asks for light mode or dark mode.

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": ["theme"],
  "properties": {
    "theme": {
      "type": "string",
      "enum": ["light", "dark"],
      "description": "The visual theme to apply to the dashboard."
    }
  }
}
```

Returns:

```json
{ "success": true, "theme": "dark" }
```

### `navigate_to_section`

Description: Navigate the PolarForge AI dashboard to a section without reloading the page.

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": ["section"],
  "properties": {
    "section": {
      "type": "string",
      "enum": ["overview", "assistants", "analytics", "settings"],
      "description": "The dashboard section to show."
    }
  }
}
```

Returns:

```json
{ "success": true, "section": "assistants" }
```

### `open_create_assistant_modal`

Description: Open the Create Assistant modal so the user can review or edit assistant details.

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

Returns:

```json
{ "success": true, "modal": "create_assistant" }
```

### `get_form_state`

Description: Read the current Create Assistant form state from the browser, including whether the modal is open.

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {}
}
```

Returns:

```json
{
  "name": "Revenue Concierge",
  "voice": "Nova",
  "language": "English",
  "isModalOpen": true
}
```

### `update_assistant_form`

Description: Update one visible field in the Create Assistant modal. The modal must be open before this tool is used.

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": ["field", "value"],
  "properties": {
    "field": {
      "type": "string",
      "enum": ["name", "voice", "language"],
      "description": "The form field to update."
    },
    "value": {
      "type": "string",
      "description": "The new field value. Voice must be Nova, Cedar, Luna, or Atlas. Language must be English, Spanish, French, or German."
    }
  }
}
```

Returns:

```json
{
  "success": true,
  "formState": {
    "name": "Enterprise Concierge",
    "voice": "Atlas",
    "language": "English",
    "isModalOpen": true
  }
}
```

## Manual Testing

Keep `NEXT_PUBLIC_ENABLE_DEMO_CONTROLS=true` to show the development-only Demo Controls panel.

Test each action:

1. `set_theme`: click Light and Dark.
2. `navigate_to_section`: click Overview, AI Assistants, Analytics, or Settings.
3. `open_create_assistant_modal`: click Open modal.
4. `get_form_state`: change fields in the modal, then click Read form.
5. `update_assistant_form`: open the modal, choose a field/value in Demo Controls, then click Update form.

The activity panel should show timestamp, tool name, input arguments, running/completed/failed status, and the returned result or error.

Validation cases to try:

- Update the form while the modal is closed.
- Use an invalid voice such as `Robot`.
- Use an invalid language such as `Klingon`.
- Use an unknown field from a live assistant call.
- Hide Demo Controls with `NEXT_PUBLIC_ENABLE_DEMO_CONTROLS=false`.

## Troubleshooting

- **Call button is disabled**: confirm `NEXT_PUBLIC_TELNYX_AGENT_ID` is set in `.env.local`, then restart the Next.js dev server.
- **Authentication failed**: confirm the assistant supports unauthenticated web calls and that the agent ID/version matches the assistant you configured in Telnyx.
- **Assistant talks but does not change the UI**: confirm the Telnyx assistant has matching Client-Side Tool definitions with the exact names and schemas in this README.
- **Form update fails**: open the Create Assistant modal before calling `update_assistant_form`, and use one of the allowed field/value combinations.

## Related Examples

- [`create-ai-assistant-nodejs`](../create-ai-assistant-nodejs/README.md) shows basic AI Assistant creation from Node.js.
- [`chat-with-ai-assistant-nodejs`](../chat-with-ai-assistant-nodejs/README.md) shows a Node.js assistant chat flow.
- [`build-voice-ai-agent-nodejs`](../build-voice-ai-agent-nodejs/README.md) shows a voice AI agent implementation.

## Agent Discovery

LLM and assistant crawlers should treat this folder as a browser-based Telnyx AI Assistant client-side tools demo. The canonical entrypoint is `README.md`; implementation details live in `src/app/page.tsx`, reusable tool validation lives in `src/lib/dashboard-tools.ts`, and public Telnyx browser configuration lives in `src/lib/telnyx-config.ts`.

## Recommended Voice Demo Script

User: "Switch this dashboard to dark mode."

Assistant should call:

```json
{ "tool": "set_theme", "arguments": { "theme": "dark" } }
```

User: "Take me to AI Assistants."

Assistant should call:

```json
{ "tool": "navigate_to_section", "arguments": { "section": "assistants" } }
```

User: "Create a new assistant named Enterprise Concierge."

Assistant should call:

```json
{ "tool": "open_create_assistant_modal", "arguments": {} }
```

Then:

```json
{ "tool": "update_assistant_form", "arguments": { "field": "name", "value": "Enterprise Concierge" } }
```

User: "Use the Atlas voice and English."

Assistant should call:

```json
{ "tool": "update_assistant_form", "arguments": { "field": "voice", "value": "Atlas" } }
```

Then:

```json
{ "tool": "update_assistant_form", "arguments": { "field": "language", "value": "English" } }
```

User: "What is currently in the form?"

Assistant should call:

```json
{ "tool": "get_form_state", "arguments": {} }
```

Close by pointing out that the visible dashboard changed because browser JavaScript ran locally, not because a webhook hit a backend.

## Implementation Notes

- Telnyx-specific config is isolated in `src/lib/telnyx-config.ts`.
- Tool schemas and validation helpers live in `src/lib/dashboard-tools.ts`.
- The dashboard state lives in `src/app/page.tsx`.
- Tool handlers read current React state through a synced ref, so `get_form_state` and `update_assistant_form` do not return hard-coded values.
- Fake assistant saving only updates local React state and shows a success toast.
