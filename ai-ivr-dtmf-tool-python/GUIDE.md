# Build an AI IVR DTMF Tool

This pattern keeps keypad control in your backend while still letting the AI Assistant decide which menu option is appropriate.

## Flow

1. Start an outbound call.
2. On `call.answered`, start the IVR assistant.
3. The assistant hears a phone menu.
4. The assistant calls `/tools/send-dtmf` with a digit and reason.
5. The backend sends `send_dtmf` to Telnyx.
6. The backend optionally plays a short DTMF WAV file to both legs for demo feedback.

## Prompt Guidance

Tell the assistant:

```txt
When a menu requires keypad input, call the send_dtmf tool with the digit. After calling the tool, stay silent and continue listening.
```

## Production Notes

- Validate requested digits before sending them.
- Restrict tool access to trusted Telnyx assistant calls.
- Log tool calls for auditability.
- Avoid letting the assistant directly choose arbitrary call-control actions.
