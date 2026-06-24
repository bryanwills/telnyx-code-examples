#!/usr/bin/env python3
"""Let a Telnyx AI Assistant request DTMF while the backend sends keypad tones."""

import base64
import io
import json
import math
import os
import wave
from typing import Any
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

app = FastAPI(title="AI IVR DTMF Tool")
sessions: dict[str, dict[str, Any]] = {}
DTMF_FREQUENCIES = {"1": (697, 1209), "2": (697, 1336), "3": (697, 1477), "4": (770, 1209), "5": (770, 1336), "6": (770, 1477), "7": (852, 1209), "8": (852, 1336), "9": (852, 1477), "0": (941, 1336), "*": (941, 1209), "#": (941, 1477)}


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


def latest_call_control_id() -> str:
    for session in reversed(list(sessions.values())):
        if session.get("state") != "ended" and session.get("call_control_id"):
            return str(session["call_control_id"])
    return ""


@app.get("/health")
async def health() -> dict[str, Any]:
    return {"ok": True, "dry_run": TELNYX_DRY_RUN, "sessions": len(sessions)}


@app.post("/calls/outbound")
async def outbound_call(body: dict[str, Any]) -> dict[str, Any]:
    to_number = str(body.get("to", ""))
    if not to_number.startswith("+"):
        raise HTTPException(status_code=400, detail="to must be an E.164 phone number")
    session_id = str(uuid4())
    sessions[session_id] = {"session_id": session_id, "to": to_number, "objective": body.get("objective", ""), "state": "dialing"}
    response = await telnyx_post("/calls", {"connection_id": TELNYX_CONNECTION_ID, "from": TELNYX_FROM_NUMBER, "to": to_number, "webhook_url": f"{PUBLIC_BASE_URL}/webhooks/telnyx", "webhook_url_method": "POST", "client_state": encode({"session_id": session_id}), "command_id": str(uuid4())})
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
        await telnyx_post(f"/calls/{call_control_id}/actions/ai_assistant_start", {"assistant": {"id": TELNYX_IVR_ASSISTANT_ID}, "greeting": "", "client_state": encode({"session_id": session["session_id"], "stage": "ivr_navigation"}), "command_id": str(uuid4())})
    elif event_type == "call.hangup":
        session["state"] = "ended"
    return {"ok": True, "event_type": event_type, "state": session["state"]}


@app.post("/tools/send-dtmf")
async def send_dtmf_tool(request: Request) -> dict[str, Any]:
    body = await request.json()
    digits = str(body.get("digits", ""))
    if not digits or any(char not in DTMF_FREQUENCIES for char in digits):
        return {"ok": True, "accepted": False, "reason": "digits must contain only 0-9, *, or #"}
    call_control_id = str(body.get("call_control_id") or latest_call_control_id())
    if not call_control_id:
        return {"ok": True, "accepted": False, "reason": "no active call_control_id"}
    response = await telnyx_post(f"/calls/{call_control_id}/actions/send_dtmf", {"digits": digits, "duration_millis": 250, "client_state": encode({"tool": "send_dtmf", "reason": body.get("reason", "")}), "command_id": str(uuid4())})
    if PUBLIC_BASE_URL:
        await telnyx_post(f"/calls/{call_control_id}/actions/playback_start", {"audio_url": f"{PUBLIC_BASE_URL}/media/dtmf/{digits[0]}.wav", "audio_type": "wav", "target_legs": "both", "cache_audio": True, "client_state": encode({"tool": "dtmf_feedback"}), "command_id": str(uuid4())})
    return {"ok": True, "accepted": True, "telnyx_response": response}


@app.get("/media/dtmf/{digit}.wav")
async def dtmf_wav(digit: str) -> Response:
    if digit not in DTMF_FREQUENCIES:
        raise HTTPException(status_code=404, detail="unknown digit")
    sample_rate = 8000
    frames = bytearray()
    f1, f2 = DTMF_FREQUENCIES[digit]
    for n in range(int(sample_rate * 0.18)):
        sample = int(16000 * (math.sin(2 * math.pi * f1 * n / sample_rate) + math.sin(2 * math.pi * f2 * n / sample_rate)) / 2)
        frames += sample.to_bytes(2, "little", signed=True)
    output = io.BytesIO()
    with wave.open(output, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(bytes(frames))
    return Response(content=output.getvalue(), media_type="audio/wav")


@app.get("/sessions")
async def list_sessions() -> list[dict[str, Any]]:
    return list(sessions.values())


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=PORT)
