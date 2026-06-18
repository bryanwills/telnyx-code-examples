# AI Call Center Quality Scorer

## What Does This Example Do?

Feed call transcripts to AI for automatic agent scoring across 5 dimensions: greeting, compliance, empathy, resolution, and talk ratio. Generates coaching notes.

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
cd telnyx-code-examples/ai-call-center-quality-scorer-python
cp .env.example .env
# Edit .env with your credentials
make setup && make run
```

## Implementation Details

### Products used

| Product | Role |
|---------|------|
| Inference | Multi-dimensional scoring |
| Reporting | Aggregate quality metrics |

## Complete Code

See [app.py](./app.py) for the full implementation.

## FAQ

**Q: Can I use this in production?**
This is a working starting point. Add error handling, persistent storage, and authentication for production use.

**Q: What model should I use?**
Default is Kimi K2.6 via Telnyx Inference. Any model on Telnyx works -- swap the AI_MODEL env var.

## Related Examples

- [Call Recording Ai Summarizer](../call-recording-ai-summarizer-python/)
- [Compliance Call Recorder Ai Auditor](../compliance-call-recorder-ai-auditor-python/)
