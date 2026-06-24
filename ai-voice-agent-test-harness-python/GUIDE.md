# Build an AI Voice Agent Test Harness

This example gives developers a controlled mock IVR that can be used to validate an outbound Telnyx AI voice agent before calling real businesses.

## Runtime Flow

1. Start the FastAPI app.
2. Create a dry-run or real outbound test session with `POST /calls/outbound`.
3. The app stores the selected scenario and expected DTMF digit.
4. The mock IVR endpoint returns TeXML with a predictable menu.
5. The AI Assistant calls `/tools/send-dtmf`.
6. The backend records whether the digit matched the scenario.
7. The mock IVR emits hold and representative pickup phrases.
8. The AI Assistant can call `/tools/end-call`.
9. You inspect `/test-results`.

## Why This Is Useful

Real business IVRs are inconsistent and slow to test against. A mock IVR gives you a repeatable target for prompt tuning, tool configuration, and regression testing.

## Production Notes

- Keep this as a test utility, not a customer-facing flow.
- Add authentication if this runs outside local development.
- Verify Telnyx webhook signatures before trusting real webhook traffic.
- Add scenario fixtures for the IVR patterns your agents commonly encounter.
- Store test results in a database if you want historical regression tracking.
