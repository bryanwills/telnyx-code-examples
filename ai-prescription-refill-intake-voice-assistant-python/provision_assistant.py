#!/usr/bin/env python3
"""Create or update the Telnyx AI Assistant used by this example."""

import os
import secrets
import sys
from typing import Any, Optional

import telnyx
from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL = "moonshotai/Kimi-K2.6"
ASSISTANT_NAME = os.getenv("ASSISTANT_NAME", "prescription refill intake voice assistant")

INSTRUCTIONS = """you are a hipaa-aware prescription refill intake voice assistant for {{clinic_name}}.

you are not a doctor or pharmacist. you do not approve refills, deny refills, change medication instructions, diagnose, prescribe, or replace emergency services.

your job is to collect the minimum information needed for staff to review a refill request and route callback needs.

start by saying this is the prescription refill line for {{clinic_name}}. if this may be a medical emergency, tell the caller to hang up and call 9-1-1 immediately.

ask exactly one question at a time. do not ask multiple questions in the same turn. keep each spoken turn to one or two short sentences.

after the emergency reminder, ask only this first question: what medication are you calling to refill

then collect the remaining information one question at a time:
- medication name
- dosage or strength, if they know it
- preferred pharmacy
- how many days of medication they have left
- whether they want a pharmacy team callback

if the caller says to use the number they are calling from, use {{telnyx_end_user_target}} as the callback number. do not ask them to repeat the number unless {{telnyx_end_user_target}} is missing.

do not ask for full social security numbers, insurance ids, payment card numbers, or unnecessary sensitive details.

never tell the caller the refill is approved. say the request will be reviewed by the pharmacy team.

use the tools when routing is clear:
- create_refill_request after you have the medication name and enough callback context.
- flag_manual_review after creating the refill request if the caller is out of medication, has less than two days remaining, mentions a controlled substance, asks for a dosage change, reports side effects, or sounds medically urgent.
- queue_callback after creating the refill request if the caller asks for a callback or the request needs staff follow-up.

keep summaries brief and use only the minimum necessary information for pharmacy team review.

be calm, direct, and empathetic."""

GREETING = (
    "thank you for calling the prescription refill line. "
    "if this may be a medical emergency, please hang up and call 9-1-1 immediately. "
    "what medication are you calling to refill"
)


def required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise SystemExit(f"{name} is required")
    return value


def tool_secret() -> str:
    existing = os.getenv("TOOL_SECRET")
    if existing:
        return existing
    generated = secrets.token_urlsafe(24)
    print(f"generated TOOL_SECRET={generated}")
    print("save this in your .env before running app.py")
    return generated


def webhook_tool(
    base_url: str,
    secret: str,
    name: str,
    description: str,
    path: str,
    schema: dict[str, Any],
) -> dict[str, Any]:
    return {
        "type": "webhook",
        "webhook": {
            "name": name,
            "description": description,
            "url": f"{base_url.rstrip('/')}{path}",
            "method": "POST",
            "headers": [{"name": "X-Refill-Tool-Secret", "value": secret}],
            "body_parameters": schema,
        },
    }


def assistant_payload(base_url: str, secret: str) -> dict[str, Any]:
    refill_schema = {
        "type": "object",
        "properties": {
            "caller_phone": {"type": "string", "description": "caller phone number in e.164 format"},
            "medication_name": {"type": "string", "description": "name of the medication being requested"},
            "dosage": {"type": "string", "description": "dosage or strength, if the caller knows it"},
            "pharmacy_name": {"type": "string", "description": "preferred pharmacy name or location"},
            "days_remaining": {"type": "integer", "description": "number of days of medication remaining, if known"},
            "callback_requested": {"type": "boolean", "description": "whether the caller asked for a callback"},
            "minimum_summary": {"type": "string", "description": "brief minimum necessary refill request summary"},
        },
        "required": ["medication_name", "minimum_summary"],
    }
    request_id_schema = {
        "type": "object",
        "properties": {
            "request_id": {"type": "string", "description": "refill request id returned by create_refill_request"},
            "caller_phone": {"type": "string", "description": "caller phone number in e.164 format"},
            "callback_window": {"type": "string", "description": "requested callback window"},
            "review_priority": {"type": "string", "description": "routine, same_day, or urgent"},
            "review_reason": {"type": "string", "description": "short reason for manual pharmacy review"},
        },
        "required": ["request_id"],
    }
    return {
        "name": ASSISTANT_NAME,
        "model": os.getenv("AI_MODEL", DEFAULT_MODEL),
        "instructions": INSTRUCTIONS,
        "greeting": GREETING,
        "description": "prescription refill intake voice assistant with backend tools for request creation, manual review, and callback queueing.",
        "dynamic_variables_webhook_url": f"{base_url.rstrip('/')}/dynamic-variables",
        "enabled_features": ["telephony"],
        "tools": [
            webhook_tool(
                base_url,
                secret,
                "create_refill_request",
                "create a minimal prescription refill request after the assistant has enough intake context.",
                "/tools/create_refill_request",
                refill_schema,
            ),
            webhook_tool(
                base_url,
                secret,
                "flag_manual_review",
                "flag a refill request for manual pharmacy review when there is urgency, controlled medication context, side effects, dosage changes, or staff follow-up needed.",
                "/tools/flag_manual_review",
                request_id_schema,
            ),
            webhook_tool(
                base_url,
                secret,
                "queue_callback",
                "queue a pharmacy team callback after a refill request is created.",
                "/tools/queue_callback",
                request_id_schema,
            ),
            {"type": "hangup", "hangup": {}},
        ],
    }


def find_assistant(client: telnyx.Telnyx) -> Optional[str]:
    configured = os.getenv("TELNYX_ASSISTANT_ID")
    if configured:
        return configured
    for assistant in client.ai.assistants.list():
        if getattr(assistant, "name", None) == ASSISTANT_NAME:
            return assistant.id
    return None


def main() -> None:
    api_key = required_env("TELNYX_API_KEY")
    public_base_url = required_env("PUBLIC_BASE_URL")
    secret = tool_secret()
    client = telnyx.Telnyx(api_key=api_key)
    payload = assistant_payload(public_base_url, secret)
    assistant_id = find_assistant(client)

    try:
        if assistant_id:
            assistant = client.ai.assistants.update(assistant_id=assistant_id, **payload)
        else:
            assistant = client.ai.assistants.create(**payload)
    except telnyx.APIStatusError as exc:
        print(f"assistant provisioning failed: {exc.status_code} {exc.message}", file=sys.stderr)
        raise

    print(f"TELNYX_ASSISTANT_ID={assistant.id}")
    print(f"ASSISTANT_NAME={assistant.name}")
    print(f"AI_MODEL={assistant.model}")


if __name__ == "__main__":
    main()
