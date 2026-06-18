# AI Customer Churn Predictor

## What Does This Example Do?

Feed customer communication patterns (call volumes, support tickets, login frequency) to AI for churn risk scoring with recommended interventions.

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
cd telnyx-code-examples/ai-customer-churn-predictor-python
cp .env.example .env
# Edit .env with your credentials
make setup && make run
```

## Implementation Details

### Products used

| Product | Role |
|---------|------|
| Inference | Churn prediction + risk scoring |
| Reporting API | Usage pattern analysis |

## Complete Code

See [app.py](./app.py) for the full implementation.

## FAQ

**Q: Can I use this in production?**
This is a working starting point. Add error handling, persistent storage, and authentication for production use.

**Q: What model should I use?**
Default is Kimi K2.6 via Telnyx Inference. Any model on Telnyx works -- swap the AI_MODEL env var.

## Related Examples

- [Call Analytics Dashboard Api](../call-analytics-dashboard-api-python/)
- [Ai Competitive Win Loss Call Analyzer](../ai-competitive-win-loss-call-analyzer-python/)
