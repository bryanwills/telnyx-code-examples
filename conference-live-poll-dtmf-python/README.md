# Conference Live Poll via DTMF

## What Does This Example Do?

During a multi-party conference call, the host triggers poll questions. All participants vote by pressing 1-4 on their phone. Results tallied instantly.

## Who Is This For?

- Developers building with Telnyx APIs.
- Teams looking for production-ready starting points.
- Anyone exploring what's possible with communications infrastructure + AI.

## Why Telnyx?

Telnyx is an **AI Communications Infrastructure** platform. This example runs entirely on Telnyx -- no third-party APIs, no middleware, no glue code between vendors.

## Prerequisites

- Python 3.8+
- Telnyx account with API key from [portal.telnyx.com](https://portal.telnyx.com)
- [ngrok](https://ngrok.com) for local development

## Quick Start

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/conference-live-poll-dtmf-python
cp .env.example .env
# Edit .env with your credentials
make setup && make run
```

## Implementation Details

### Products used

| Product | Role |
|---------|------|
| Conference API | Multi-party calls |
| DTMF | Vote collection |
| Call Control | Per-participant interaction |

## Complete Code

See [app.py](./app.py) for the full implementation.

## FAQ

**Q: Can I use this in production?**
This is a working starting point. Add error handling, persistent storage, and authentication for production use.

**Q: What model should I use?**
Default is Kimi K2.6 via Telnyx Inference. Any model on Telnyx works -- swap the AI_MODEL env var.

## Related Examples

- [Conference Call With Ai Summary](../conference-call-with-ai-summary-python/)
- [Sms Poll Voting System](../sms-poll-voting-system-python/)
