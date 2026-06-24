#!/usr/bin/env python3
"""Test harness for outbound Telnyx AI voice agents."""

import base64
import html
import json
import os
from typing import Any
from urllib.parse import parse_qs
from uuid import uuid4

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response
import uvicorn

load_dotenv()

API_BASE = "https://api.telnyx.com/v2"
TELNYX_API_KEY = os.getenv("TELNYX_API_KEY", "")
TELNYX_CONNECTION_ID = os.getenv("TELNYX_CONNECTION_ID", "")
TELNYX_FROM_NUMBER = os.getenv("TELNYX_FROM_NUMBER", "")
TELNYX_IVR_ASSISTANT_ID = os.getenv("TELNYX_IVR_ASSISTANT_ID", "")
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")
TELNYX_DRY_RUN = os.getenv("TELNYX_DRY_RUN", "true").lower() != "false"
PORT = int(os.getenv("PORT", "8000"))

app = FastAPI(title="AI Voice Agent Test Harness")
sessions: dict[str, dict[str, Any]] = {}
tool_events: list[dict[str, Any]] = []

SCENARIOS = {
    "support_hold": {
        "name": "Support queue with hold",
        "valid_digits": "12",
        "correct_digit": "1",
        "menu": "for support, press 1. for billing, press 2.",
        "wrong_digit_prompt": "that was not a supported option. for support, press 1.",
        "after_digit": [
            "support. one moment while i connect you.",
            "please hold for the next available agent.",
            "your call is important to us.",
        ],
        "representative": [
            "thanks for holding, this is the support desk.",
            "how can i help you today?",
        ],
    },
    "billing_fast_pickup": {
        "name": "Billing queue with fast pickup",
        "valid_digits": "12",
        "correct_digit": "2",
        "menu": "for support, press 1. for billing, press 2.",
        "wrong_digit_prompt": "that was not a supported option. for billing, press 2.",
        "after_digit": [
            "billing. connecting you now.",
        ],
        "representative": [
            "this is billing, may i have the account number?",
        ],
    },
}


def encode(value: dict[str, Any]) -> str:
    return base64.b64encode(json.dumps(value, separators=(",", ":")).encode()).decode()


async def telnyx_post(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    if TELNYX_DRY_RUN:
        return {
            "data": {
                "id": f"dry-run-{uuid4()}",
                "call_control_id": payload.get("call_control_id", f"dry-run-call-{uuid4()}"),
                "state": "dry_run",
                "path": path,
            }
        }
    headers = {"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(f"{API_BASE}{path}", headers=headers, json=payload)
    if response.is_error:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


def texml(*parts: str) -> Response:
    return Response(
        content="\n".join(['<?xml version="1.0" encoding="UTF-8"?>', "<Response>", *parts, "</Response>"]),
        media_type="application/xml",
    )


def say(text: str) -> str:
    return f"<Say>{html.escape(text)}</Say>"


def public_url(path: str, request: Request) -> str:
    if PUBLIC_BASE_URL:
        return f"{PUBLIC_BASE_URL}{path}"
    return f"{str(request.base_url).rstrip('/')}{path}"


async def request_values(request: Request) -> dict[str, list[str]]:
    if request.method == "GET":
        return {key: [value] for key, value in request.query_params.items()}
    body = (await request.body()).decode()
    if not body:
        return {}
    if "application/json" in request.headers.get("content-type", ""):
        payload = json.loads(body)
        return {key: [str(value)] for key, value in payload.items()}
    return parse_qs(body)


def latest_call_control_id() -> str:
    for session in reversed(list(sessions.values())):
        if session.get("state") != "ended" and session.get("call_control_id"):
            return str(session["call_control_id"])
    return ""


@app.get("/health")
async def health() -> dict[str, Any]:
    return {"ok": True, "dry_run": TELNYX_DRY_RUN, "sessions": len(sessions), "tool_events": len(tool_events)}


@app.get("/scenarios")
async def list_scenarios() -> dict[str, Any]:
    return {"scenarios": SCENARIOS}


@app.api_route("/mock-ivr/{scenario}/start", methods=["GET", "POST"])
async def mock_ivr_start(scenario: str, request: Request) -> Response:
    config = SCENARIOS.get(scenario)
    if not config:
        raise HTTPException(status_code=404, detail="unknown scenario")
    action_url = public_url(f"/mock-ivr/{scenario}/menu", request)
    return texml(
        say(f"test harness scenario. {config['name']}."),
        f'<Gather action="{html.escape(action_url)}" input="dtmf" numDigits="1" timeout="8" validDigits="{html.escape(config["valid_digits"])}">',
        say(str(config["menu"])),
        "</Gather>",
        f"<Redirect>{html.escape(action_url)}</Redirect>",
    )


@app.api_route("/mock-ivr/{scenario}/menu", methods=["GET", "POST"])
async def mock_ivr_menu(scenario: str, request: Request) -> Response:
    config = SCENARIOS.get(scenario)
    if not config:
        raise HTTPException(status_code=404, detail="unknown scenario")
    values = await request_values(request)
    digit = (values.get("Digits") or values.get("digits") or [""])[0]
    if digit != config["correct_digit"]:
        return texml(
            say(str(config["wrong_digit_prompt"])),
            f"<Redirect>{html.escape(public_url(f'/mock-ivr/{scenario}/start', request))}</Redirect>",
        )

    parts = [say(text) for text in config["after_digit"]]
    parts.append('<Pause length="3"/>')
    parts.extend(say(text) for text in config["representative"])
    parts.append('<Pause length="20"/>')
    parts.append(say("test harness call complete. goodbye."))
    parts.append("<Hangup/>")
    return texml(*parts)


@app.post("/calls/outbound")
async def outbound_call(body: dict[str, Any]) -> dict[str, Any]:
    scenario = str(body.get("scenario", "support_hold"))
    if scenario not in SCENARIOS:
        raise HTTPException(status_code=400, detail="unknown scenario")
    session_id = str(uuid4())
    sessions[session_id] = {
        "session_id": session_id,
        "to": body["to"],
        "scenario": scenario,
        "objective": body.get("objective", f"complete the {SCENARIOS[scenario]['name']} test scenario"),
        "context": body.get("context", {}),
        "state": "dialing",
        "expected_digit": SCENARIOS[scenario]["correct_digit"],
    }
    response = await telnyx_post(
        "/calls",
        {
            "connection_id": TELNYX_CONNECTION_ID,
            "from": TELNYX_FROM_NUMBER,
            "to": body["to"],
            "webhook_url": f"{PUBLIC_BASE_URL}/webhooks/telnyx",
            "webhook_url_method": "POST",
            "client_state": encode({"session_id": session_id, "scenario": scenario}),
            "command_id": str(uuid4()),
        },
    )
    sessions[session_id]["call_control_id"] = response.get("data", {}).get("call_control_id")
    return sessions[session_id]


@app.post("/webhooks/telnyx")
async def telnyx_webhook(request: Request) -> dict[str, Any]:
    payload = await request.json()
    data = payload.get("data", {})
    event_type = data.get("event_type", "")
    call_control_id = data.get("payload", {}).get("call_control_id", "")
    session = next((item for item in sessions.values() if item.get("call_control_id") == call_control_id), None)
    if not session:
        return {"ok": True, "ignored": True}
    if event_type == "call.answered":
        session["state"] = "ivr_navigation"
        await telnyx_post(
            f"/calls/{call_control_id}/actions/ai_assistant_start",
            {
                "assistant": {"id": TELNYX_IVR_ASSISTANT_ID},
                "greeting": "",
                "client_state": encode(
                    {
                        "session_id": session["session_id"],
                        "stage": "ivr_navigation",
                        "scenario": session["scenario"],
                        "objective": session["objective"],
                    }
                ),
                "command_id": str(uuid4()),
            },
        )
    elif event_type == "call.hangup":
        session["state"] = "ended"
    return {"ok": True, "event_type": event_type, "state": session["state"]}


@app.post("/tools/send-dtmf")
async def send_dtmf(body: dict[str, Any]) -> dict[str, Any]:
    call_control_id = str(body.get("call_control_id") or latest_call_control_id())
    digits = str(body.get("digits", ""))
    if not call_control_id:
        return {"ok": True, "accepted": False, "reason": "no active call"}
    session = next((item for item in sessions.values() if item.get("call_control_id") == call_control_id), None)
    expected_digit = session.get("expected_digit") if session else None
    matched_expected = digits == expected_digit if expected_digit else None
    event = {"tool": "send_dtmf", "digits": digits, "expected_digit": expected_digit, "matched_expected": matched_expected}
    tool_events.append(event)
    response = await telnyx_post(
        f"/calls/{call_control_id}/actions/send_dtmf",
        {
            "digits": digits,
            "duration_millis": 250,
            "client_state": encode({"tool": "send_dtmf", "matched_expected": matched_expected}),
            "command_id": str(uuid4()),
        },
    )
    return {"ok": True, "accepted": True, **event, "telnyx_response": response}


@app.post("/tools/end-call")
async def end_call(body: dict[str, Any]) -> dict[str, Any]:
    call_control_id = str(body.get("call_control_id") or latest_call_control_id())
    if not call_control_id:
        return {"ok": True, "accepted": False, "reason": "no active call"}
    tool_events.append({"tool": "end_call", "reason": body.get("reason", "")})
    response = await telnyx_post(
        f"/calls/{call_control_id}/actions/hangup",
        {"client_state": encode({"tool": "end_call", "reason": body.get("reason", "")}), "command_id": str(uuid4())},
    )
    return {"ok": True, "accepted": True, "telnyx_response": response}


@app.get("/test-results")
async def test_results() -> dict[str, Any]:
    return {"sessions": list(sessions.values()), "tool_events": tool_events}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=PORT)
