# Build an AI Assistant Context Handoff

This example focuses on prompt and state separation.

## IVR Assistant

The IVR assistant should listen to menus, request DTMF tools, and stay silent once the backend moves the call to the next stage.

## Representative Assistant

The representative assistant receives:

- original objective
- target company
- approved user context
- recent transcript snippets
- current call state

It should use that context without repeating IVR details unless the representative asks.

## Production Notes

- Keep context scoped to information approved for the call.
- Avoid sending unnecessary sensitive data in `client_state`.
- Verify Telnyx webhook signatures before trusting call lifecycle events.
- Persist handoff state outside memory for long-running calls.
