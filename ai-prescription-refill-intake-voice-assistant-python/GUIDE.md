# Build an AI Prescription Refill Intake Voice Assistant

This guide shows how to build a healthcare voice AI workflow where Telnyx answers an inbound prescription refill call, starts an AI Assistant, and lets the assistant create structured refill requests through webhook tools.

## Why This Sample Works Well

Prescription refill intake is specific enough for a healthcare demo, but the assistant does not practice medicine or approve prescriptions. It collects admin workflow context and routes the request to staff.

The assistant can:

- ask for the medication name
- ask for dosage or strength, if known
- ask for the preferred pharmacy
- ask how many days of medication are left
- queue a pharmacy callback
- flag manual review for urgent or sensitive requests

## 1. Configure Environment Variables

```bash
cp .env.example .env
```

Set:

```bash
TELNYX_API_KEY=KEY_your_telnyx_api_key_here
TELNYX_PHONE_NUMBER=+18005551234
PUBLIC_BASE_URL=https://your-public-url.example.com
TOOL_SECRET=replace_with_a_random_shared_secret
```

Optional:

```bash
PHARMACY_SLACK_WEBHOOK=https://hooks.slack.com/services/...
```

## 2. Expose The Flask App

```bash
python app.py
ngrok http 5000
```

Set `PUBLIC_BASE_URL` to the ngrok HTTPS URL.

## 3. Provision The Assistant

```bash
python provision_assistant.py
```

Set the printed `TELNYX_ASSISTANT_ID` in `.env`.

The provisioned assistant:

- uses `moonshotai/Kimi-K2.6` by default
- starts with a short refill-line greeting
- asks one question at a time
- uses `9-1-1` for emergency wording
- never says a refill is approved or denied
- calls webhook tools for refill requests, manual review, and callbacks

## 4. Configure Call Control

In the Telnyx Portal, create or update a Call Control Application:

- Webhook URL: `https://your-public-url.example.com/webhooks/voice`
- Webhook API version: `2`

Assign your Telnyx phone number to that Call Control Application.

## 5. Test The Flow

Call the Telnyx phone number assigned to the Call Control Application.

The assistant should ask one question at a time:

```text
what medication are you calling to refill
```

After the assistant collects enough context, it calls `create_refill_request`. If the request needs staff review, it calls `flag_manual_review`. If the caller asks for a callback, it calls `queue_callback`.

## 6. Review Refill Requests

```bash
curl http://localhost:5000/refills/requests | python3 -m json.tool
```

## HIPAA-Aware Notes

This sample intentionally avoids claiming HIPAA compliance. It demonstrates practical safeguards:

- verify Telnyx webhooks before trusting events
- pass assistant tool requests through a shared secret
- store masked caller identifiers
- keep notes to minimum necessary summaries
- avoid sending raw PHI to Slack or logs unless your compliance program allows it
- route approval, denial, controlled substance, side effect, and urgent access decisions to human staff

For production, add encrypted storage, staff authentication, audit logging, retention policies, monitoring, and compliance review.
