#!/usr/bin/env python3
"""Hand off from one Telnyx AI Assistant to another with preserved call context."""

import base64
import json
import os
from typing import Any, Optional
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
TELNYX_IVR_ASSISTANT_ID = os.getenv("TELNYX_IVR_ASSISTANT_ID", "")
TELNYX_REPRESENTATIVE_ASSISTANT_ID = os.getenv("TELNYX_REPRESENTATIVE_ASSISTANT_ID", "")
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")
TELNYX_DRY_RUN = os.getenv("TELNYX_DRY_RUN", "true").lower() != "false"
PORT = int(os.getenv("PORT", "8000"))

app = FastAPI(title="AI Assistant Context Handoff")
sessions: dict[str, dict[str, Any]] = {}


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


def latest_session() -> Optional[dict[str, Any]]:
    active = [item for item in sessions.values() if item.get("state") != "ended"]
    return active[-1] if active else None


def assistant_context(session: dict[str, Any], stage: str) -> dict[str, Any]:
    return {"session_id": session["session_id"], "stage": stage, "objective": session.get("objective"), "target_company": session.get("target_company"), "user_context": session.get("context", {}), "recent_transcript": session.get("transcript", [])[-5:]}


@app.post("/calls/outbound")
async def outbound_call(body: dict[str, Any]) -> dict[str, Any]:
    session_id = str(uuid4())
    sessions[session_id] = {"session_id": session_id, "to": body["to"], "objective": body.get("objective", ""), "target_company": body.get("target_company", ""), "context": body.get("context", {}), "transcript": [], "state": "dialing"}
    response = await telnyx_post("/calls", {"connection_id": TELNYX_CONNECTION_ID, "from": TELNYX_FROM_NUMBER, "to": body["to"], "webhook_url": f"{PUBLIC_BASE_URL}/webhooks/telnyx", "webhook_url_method": "POST", "client_state": encode({"session_id": session_id}), "command_id": str(uuid4())})
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
        await telnyx_post(f"/calls/{call_control_id}/actions/ai_assistant_start", {"assistant": {"id": TELNYX_IVR_ASSISTANT_ID}, "greeting": "", "client_state": encode(assistant_context(session, "ivr_navigation")), "command_id": str(uuid4())})
        session["active_assistant"] = "ivr"
    elif event_type == "call.hangup":
        session["state"] = "ended"
        session["active_assistant"] = None
    return {"ok": True, "event_type": event_type, "state": session["state"]}


@app.post("/tools/representative-detected")
async def representative_detected(body: dict[str, Any]) -> dict[str, Any]:
    session = latest_session()
    if not session:
        return {"ok": True, "accepted": False, "reason": "no active session"}
    call_control_id = session["call_control_id"]
    if session.get("active_assistant"):
        await telnyx_post(f"/calls/{call_control_id}/actions/ai_assistant_stop", {"client_state": encode(assistant_context(session, "handoff")), "command_id": str(uuid4())})
    greeting = f"hi, i am calling to {session.get('objective', 'complete the requested task')}."
    await telnyx_post(f"/calls/{call_control_id}/actions/ai_assistant_start", {"assistant": {"id": TELNYX_REPRESENTATIVE_ASSISTANT_ID}, "greeting": greeting, "client_state": encode(assistant_context(session, "representative")), "command_id": str(uuid4())})
    session["state"] = "live_conversation"
    session["active_assistant"] = "representative"
    session.setdefault("events", []).append({"event": "representative_detected", "reason": body.get("reason", "")})
    return {"ok": True, "accepted": True, "state": session["state"]}


@app.get("/sessions")
async def list_sessions() -> list[dict[str, Any]]:
    return list(sessions.values())


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=PORT)
