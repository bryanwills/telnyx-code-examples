---
name: ai-pci-protected-payment-collection
title: "AI PCI Protected Payment Collection"
description: "A PCI-protected inbound payment collection demo using Telnyx Voice API, AI Assistants, the native Pay tool, and Pay over Voice."
language: python
framework: flask
telnyx_products: [Voice API, AI Assistants, Pay over Voice]
channel: [voice]
---

# AI PCI Protected Payment Collection

This demo answers an inbound billing call, starts a Telnyx AI Assistant, lets the assistant negotiate a payment plan, and uses the native Telnyx `Pay (BETA)` tool to start Pay over Voice for secure card collection.

Use this example to build AI Communications Infrastructure for PCI-protected voice payment workflows.

The important PCI point is that the app and assistant do **not** gather raw card digits. Telnyx Pay over Voice handles the keypad payment IVR and sends sanitized progress/completion webhooks back to the app.

## Telnyx DevDocs Used

- [Voice API Commands and Resources](https://developers.telnyx.com/docs/voice/programmable-voice/voice-api-commands-and-resources)
- [Attach an AI Assistant to a Call](https://developers.telnyx.com/docs/voice/programmable-voice/ai-assistant-start)
- [Pay over Voice](https://developers.telnyx.com/docs/voice/programmable-voice/pay)
- [AI Assistants](https://developers.telnyx.com/docs/inference/ai-assistants)

## Flow

1. Caller dials the Telnyx billing number.
2. The Flask app answers with Voice API.
3. The app starts a Telnyx AI Assistant with `ai_assistant_start`.
4. The assistant verifies the caller and negotiates a payment plan.
5. The caller confirms consent to secure card collection.
6. The assistant invokes the native `Pay (BETA)` tool.
7. Telnyx Pay over Voice prompts for card number, expiration date, postal code, and security code by keypad.
8. Telnyx posts the authorization request to `/webhooks/payment-processor`.
9. Telnyx sends `call.payment.progress` and `call.payment.completed` webhooks to `/webhooks/voice`.
10. The local dashboard shows sanitized payment events without raw card digits.

## Setup

```bash
cd ai-pci-protected-payment-collection-python
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Expose the app:

```bash
ngrok http 5000
```

Configure your Telnyx Voice API application webhook URL:

```text
https://<ngrok-id>.ngrok-free.app/webhooks/voice
```

Update `.env`:

```text
TELNYX_API_KEY=KEY...
PUBLIC_BASE_URL=https://<ngrok-id>.ngrok-free.app
PAY_CONNECTOR_NAME=pci-protected-payment-demo
AI_MODEL=moonshotai/Kimi-K2.6
```

Provision the Pay Connector, native Pay tool, and AI Assistant:

```bash
python provision_assistant.py
```

Copy the printed `TELNYX_ASSISTANT_ID` into `.env`, then start the app:

```bash
python app.py
```

Open the local dashboard:

```text
http://127.0.0.1:5000
```

Assign a Telnyx voice-capable phone number to the Voice API application, then call the number.

## Pay over Voice Setup

`provision_assistant.py` creates:

- a test-mode generic Pay Connector pointed at `/webhooks/payment-processor`
- a native `Pay (BETA)` AI tool that uses that connector
- an AI Assistant with only that Pay tool attached

The default assistant model is:

```text
moonshotai/Kimi-K2.6
```

For test mode, use one of the Pay over Voice test card numbers from the Telnyx docs. A common Visa test card is:

```text
4111111111111111
```

Use any future expiration date in `MMYY` format, a postal code, and a 3-digit security code for local testing.

## Environment Variables

| Variable | Required | Description |
|---|---:|---|
| `TELNYX_API_KEY` | yes | Telnyx API key. |
| `TELNYX_PUBLIC_KEY` | recommended | Public key for webhook signature verification. |
| `PUBLIC_BASE_URL` | yes for provisioning | Public HTTPS URL for this Flask app. |
| `PAY_CONNECTOR_NAME` | yes | Name of the Telnyx Pay Connector. |
| `PAYMENT_DESCRIPTION` | no | Description used by the native Pay tool. |
| `AI_MODEL` | no | Assistant model. Defaults to `moonshotai/Kimi-K2.6`. |
| `TELNYX_ASSISTANT_ID` | yes | AI Assistant ID printed by `provision_assistant.py`. |
| `DEMO_CUSTOMER_ID` | no | Customer id from `data/customers.json`, default `acct_1042`. |
| `PORT` | no | Flask port, default `5000`. |

## Demo Script

Use caller data from `data/customers.json`.

For Jordan Lee:

- Phone on file: `+15555550100`
- Date of birth: `1990-03-15`
- Balance: `$342.50`

Suggested call:

```text
caller: jordan lee
ai: thanks. what is your date of birth?
caller: march fifteenth nineteen ninety
ai: your account is 45 days past due with a balance of $342.50...
caller: can i do forty dollars a week
ai: i can set that up as 8 weekly payments of $40.00 plus a final payment of $22.50...
caller: yes, i'd like to make the first payment now
pay over voice: enter card details on the keypad
```

Suggested keypad input:

```text
4111111111111111
0827
94111
123
```

## API Reference

### `POST /webhooks/voice`

Receives Telnyx Voice API webhooks.

Handled events include:

- `call.initiated`
- `call.answered`
- `call.payment.progress`
- `call.payment.completed`
- `call.conversation.ended`
- `call.conversation_insights.generated`
- `call.hangup`

### `POST /webhooks/payment-processor`

Mock payment processor endpoint for a Telnyx Pay Connector.

It returns a successful charge unless the card number ends in `0002`.

### `GET /health`

Returns demo configuration and runtime health.

### `GET /events`

Returns sanitized local audit events for the dashboard.

### `GET /sessions`

Returns completed payment sessions.

## PCI Notes

This demo is designed to show a PCI-conscious architecture pattern, not to certify your production environment.

- The app never asks the caller to speak card data.
- The app never uses raw `gather_using_audio` to receive the PAN.
- The assistant uses the native Telnyx Pay tool for the sensitive card-entry step.
- The local dashboard logs only high-level payment status and masked payment fields.
- The local dashboard does not log PAN, CVV, expiration date, postal code, or raw DTMF.

## Troubleshooting

- If the assistant does not answer, confirm `TELNYX_ASSISTANT_ID` is set and the Voice API application webhook points to `/webhooks/voice`.
- If the Pay tool is not available, confirm your Telnyx org has AI Assistant Pay tool access.
- If Pay over Voice does not start, confirm the assistant has the native `Pay (BETA)` tool attached and that `PAY_CONNECTOR_NAME` matches the connector created by `provision_assistant.py`.
- If the processor webhook returns `Method Not Allowed` in a browser, that is expected. The endpoint only accepts `POST`.
- If card digits appear in your app logs, stop and review the integration. This sample should only log sanitized payment status or masked payment fields.

## Related Examples

- [route-phone-calls-to-ai-agent-python](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/route-phone-calls-to-ai-agent-python/README.md)
- [chat-with-ai-assistant-python](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/chat-with-ai-assistant-python/README.md)
- [ai-assistant-multi-tool-python](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/ai-assistant-multi-tool-python/README.md)

## Agent Discovery

Agents should start with `README.md`, then inspect `API.md` for endpoint contracts and `provision_assistant.py` for assistant, Pay Connector, and native Pay tool provisioning. The primary runtime entrypoint is `app.py`.
