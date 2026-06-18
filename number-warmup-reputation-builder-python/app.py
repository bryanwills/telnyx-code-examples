#!/usr/bin/env python3
"""Number Warmup & Reputation Builder — gradually ramp SMS volume on new numbers to build carrier reputation and avoid spam flags."""
import os, json, time, requests
from dotenv import load_dotenv
from flask import Flask, request, jsonify
load_dotenv()
app = Flask(__name__)
TELNYX_API_KEY = os.getenv("TELNYX_API_KEY")
MESSAGING_PROFILE_ID = os.getenv("MESSAGING_PROFILE_ID", "")
warmup_numbers = {}
warmup_log = []

WARMUP_SCHEDULE = [
    {"day": 1, "max_messages": 10, "delay_seconds": 300},
    {"day": 2, "max_messages": 25, "delay_seconds": 180},
    {"day": 3, "max_messages": 50, "delay_seconds": 120},
    {"day": 5, "max_messages": 100, "delay_seconds": 60},
    {"day": 7, "max_messages": 250, "delay_seconds": 30},
    {"day": 10, "max_messages": 500, "delay_seconds": 15},
    {"day": 14, "max_messages": 1000, "delay_seconds": 10},
]

@app.route("/warmup/start", methods=["POST"])
def start_warmup():
    data = request.get_json()
    number = data.get("number")
    warmup_numbers[number] = {"started": time.time(), "day": 0, "total_sent": 0, "today_sent": 0, "status": "warming",
        "errors": 0, "last_sent": 0}
    return jsonify({"status": "started", "number": number, "schedule": WARMUP_SCHEDULE}), 200

@app.route("/warmup/send", methods=["POST"])
def send_warmup():
    data = request.get_json()
    number = data.get("from_number")
    to = data.get("to")
    text = data.get("text", "Test message for number warmup")
    wp = warmup_numbers.get(number)
    if not wp: return jsonify({"error": "Number not in warmup"}), 404
    days_elapsed = int((time.time() - wp["started"]) / 86400)
    wp["day"] = days_elapsed
    current_limit = 10
    current_delay = 300
    for step in WARMUP_SCHEDULE:
        if days_elapsed >= step["day"]:
            current_limit = step["max_messages"]
            current_delay = step["delay_seconds"]
    if wp["today_sent"] >= current_limit:
        return jsonify({"error": "Daily limit reached", "limit": current_limit, "sent": wp["today_sent"]}), 429
    elapsed = time.time() - wp["last_sent"]
    if elapsed < current_delay:
        return jsonify({"error": "Too soon", "wait_seconds": int(current_delay - elapsed)}), 429
    try:
        resp = requests.post("https://api.telnyx.com/v2/messages",
            headers={"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"},
            json={"from": number, "to": to, "text": text, "messaging_profile_id": MESSAGING_PROFILE_ID}, timeout=10)
        if resp.ok:
            wp["total_sent"] += 1
            wp["today_sent"] += 1
            wp["last_sent"] = time.time()
            warmup_log.append({"number": number, "to": to, "day": days_elapsed, "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")})
            return jsonify({"status": "sent", "day": days_elapsed, "today_count": wp["today_sent"], "limit": current_limit}), 200
        else:
            wp["errors"] += 1
            return jsonify({"error": resp.text}), resp.status_code
    except Exception as e:
        wp["errors"] += 1
        return jsonify({"error": str(e)}), 500

@app.route("/warmup/status", methods=["GET"])
def warmup_status():
    status = {}
    for num, wp in warmup_numbers.items():
        days = int((time.time() - wp["started"]) / 86400)
        current_limit = 10
        for step in WARMUP_SCHEDULE:
            if days >= step["day"]: current_limit = step["max_messages"]
        ready = days >= 14
        status[num] = {"day": days, "total_sent": wp["total_sent"], "today_sent": wp["today_sent"],
            "current_limit": current_limit, "errors": wp["errors"], "ready": ready}
    return jsonify({"numbers": status}), 200

@app.route("/warmup/reset-daily", methods=["POST"])
def reset_daily():
    for wp in warmup_numbers.values():
        wp["today_sent"] = 0
    return jsonify({"status": "reset", "numbers": len(warmup_numbers)}), 200

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "warming_numbers": len(warmup_numbers)}), 200

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
