#!/usr/bin/env python3
"""Place an outbound Telnyx call and start an AI Assistant after answer."""

import base64
import json
import os
from typing import Any
from uuid import uuid4

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
import uvicorn

load_dotenv()

API_BASE = "https://api.telnyx.com/v2"
TELNYX_API_KEY = os.getenv("TELNYX_API_KEY", "")
TELNYX_CONNECTION_ID = os.getenv("TELNYX_CONNECTION_ID", "")
TELNYX_FROM_NUMBER = os.getenv("TELNYX_FROM_NUMBER", "")
TELNYX_ASSISTANT_ID = os.getenv("TELNYX_ASSISTANT_ID", "")
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")
TELNYX_DRY_RUN = os.getenv("TELNYX_DRY_RUN", "true").lower() != "false"
PORT = int(os.getenv("PORT", "8000"))

app = FastAPI(title="Outbound AI Assistant Call")
sessions: dict[str, dict[str, Any]] = {}


def required_missing() -> list[str]:
    if TELNYX_DRY_RUN:
        return []
    required = {
        "TELNYX_API_KEY": TELNYX_API_KEY,
        "TELNYX_CONNECTION_ID": TELNYX_CONNECTION_ID,
        "TELNYX_FROM_NUMBER": TELNYX_FROM_NUMBER,
        "TELNYX_ASSISTANT_ID": TELNYX_ASSISTANT_ID,
        "PUBLIC_BASE_URL": PUBLIC_BASE_URL,
    }
    return [name for name, value in required.items() if not value]


def headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"}


def encode_client_state(value: dict[str, Any]) -> str:
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
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(f"{API_BASE}{path}", headers=headers(), json=payload)
    if response.is_error:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


@app.get("/health")
async def health() -> dict[str, Any]:
    missing = required_missing()
    return {"ok": not missing, "dry_run": TELNYX_DRY_RUN, "missing": missing, "sessions": len(sessions)}


@app.post("/calls/outbound")
async def outbound_call(body: dict[str, Any]) -> dict[str, Any]:
    missing = required_missing()
    if missing:
        raise HTTPException(status_code=400, detail={"missing": missing})
    to_number = str(body.get("to", ""))
    if not to_number.startswith("+"):
        raise HTTPException(status_code=400, detail="to must be an E.164 phone number")

    session_id = str(uuid4())
    sessions[session_id] = {"session_id": session_id, "to": to_number, "state": "dialing"}
    response = await telnyx_post(
        "/calls",
        {
            "connection_id": TELNYX_CONNECTION_ID,
            "from": TELNYX_FROM_NUMBER,
            "to": to_number,
            "webhook_url": f"{PUBLIC_BASE_URL}/webhooks/telnyx",
            "webhook_url_method": "POST",
            "client_state": encode_client_state({"session_id": session_id}),
            "command_id": str(uuid4()),
        },
    )
    data = response.get("data", {})
    sessions[session_id]["call_control_id"] = data.get("call_control_id")
    return sessions[session_id]


@app.post("/webhooks/telnyx")
async def telnyx_webhook(request: Request) -> dict[str, Any]:
    payload = await request.json()
    data = payload.get("data", {})
    event_payload = data.get("payload", {})
    event_type = data.get("event_type", "")
    call_control_id = event_payload.get("call_control_id", "")
    session = next((item for item in sessions.values() if item.get("call_control_id") == call_control_id), None)
    if not session:
        return {"ok": True, "ignored": True, "event_type": event_type}

    if event_type == "call.answered":
        session["state"] = "assistant_started"
        await telnyx_post(
            f"/calls/{call_control_id}/actions/ai_assistant_start",
            {
                "assistant": {"id": TELNYX_ASSISTANT_ID},
                "client_state": encode_client_state({"session_id": session["session_id"], "stage": "assistant"}),
                "command_id": str(uuid4()),
            },
        )
    elif event_type == "call.hangup":
        session["state"] = "ended"
    return {"ok": True, "event_type": event_type, "state": session["state"]}


@app.get("/sessions")
async def list_sessions() -> list[dict[str, Any]]:
    return list(sessions.values())


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=PORT)
