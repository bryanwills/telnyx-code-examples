#!/usr/bin/env python3
"""Smart IVR A/B Tester — run two IVR flows simultaneously and track which converts better."""
import os, json, time, random, requests, telnyx
from dotenv import load_dotenv
from flask import Flask, request, jsonify
load_dotenv()
app = Flask(__name__)
client = telnyx.Telnyx(api_key=os.getenv("TELNYX_API_KEY"))
TELNYX_API_KEY = os.getenv("TELNYX_API_KEY")
IVR_NUMBER = os.getenv("IVR_NUMBER")
AGENT_NUMBER = os.getenv("AGENT_NUMBER")
experiments = {}
active_calls = {}

DEFAULT_EXPERIMENT = {
    "variant_a": {"greeting": "Thanks for calling! Press 1 for sales, 2 for support.", "name": "Standard"},
    "variant_b": {"greeting": "Hey! Looking to buy? Press 1. Need help? Press 2. Or just tell me what you need.", "name": "Casual"},
    "traffic_split": 0.5,
    "results": {"a": {"calls": 0, "connected": 0, "hangups": 0}, "b": {"calls": 0, "connected": 0, "hangups": 0}},
}
experiments["default"] = DEFAULT_EXPERIMENT

@app.route("/experiments", methods=["POST"])
def create_experiment():
    data = request.get_json()
    eid = f"EXP-{int(time.time())}"
    experiments[eid] = {"variant_a": data.get("variant_a", {}), "variant_b": data.get("variant_b", {}),
        "traffic_split": data.get("split", 0.5), "results": {"a": {"calls": 0, "connected": 0, "hangups": 0}, "b": {"calls": 0, "connected": 0, "hangups": 0}}}
    return jsonify({"experiment_id": eid}), 200

@app.route("/webhooks/voice", methods=["POST"])
def handle_voice():
    payload = request.get_json()
    event_type = payload.get("data", {}).get("event_type")
    ccid = payload.get("data", {}).get("call_control_id")
    data = payload.get("data", {})
    if event_type == "call.initiated" and data.get("direction") == "incoming":
        exp = experiments.get("default", DEFAULT_EXPERIMENT)
        variant = "a" if random.random() < exp["traffic_split"] else "b"
        exp["results"][variant]["calls"] += 1
        active_calls[ccid] = {"variant": variant, "experiment": "default"}
        client.calls.actions.answer(ccid)
        return jsonify({"status": "answering"}), 200
    elif event_type == "call.answered":
        call = active_calls.get(ccid)
        if call:
            exp = experiments.get(call["experiment"], DEFAULT_EXPERIMENT)
            greeting = exp[f"variant_{call['variant']}"]["greeting"]
            client.calls.actions.speak(ccid, payload=greeting, voice="female", language_code="en-US")
        return jsonify({"status": "greeting"}), 200
    elif event_type == "call.speak.ended":
        client.calls.actions.gather(ccid, input_type="dtmf speech", timeout_secs=10, min_digits=1, max_digits=1, language_code="en-US")
        return jsonify({"status": "listening"}), 200
    elif event_type == "call.gather.ended":
        call = active_calls.get(ccid)
        digits = data.get("digits", "")
        if call and digits in ("1", "2"):
            exp = experiments.get(call["experiment"], DEFAULT_EXPERIMENT)
            exp["results"][call["variant"]]["connected"] += 1
            if AGENT_NUMBER:
                client.calls.actions.transfer(ccid, to=AGENT_NUMBER)
            else:
                client.calls.actions.speak(ccid, payload="Thanks! Connecting you now.", voice="female", language_code="en-US")
        return jsonify({"status": "routed"}), 200
    elif event_type == "call.hangup":
        call = active_calls.pop(ccid, None)
        if call:
            exp = experiments.get(call["experiment"], DEFAULT_EXPERIMENT)
            exp["results"][call["variant"]]["hangups"] += 1
        return jsonify({"status": "ended"}), 200
    return jsonify({"status": "ok"}), 200

@app.route("/experiments/<eid>/results", methods=["GET"])
def get_results(eid):
    exp = experiments.get(eid)
    if not exp: return jsonify({"error": "Not found"}), 404
    results = {}
    for v in ("a", "b"):
        r = exp["results"][v]
        rate = round(r["connected"] / max(r["calls"], 1) * 100, 1)
        results[v] = {"name": exp[f"variant_{v}"].get("name", v), "calls": r["calls"], "connected": r["connected"], "hangups": r["hangups"], "conversion_rate": rate}
    winner = "a" if results["a"]["conversion_rate"] > results["b"]["conversion_rate"] else "b"
    return jsonify({"results": results, "winner": winner, "confidence": "need more data" if results["a"]["calls"] + results["b"]["calls"] < 100 else "significant"}), 200

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "experiments": len(experiments)}), 200

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
