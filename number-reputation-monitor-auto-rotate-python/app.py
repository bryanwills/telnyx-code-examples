#!/usr/bin/env python3
"""Number Reputation Monitor — track outbound number reputation, auto-rotate flagged numbers."""
import os, json, time, requests
from dotenv import load_dotenv
from flask import Flask, request, jsonify
import threading, time as _ttl_time
load_dotenv()
app = Flask(__name__)
TELNYX_API_KEY = os.getenv("TELNYX_API_KEY")
AI_MODEL = os.getenv("AI_MODEL", "MiniMaxAI/MiniMax-M3-MXFP8")
ALERT_NUMBER = os.getenv("ALERT_NUMBER")
INFERENCE_URL = "https://api.telnyx.com/v2/ai/chat/completions"
number_health = {}  # number -> {calls, complaints, answer_rate, flagged}

def _extract_json(text):
    if not text:
        return None
    s = text.strip()
    if s.startswith("```"):
        s = s.split("```", 2)[1]
        if s.startswith("json"):
            s = s[4:]
        s = s.strip()
    start = s.find("{")
    end = s.rfind("}")
    if start != -1 and end != -1 and end > start:
        s = s[start:end + 1]
    return s

def parse_json_response(result):
    payload = _extract_json(result)
    if not payload:
        return None
    return json.loads(payload)

def _start_ttl_cleanup(*stores, ttl_seconds=3600, interval=300):
    def _cleanup():
        while True:
            _ttl_time.sleep(interval)
            cutoff = _ttl_time.time() - ttl_seconds
            for store in stores:
                expired = [k for k, v in store.items()
                           if isinstance(v, dict) and v.get("_ts", _ttl_time.time()) < cutoff]
                for k in expired:
                    store.pop(k, None)
    threading.Thread(target=_cleanup, daemon=True).start()

_start_ttl_cleanup(number_health)

rotation_log = []

def get_numbers():
    try:
        resp = requests.get("https://api.telnyx.com/v2/phone_numbers", headers={"Authorization": f"Bearer {TELNYX_API_KEY}"}, params={"page[size]": 100}, timeout=15)
        if resp.ok:
            return resp.json().get("data", [])
    except Exception:
        pass
    return []

def analyze_health(number_data):
    messages = [{"role": "system", "content": "Analyze phone number health metrics. Return only JSON, no prose, no markdown fences: risk_level (healthy/warning/critical), recommendation (keep/rotate/retire), reasoning (string)."},
        {"role": "user", "content": json.dumps(number_data)}]
    resp = requests.post(INFERENCE_URL, headers={"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"},
        json={"model": AI_MODEL, "messages": messages, "max_tokens": 800, "temperature": 0.2}, timeout=15)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]

@app.route("/scan", methods=["POST"])
def scan_numbers():
    numbers = get_numbers()
    results = []
    for num in numbers[:20]:
        phone = num.get("phone_number", "")
        health = number_health.get(phone, {"calls": 0, "complaints": 0, "answer_rate": 0.5})
        try:
            analysis = parse_json_response(analyze_health({**health, "number": phone}))
            if analysis is None:
                results.append({"number": phone, "analysis": {"risk_level": "unknown"}})
                continue
            number_health[phone] = {**health, "analysis": analysis, "last_scan": time.time()}
            if analysis.get("recommendation") == "rotate":
                rotation_log.append({"number": phone, "reason": analysis.get("reasoning", "flagged"), "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")})
            results.append({"number": phone, "analysis": analysis})
        except Exception:
            results.append({"number": phone, "analysis": {"risk_level": "unknown"}})
    return jsonify({"scanned": len(results), "results": results}), 200

@app.route("/health-report", methods=["GET"])
def health_report():
    return jsonify({"numbers": number_health, "rotations": rotation_log[-20:]}), 200

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "numbers_tracked": len(number_health), "rotations": len(rotation_log)}), 200

if __name__ == "__main__":
    app.run(debug=False, host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", "5000")))
