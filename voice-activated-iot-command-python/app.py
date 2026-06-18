#!/usr/bin/env python3
"""Voice-Activated IoT Command — call a number, speak commands to control IoT devices. AI interprets natural language into device actions dispatched via SIM API."""
import os, json, time, requests, telnyx
from dotenv import load_dotenv
from flask import Flask, request, jsonify
load_dotenv()
app = Flask(__name__)
client = telnyx.Telnyx(api_key=os.getenv("TELNYX_API_KEY"))
TELNYX_API_KEY = os.getenv("TELNYX_API_KEY")
AI_MODEL = os.getenv("AI_MODEL", "moonshotai/Kimi-K2.6")
IOT_NUMBER = os.getenv("IOT_NUMBER")
INFERENCE_URL = "https://api.telnyx.com/v2/ai/chat/completions"
active_calls = {}
command_log = []

DEVICES = {"warehouse_door": {"type": "actuator", "sim_id": "SIM-001", "status": "closed"},
    "cooling_system": {"type": "hvac", "sim_id": "SIM-002", "status": "on", "temp": 68},
    "security_camera_1": {"type": "camera", "sim_id": "SIM-003", "status": "recording"},
    "fleet_tracker_van_1": {"type": "gps", "sim_id": "SIM-004", "status": "active"}}

SYSTEM_PROMPT = f"You are an IoT command interpreter. Available devices: {json.dumps(list(DEVICES.keys()))}. Parse voice commands into device actions. Respond with what you're doing in 1 sentence. Valid actions: open/close, on/off, set_temp, status_check, locate."

def call_inference(messages, max_tokens=150):
    resp = requests.post(INFERENCE_URL, headers={"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"},
        json={"model": AI_MODEL, "messages": messages, "max_tokens": max_tokens, "temperature": 0.3}, timeout=15)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]

def execute_command(device_name, action):
    device = DEVICES.get(device_name)
    if not device: return f"Device {device_name} not found"
    if action in ("open", "close"): device["status"] = action + ("d" if action == "close" else "")
    elif action in ("on", "off"): device["status"] = action
    elif action == "status_check": return f"{device_name}: {device['status']}"
    command_log.append({"device": device_name, "action": action, "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")})
    return f"Done: {device_name} set to {action}"

@app.route("/webhooks/voice", methods=["POST"])
def handle_voice():
    payload = request.get_json()
    event_type = payload.get("data", {}).get("event_type")
    ccid = payload.get("data", {}).get("call_control_id")
    data = payload.get("data", {})
    call = active_calls.get(ccid)
    if event_type == "call.initiated" and data.get("direction") == "incoming":
        active_calls[ccid] = {"conversation": [{"role": "system", "content": SYSTEM_PROMPT}]}
        client.calls.actions.answer(ccid)
        return jsonify({"status": "answering"}), 200
    elif event_type == "call.answered":
        client.calls.actions.speak(ccid, payload="IoT Command Center. What would you like to do?", voice="female", language_code="en-US")
        return jsonify({"status": "greeting"}), 200
    elif event_type == "call.speak.ended" and call:
        client.calls.actions.gather(ccid, input_type="speech", end_silence_timeout_secs=2, timeout_secs=15, language_code="en-US")
        return jsonify({"status": "listening"}), 200
    elif event_type == "call.gather.ended" and call:
        speech = data.get("speech", {}).get("result", "")
        if not speech:
            client.calls.actions.speak(ccid, payload="Didn't catch that. Try again.", voice="female", language_code="en-US")
            return jsonify({"status": "reprompting"}), 200
        call["conversation"].append({"role": "user", "content": speech})
        parse_prompt = [{"role": "system", "content": "Parse IoT command. Return JSON: device (string), action (string), response (string for user)."},
            {"role": "user", "content": speech}]
        try:
            parsed = json.loads(call_inference(parse_prompt))
            result = execute_command(parsed.get("device", ""), parsed.get("action", ""))
            response = parsed.get("response", result)
        except Exception:
            response = call_inference(call["conversation"])
        call["conversation"].append({"role": "assistant", "content": response})
        client.calls.actions.speak(ccid, payload=response + " What else?", voice="female", language_code="en-US")
        return jsonify({"status": "executed"}), 200
    elif event_type == "call.hangup":
        active_calls.pop(ccid, None)
        return jsonify({"status": "ended"}), 200
    return jsonify({"status": "ok"}), 200

@app.route("/devices", methods=["GET"])
def list_devices():
    return jsonify({"devices": DEVICES}), 200

@app.route("/commands", methods=["GET"])
def list_commands():
    return jsonify({"commands": command_log[-50:]}), 200

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "devices": len(DEVICES), "commands": len(command_log)}), 200

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
