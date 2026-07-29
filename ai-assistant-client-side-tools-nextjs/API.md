# AI Assistant Client-Side Tools API Reference

This example is a browser-only Next.js app. It does not expose backend routes, webhook endpoints, database APIs, or CRUD APIs.

The relevant API surface is the Telnyx AI Agent Lib client-side tools contract registered in the browser with `@telnyx/ai-agent-lib`.

## Telnyx Library Used By The App

### `TelnyxAIAgentProvider`

The app wraps the website voice-agent panel with `TelnyxAIAgentProvider` when `NEXT_PUBLIC_TELNYX_AGENT_ID` is configured.

```tsx
<TelnyxAIAgentProvider
  agentId={telnyxConfig.agentId}
  versionId={telnyxConfig.versionId}
  widgetVersion={telnyxConfig.widgetVersion}
  environment={telnyxConfig.environment}
  debug={telnyxConfig.debug}
  clientToolTimeoutMs={telnyxConfig.clientToolTimeoutMs}
>
  <ToolRegistrar executeTool={executeTool} />
  <TelnyxWidget />
</TelnyxAIAgentProvider>
```

### `useClient().registerClientTool(name, handler)`

The app registers five browser functions as client-side tools. The assistant invokes these tools during a WebRTC voice/chat session, and the handlers run in the user’s browser.

## Client-Side Tools

### `set_theme`

Changes the dashboard theme.

Input:

```json
{
  "theme": "dark"
}
```

Schema:

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": ["theme"],
  "properties": {
    "theme": {
      "type": "string",
      "enum": ["light", "dark"]
    }
  }
}
```

Returns:

```json
{
  "success": true,
  "theme": "dark"
}
```

### `navigate_to_section`

Changes the active dashboard section without reloading the page.

Input:

```json
{
  "section": "assistants"
}
```

Schema:

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": ["section"],
  "properties": {
    "section": {
      "type": "string",
      "enum": ["overview", "assistants", "analytics", "settings"]
    }
  }
}
```

Returns:

```json
{
  "success": true,
  "section": "assistants"
}
```

### `open_create_assistant_modal`

Opens the Create Assistant modal.

Input:

```json
{}
```

Schema:

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [],
  "properties": {}
}
```

Returns:

```json
{
  "success": true,
  "modal": "create_assistant"
}
```

### `get_form_state`

Reads the current React state for the Create Assistant form.

Input:

```json
{}
```

Schema:

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [],
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

Updates the visible Create Assistant form. The modal must be open first.

Input:

```json
{
  "field": "voice",
  "value": "Atlas"
}
```

Schema:

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": ["field", "value"],
  "properties": {
    "field": {
      "type": "string",
      "enum": ["name", "voice", "language"]
    },
    "value": {
      "type": "string"
    }
  }
}
```

Returns:

```json
{
  "success": true,
  "formState": {
    "name": "Revenue Concierge",
    "voice": "Atlas",
    "language": "English",
    "isModalOpen": true
  }
}
```

## Error Cases

The tool executor logs failed invocations in the activity panel and returns structured errors for:

- unknown sections
- unknown form fields
- invalid themes
- invalid voices or languages
- empty or too-long names
- tool timeouts
- missing Telnyx configuration
- updating the form while the modal is closed

## No Backend API

This sample intentionally has no `pages/api`, App Router route handlers, Express server, webhook receiver, database, or Telnyx API key in browser code.
