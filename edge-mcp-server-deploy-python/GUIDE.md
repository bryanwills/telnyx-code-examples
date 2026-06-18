# Edge MCP Server Deploy

> Deploy an MCP (Model Context Protocol) server to Telnyx Edge, giving AI agents tool access to Telnyx APIs.

## What You'll Build

A serverless MCP tool server running on Telnyx Edge Compute that exposes Telnyx capabilities (search numbers, send SMS, create calls) as tools any MCP-compatible AI agent can discover and use.

| | |
|---|---|
| **Lines of code** | ~80 |
| **Time to build** | ~15 minutes |
| **Difficulty** | Intermediate |
| **Products** | Edge Compute, Voice, SMS, Numbers |

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)
- [Telnyx Edge CLI](https://developers.telnyx.com/docs/edge-compute) (`telnyx-edge`) installed

## Telnyx APIs Used

- **Search Numbers**: `GET /v2/available_phone_numbers` — [API reference](https://developers.telnyx.com/api/numbers/list-available-phone-numbers)
- **Send Message**: `POST /v2/messages` — [API reference](https://developers.telnyx.com/api/messaging/send-message)
- **Create Call**: `POST /v2/calls` — [API reference](https://developers.telnyx.com/api/call-control/create-call)

## Step 1: Clone & Configure

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/edge-mcp-server-deploy-python
```

Set your API key:

```bash
telnyx-edge secrets add TELNYX_API_KEY <your-api-key>
```

## Step 2: Code Walkthrough

`function/func.py` implements the MCP protocol:

- **`tools/list`** — returns available tools (search_numbers, send_sms, create_call)
- **`tools/call`** — executes a tool with provided arguments
- Each tool maps directly to a Telnyx API endpoint

## Step 3: Deploy to Edge

```bash
telnyx-edge deploy
```

## Step 4: Test

```bash
# List available tools
curl https://<your-edge-url> \
  -H "Content-Type: application/json" \
  -d '{"method": "tools/list"}'
```

```json
{"tools": [{"name": "search_numbers", "description": "Search available phone numbers"}, {"name": "send_sms", "description": "Send an SMS message"}, {"name": "create_call", "description": "Create an outbound call"}]}
```

## Step 5: Connect to an AI Agent

Point any MCP-compatible agent (Claude, GPT, custom) at your edge URL:

```json
{
  "mcpServers": {
    "telnyx": {
      "url": "https://<your-edge-url>"
    }
  }
}
```

The agent can now search for phone numbers, send SMS, and initiate calls autonomously.

## Customize & Extend

- Add more Telnyx tools (fax, verify, SIP, IoT)
- Add authentication to restrict agent access
- Chain with other MCP servers for multi-provider workflows
- Add rate limiting and usage tracking

## Resources

- [Full source code and README](./README.md)
- [MCP Protocol Specification](https://modelcontextprotocol.io)
- [Telnyx Edge Compute Docs](https://developers.telnyx.com/docs/edge-compute)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Telnyx Portal](https://portal.telnyx.com)
