#!/usr/bin/env python3
"""Create or update the Telnyx AI Assistant used by the multilingual
code-switching voice agent example."""

from __future__ import annotations

import os
import sys
from typing import Any, Optional

import telnyx
from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL = "moonshotai/Kimi-K2.6"
ASSISTANT_NAME = os.getenv("ASSISTANT_NAME", "multilingual code-switching voice agent")

INSTRUCTIONS = """voice: voice ultra katie

you are a friendly multilingual voice agent for a global customer support line.
you can speak english, spanish, portuguese, hindi, and mandarin.

listen carefully to the caller. detect the language they are speaking on every turn.
reply in the same language the caller is using right now.
if the caller switches language mid-conversation or mid-sentence, switch with them.
if you are unsure which language to use, ask in english "which language would you prefer".

keep replies short and natural. this is a phone call.
do not translate unless the caller asks. you are not an interpreter — you are the agent.
if a caller mixes two languages in one sentence, reply in the dominant language.
never say the name of the language out loud unless asked."""

GREETING = (
    "hello, i can speak english, spanish, portuguese, hindi, and mandarin. "
    "please go ahead and speak in any of these languages."
)


def assistant_payload() -> dict[str, Any]:
    return {
        "name": ASSISTANT_NAME,
        "model": os.getenv("AI_MODEL", DEFAULT_MODEL),
        "instructions": INSTRUCTIONS,
        "greeting": GREETING,
        "description": (
            "a multilingual voice agent that detects the caller's language on every turn "
            "and replies in the same language, code-switching mid-conversation when the "
            "caller switches."
        ),
        "enabled_features": ["telephony"],
        "transcription": {
            "model": "deepgram/nova-3",
            "language": "multi",
            "settings": {
                "keyterm": "",
            },
        },
        "interruption_settings": {
            "enable": True,
            "disable_greeting_interruption": True,
            "interrupt_prediction_threshold": 0.4,
            "start_speaking_plan": {
                "wait_seconds": 0.5,
                "transcription_endpointing_plan": {
                    "on_no_punctuation_seconds": 1.5,
                    "on_punctuation_seconds": 0.4,
                    "on_number_seconds": 1.0,
                },
            },
        },
        "telephony_settings": {
            "noise_suppression": "krisp",
            "user_idle_reply_secs": 10,
            "time_limit_secs": 600,
            "recording_settings": {"enabled": False},
        },
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
    api_key = os.getenv("TELNYX_API_KEY")
    if not api_key:
        print("TELNYX_API_KEY is not set", file=sys.stderr)
        sys.exit(1)

    client = telnyx.Telnyx(api_key=api_key)
    payload = assistant_payload()

    connection_id = os.getenv("TELNYX_CONNECTION_ID")
    if connection_id:
        payload["telephony_settings"]["default_texml_app_id"] = connection_id

    assistant_id = find_assistant(client)

    try:
        if assistant_id:
            assistant = client.ai.assistants.update(
                assistant_id=assistant_id, **payload
            )
        else:
            assistant = client.ai.assistants.create(**payload)
    except telnyx.APIStatusError as exc:
        print(
            f"assistant provisioning failed: {exc.status_code} {exc.message}",
            file=sys.stderr,
        )
        raise

    print(f"TELNYX_ASSISTANT_ID={assistant.id}")
    print(f"ASSISTANT_NAME={assistant.name}")
    print(f"AI_MODEL={assistant.model}")


if __name__ == "__main__":
    main()
