# Edge Compute Webhook Proxy

> Deploy a webhook handler to Telnyx Edge for low-latency event processing close to your users.

## What You'll Build

A serverless webhook proxy that runs on Telnyx Edge Compute, processing Telnyx events (calls, messages, SIM status) at the edge with sub-10ms routing.

| | |
|---|---|
| **Lines of code** | ~50 |
| **Time to build** | ~10 minutes |
| **Difficulty** | Intermediate |
| **Products** | Edge Compute, Voice, SMS |

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)
- [Telnyx Edge CLI](https://developers.telnyx.com/docs/edge-compute) (`telnyx-edge`) installed
- [ngrok](https://ngrok.com) for local testing

## Telnyx APIs Used

- **Edge Compute Deploy**: `telnyx-edge deploy` — [Edge Compute docs](https://developers.telnyx.com/docs/edge-compute)

## Step 1: Clone & Configure

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/edge-compute-webhook-proxy-python
```

Set your API key as an edge secret:

```bash
telnyx-edge secrets add TELNYX_API_KEY <your-api-key>
```

## Step 2: Code Walkthrough

The function lives in `function/func.py`. It receives Telnyx webhook events and routes them based on event type:

- **Voice events** → logged and optionally forwarded
- **SMS events** → parsed and routed
- **Unknown events** → returned with metadata for debugging

## Step 3: Test Locally

```bash
cd function
python -c "from func import handler; print(handler({'body': '{\"data\":{\"event_type\":\"call.initiated\"}}'}, None))"
```

## Step 4: Deploy to Edge

```bash
telnyx-edge deploy
```

Your function is now running globally on Telnyx Edge. Use the returned URL as your webhook endpoint in the [Telnyx Portal](https://portal.telnyx.com).

## Step 5: Test

```bash
curl -X POST https://<your-edge-url> \
  -H "Content-Type: application/json" \
  -d '{"data": {"event_type": "call.initiated"}}'
```

```json
{"status": "processed", "event_type": "call.initiated"}
```

## Customize & Extend

- Add event filtering and routing rules
- Forward events to multiple downstream services
- Add authentication and signature verification
- Chain with other edge functions for complex workflows

## Resources

- [Full source code and README](./README.md)
- [Telnyx Edge Compute Docs](https://developers.telnyx.com/docs/edge-compute)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Telnyx Portal](https://portal.telnyx.com)
- [Community & Support](https://support.telnyx.com)
