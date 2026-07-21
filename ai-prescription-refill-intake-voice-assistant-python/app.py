#!/usr/bin/env python3
"""Prescription refill intake with Telnyx AI Assistants."""

import os
import time
import uuid
from typing import Any, Optional

import requests
import telnyx
from dotenv import load_dotenv
from flask import Flask, jsonify, request

load_dotenv()

app = Flask(__name__)

TELNYX_API_KEY = os.getenv("TELNYX_API_KEY", "")
TELNYX_PUBLIC_KEY = os.getenv("TELNYX_PUBLIC_KEY", "")
TELNYX_ASSISTANT_ID = os.getenv("TELNYX_ASSISTANT_ID", "")
TELNYX_PHONE_NUMBER = os.getenv("TELNYX_PHONE_NUMBER", "")
TOOL_SECRET = os.getenv("TOOL_SECRET", "")
PHARMACY_SLACK_WEBHOOK = os.getenv("PHARMACY_SLACK_WEBHOOK", "")

API_BASE = "https://api.telnyx.com/v2"
HEADERS = {"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"}

client = telnyx.Telnyx(api_key=TELNYX_API_KEY, public_key=TELNYX_PUBLIC_KEY or None)

active_calls: dict[str, dict[str, Any]] = {}
refill_requests: list[dict[str, Any]] = []


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def mask_phone(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    digits = "".join(ch for ch in value if ch.isdigit())
    if len(digits) < 4:
        return "****"
    return f"+***{digits[-4:]}"


def verify_telnyx_webhook() -> bool:
    if not TELNYX_PUBLIC_KEY:
        app.logger.warning("TELNYX_PUBLIC_KEY is unset; skipping webhook signature verification")
        return True
    try:
        client.webhooks.unwrap(request.get_data(as_text=True), headers=dict(request.headers))
        return True
    except Exception as exc:
        app.logger.warning("webhook signature verification failed: %s", exc)
        return False


def require_tool_secret() -> tuple[Optional[dict[str, str]], Optional[int]]:
    if not TOOL_SECRET:
        return None, None
    incoming = request.headers.get("X-Refill-Tool-Secret")
    if incoming != TOOL_SECRET:
        return {"error": "unauthorized"}, 401
    return None, None


def telnyx_post(path: str, body: dict[str, Any]) -> dict[str, Any]:
    response = requests.post(f"{API_BASE}{path}", headers=HEADERS, json=body, timeout=15)
    response.raise_for_status()
    return response.json()


def start_assistant(call_control_id: str) -> dict[str, Any]:
    if not TELNYX_ASSISTANT_ID:
        raise RuntimeError("TELNYX_ASSISTANT_ID is required")
    return telnyx_post(
        f"/calls/{call_control_id}/actions/ai_assistant_start",
        {"assistant": {"id": TELNYX_ASSISTANT_ID}},
    )


def send_sms(to_number: str, text: str) -> None:
    if not TELNYX_PHONE_NUMBER:
        app.logger.info("TELNYX_PHONE_NUMBER unset; skipping sms")
        return
    telnyx_post("/messages", {"from": TELNYX_PHONE_NUMBER, "to": to_number, "text": text})


def notify_pharmacy_team(refill_request: dict[str, Any]) -> None:
    if not PHARMACY_SLACK_WEBHOOK:
        return
    text = (
        f"prescription refill request needs review: {refill_request['request_id']} "
        f"for caller {refill_request['caller_masked']}. reason: {refill_request['review_reason']}"
    )
    try:
        requests.post(PHARMACY_SLACK_WEBHOOK, json={"text": text}, timeout=10)
    except requests.RequestException as exc:
        app.logger.warning("pharmacy notification failed: %s", exc)


@app.route("/webhooks/voice", methods=["POST"])
def voice_webhook():
    if not verify_telnyx_webhook():
        return jsonify({"error": "invalid signature"}), 401

    event = request.get_json(silent=True) or {}
    data = event.get("data", {})
    payload = data.get("payload", {})
    event_type = data.get("event_type")
    call_control_id = payload.get("call_control_id")

    if event_type == "call.initiated" and payload.get("direction") == "incoming":
        telnyx_post(f"/calls/{call_control_id}/actions/answer", {})
        return jsonify({"status": "answered"}), 200

    if event_type == "call.answered" and call_control_id:
        result = start_assistant(call_control_id)
        active_calls[call_control_id] = {
            "caller_masked": mask_phone(payload.get("from")),
            "started_at": now_iso(),
            "assistant_id": TELNYX_ASSISTANT_ID,
            "conversation_id": result.get("data", {}).get("conversation_id"),
        }
        return jsonify({"status": "assistant_started", "assistant_id": TELNYX_ASSISTANT_ID}), 200

    if event_type in {"call.hangup", "call.conversation.ended"} and call_control_id:
        active_calls.pop(call_control_id, None)
        return jsonify({"status": "closed"}), 200

    return jsonify({"status": "ignored", "event_type": event_type}), 200


@app.route("/tools/create_refill_request", methods=["POST"])
def create_refill_request():
    error, status = require_tool_secret()
    if error:
        return jsonify(error), status

    body = request.get_json(silent=True) or {}
    request_record = {
        "request_id": f"refill-{uuid.uuid4().hex[:10]}",
        "created_at": now_iso(),
        "caller_masked": mask_phone(body.get("caller_phone")),
        "medication_name": body.get("medication_name", ""),
        "dosage": body.get("dosage", ""),
        "pharmacy_name": body.get("pharmacy_name", ""),
        "days_remaining": body.get("days_remaining"),
        "callback_requested": bool(body.get("callback_requested", False)),
        "minimum_summary": body.get("minimum_summary", ""),
        "status": "created",
    }
    refill_requests.append(request_record)
    return jsonify(request_record), 201


@app.route("/tools/flag_manual_review", methods=["POST"])
def flag_manual_review():
    error, status = require_tool_secret()
    if error:
        return jsonify(error), status

    body = request.get_json(silent=True) or {}
    request_id = body.get("request_id")
    request_record = next((item for item in refill_requests if item["request_id"] == request_id), None)
    if not request_record:
        return jsonify({"error": "request_id not found"}), 404

    request_record["status"] = "manual_review_required"
    request_record["review_reason"] = body.get("review_reason", "")
    request_record["review_priority"] = body.get("review_priority", "routine")
    request_record["flagged_at"] = now_iso()
    notify_pharmacy_team(request_record)
    return jsonify({"status": "manual_review_required", "request_id": request_id}), 200


@app.route("/tools/queue_callback", methods=["POST"])
def queue_callback():
    error, status = require_tool_secret()
    if error:
        return jsonify(error), status

    body = request.get_json(silent=True) or {}
    request_id = body.get("request_id")
    request_record = next((item for item in refill_requests if item["request_id"] == request_id), None)
    if not request_record:
        return jsonify({"error": "request_id not found"}), 404

    request_record["status"] = "callback_queued"
    request_record["callback_window"] = body.get("callback_window", "next business day")
    request_record["queued_at"] = now_iso()
    if body.get("caller_phone"):
        send_sms(body["caller_phone"], "your prescription refill callback request has been queued.")
    return jsonify({"status": "queued", "request_id": request_id}), 200


@app.route("/dynamic-variables", methods=["POST"])
def dynamic_variables():
    return jsonify(
        {
            "dynamic_variables": {
                "clinic_name": os.getenv("CLINIC_NAME", "valley health clinic"),
                "callback_window": os.getenv("CALLBACK_WINDOW", "next business day"),
                "emergency_instruction": "if this may be a medical emergency, hang up and call 9-1-1 immediately",
            }
        }
    ), 200


@app.route("/refills/requests", methods=["GET"])
def list_refill_requests():
    return jsonify({"requests": refill_requests[-50:]}), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify(
        {
            "status": "ok",
            "assistant_configured": bool(TELNYX_ASSISTANT_ID),
            "active_calls": len(active_calls),
            "refill_requests": len(refill_requests),
        }
    ), 200


if __name__ == "__main__":
    app.run(debug=False, host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", "5000")))
