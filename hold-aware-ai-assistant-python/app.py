#!/usr/bin/env python3
"""Stop a Telnyx AI Assistant during hold and resume it after representative pickup."""

import base64
import json
import os
from datetime import datetime, timezone
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
TRANSCRIPTION_ENGINE = os.getenv("TRANSCRIPTION_ENGINE", "Deepgram")
TRANSCRIPTION_MODEL = os.getenv("TRANSCRIPTION_MODEL", "nova-2")
TRANSCRIPTION_LANGUAGE = os.getenv("TRANSCRIPTION_LANGUAGE", "en")
TELNYX_DRY_RUN = os.getenv("TELNYX_DRY_RUN", "true").lower() != "false"
PORT = int(os.getenv("PORT", "8000"))

app = FastAPI(title="Hold-Aware AI Assistant")
sessions: dict[str, dict[str, Any]] = {}
HOLD_PHRASES = ("please hold", "next available representative", "next available agent", "estimated wait time", "remain on the line", "your call is important")
REP_PHRASES = ("thanks for holding", "thank you for holding", "how can i help", "how may i help", "this is", "my name is", "who am i speaking with")


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


def extract_transcript(payload: dict[str, Any]) -> str:
    found: list[str] = []

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if key in {"transcript", "text"} and isinstance(child, str):
                    found.append(child)
                else:
                    walk(child)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(payload)
    return next((item.strip() for item in found if item.strip()), "")


def latest_session() -> Optional[dict[str, Any]]:
    active = [item for item in sessions.values() if item.get("state") != "ended"]
    return active[-1] if active else None


async def start_assistant(session: dict[str, Any], assistant_id: str, stage: str, greeting: str = "") -> None:
    await telnyx_post(f"/calls/{session['call_control_id']}/actions/ai_assistant_start", {"assistant": {"id": assistant_id}, "greeting": greeting, "client_state": encode({"session_id": session["session_id"], "stage": stage, "objective": session.get("objective"), "recent_transcript": session.get("transcript", [])[-5:]}), "command_id": str(uuid4())})
    session["active_assistant"] = stage


async def enter_hold(session: dict[str, Any], reason: str) -> None:
    if session.get("state") == "hold_monitoring":
        return
    session["state"] = "hold_monitoring"
    session["hold_started_at"] = datetime.now(timezone.utc).isoformat()
    session.setdefault("events", []).append({"event": "hold_detected", "reason": reason})
    if session.get("active_assistant"):
        await telnyx_post(f"/calls/{session['call_control_id']}/actions/ai_assistant_stop", {"client_state": encode({"session_id": session["session_id"], "reason": reason}), "command_id": str(uuid4())})
        session["active_assistant"] = None
    await telnyx_post(f"/calls/{session['call_control_id']}/actions/transcription_start", {"transcription_engine": TRANSCRIPTION_ENGINE, "transcription_engine_config": {"transcription_model": TRANSCRIPTION_MODEL, "language": TRANSCRIPTION_LANGUAGE, "interim_results": True}, "transcription_tracks": "inbound", "client_state": encode({"session_id": session["session_id"], "stage": "hold_monitoring"}), "command_id": str(uuid4())})
    session["transcription_active"] = True


async def representative_detected(session: dict[str, Any], reason: str) -> None:
    if session.get("state") == "live_conversation":
        return
    session["state"] = "live_conversation"
    greeting = f"hi, i am calling to {session.get('objective', 'complete the requested task')}."
    await start_assistant(session, TELNYX_REPRESENTATIVE_ASSISTANT_ID, "representative", greeting)
    if session.get("transcription_active"):
        await telnyx_post(f"/calls/{session['call_control_id']}/actions/transcription_stop", {"client_state": encode({"session_id": session["session_id"], "stage": "live_conversation"}), "command_id": str(uuid4())})
        session["transcription_active"] = False
    session.setdefault("events", []).append({"event": "representative_detected", "reason": reason})


@app.post("/calls/outbound")
async def outbound_call(body: dict[str, Any]) -> dict[str, Any]:
    session_id = str(uuid4())
    sessions[session_id] = {"session_id": session_id, "to": body["to"], "objective": body.get("objective", ""), "target_company": body.get("target_company", ""), "state": "dialing", "transcript": []}
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
    transcript = extract_transcript(payload)
    if transcript:
        session.setdefault("transcript", []).append(transcript)
    lowered = transcript.lower()
    if event_type == "call.answered":
        session["state"] = "ivr_navigation"
        await start_assistant(session, TELNYX_IVR_ASSISTANT_ID, "ivr_navigation")
    elif event_type == "call.hold" or any(phrase in lowered for phrase in HOLD_PHRASES):
        await enter_hold(session, event_type or "hold phrase")
    elif event_type == "call.unhold" or (session.get("state") == "hold_monitoring" and any(phrase in lowered for phrase in REP_PHRASES)):
        await representative_detected(session, event_type or "representative phrase")
    elif event_type == "call.hangup":
        session["state"] = "ended"
    return {"ok": True, "event_type": event_type, "state": session["state"]}


@app.post("/tools/hold-detected")
async def hold_detected_tool(body: dict[str, Any]) -> dict[str, Any]:
    session = latest_session()
    if not session:
        return {"ok": True, "accepted": False, "reason": "no active session"}
    await enter_hold(session, str(body.get("reason", "assistant tool")))
    return {"ok": True, "accepted": True, "state": session["state"]}


@app.get("/sessions")
async def list_sessions() -> list[dict[str, Any]]:
    return list(sessions.values())


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=PORT)
