# Build Guide

This example follows the Telnyx DevDocs pattern for Voice API applications plus the native AI Assistant Pay tool:

1. answer an inbound call
2. attach a Telnyx AI Assistant with `ai_assistant_start`
3. let the assistant invoke the native `Pay (BETA)` tool
4. receive Pay over Voice progress/completed webhooks
5. show sanitized proof in the demo dashboard

## Why Native Pay Tool

For PCI demos, avoid collecting card data through ordinary speech, raw DTMF, or custom assistant webhook tools. The native Pay tool starts Telnyx Pay over Voice directly from the assistant, so the assistant can manage the conversation while Pay over Voice manages the sensitive card-entry step.

## Default Model

The provisioning script defaults to:

```text
moonshotai/Kimi-K2.6
```

Override it with `AI_MODEL` if your account uses a different supported model.

## Demo Completion

Pay over Voice emits progress and completion webhooks when the IVR flow finishes. The dashboard marks the payment step complete from `call.payment.progress` and `call.payment.completed` events. It does not require a second assistant webhook tool to record completion.
