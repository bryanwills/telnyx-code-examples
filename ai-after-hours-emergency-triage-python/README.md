# AI After-Hours Emergency Triage

## What Does This Example Do?

After-hours calls screened by AI. True emergencies (outages, security breaches) get forwarded to on-call. Everything else gets a voicemail and next-day callback promise.

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
cd telnyx-code-examples/ai-after-hours-emergency-triage-python
cp .env.example .env
# Edit .env with your credentials
make setup && make run
```

## Implementation Details

### Products used

| Product | Role |
|---------|------|
| Voice API | After-hours routing |
| Inference | Emergency classification |
| Call Control | Conditional forwarding |

## Complete Code

See [app.py](./app.py) for the full implementation.

## FAQ

**Q: Can I use this in production?**
This is a working starting point. Add error handling, persistent storage, and authentication for production use.

**Q: What model should I use?**
Default is Kimi K2.6 via Telnyx Inference. Any model on Telnyx works -- swap the AI_MODEL env var.

## Related Examples

- [Texml Dynamic Call Router](../texml-dynamic-call-router-python/)
- [Ai After Hours Emergency Triage](../ai-after-hours-emergency-triage-python/)
