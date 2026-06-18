#!/usr/bin/env python3
"""Edge Compute Webhook Proxy - local dev server for testing webhook routing logic before deploying to Telnyx Edge. Includes the Edge function source and deployment instructions."""
import os, json, time, requests
from dotenv import load_dotenv
from flask import Flask, request, jsonify
load_dotenv()
app = Flask(__name__)
TELNYX_API_KEY = os.getenv("TELNYX_API_KEY")
VOICE_HANDLER_URL = os.getenv("VOICE_HANDLER_URL", "")
MESSAGE_HANDLER_URL = os.getenv("MESSAGE_HANDLER_URL", "")
DEFAULT_HANDLER_URL = os.getenv("DEFAULT_HANDLER_URL", "")
event_log = []
route_stats = {}

# The actual Edge function you deploy with telnyx-edge ship
EDGE_FUNCTION_JS = """
// Deploy: telnyx-edge new-func --name webhook-proxy && telnyx-edge ship
export default {
  async fetch(request, env) {
    const payload = await request.json();
    const eventType = payload?.data?.event_type || "unknown";
    const routes = {
      "call.initiated": env.VOICE_HANDLER_URL,
      "call.answered": env.VOICE_HANDLER_URL,
      "call.hangup": env.VOICE_HANDLER_URL,
      "message.received": env.MESSAGE_HANDLER_URL,
      "message.sent": env.MESSAGE_HANDLER_URL,
    };
    const target = routes[eventType] || env.DEFAULT_HANDLER_URL;
    if (target) {
      await fetch(target, { method: "POST",
        headers: { "Content-Type": "application/json", "X-Edge-Processed": "true" },
        body: JSON.stringify(payload) });
    }
    return new Response(JSON.stringify({ status: "routed", event: eventType }));
  }
};
"""

ROUTES = {"call.initiated": "voice", "call.answered": "voice", "call.hangup": "voice",
    "call.speak.ended": "voice", "call.gather.ended": "voice",
    "message.received": "message", "message.sent": "message", "message.finalized": "message"}

def forward(url, payload):
    if not url:
        return {"forwarded": False, "reason": "no_target_url"}
    try:
        resp = requests.post(url, json=payload,
            headers={"Content-Type": "application/json", "X-Edge-Processed": "true"}, timeout=10)
        return {"forwarded": True, "status_code": resp.status_code}
    except Exception as e:
        return {"forwarded": False, "error": str(e)}

@app.route("/webhook", methods=["POST"])
def handle():
    payload = request.get_json()
    event_type = payload.get("data", {}).get("event_type", "unknown")
    cat = ROUTES.get(event_type, "default")
    targets = {"voice": VOICE_HANDLER_URL, "message": MESSAGE_HANDLER_URL, "default": DEFAULT_HANDLER_URL}
    result = forward(targets.get(cat, DEFAULT_HANDLER_URL), payload)
    event_log.append({"event": event_type, "route": cat, "forwarded": result.get("forwarded"),
        "at": time.strftime("%Y-%m-%dT%H:%M:%SZ")})
    route_stats[cat] = route_stats.get(cat, 0) + 1
    return jsonify({"event": event_type, "route": cat, "forward": result}), 200

@app.route("/edge-source", methods=["GET"])
def edge_source():
    return jsonify({"source": EDGE_FUNCTION_JS,
        "deploy": ["npm install -g @telnyx/telnyx-edge",
            "telnyx-edge auth api-key set $TELNYX_API_KEY",
            "telnyx-edge new-func --name webhook-proxy",
            "# paste source into index.js",
            "telnyx-edge secrets add VOICE_HANDLER_URL <url>",
            "telnyx-edge ship"],
        "note": "This Flask server simulates the same routing logic locally for testing."}), 200

@app.route("/routes", methods=["GET"])
def list_routes():
    return jsonify({"routes": ROUTES, "targets": {"voice": VOICE_HANDLER_URL or "(not set)",
        "message": MESSAGE_HANDLER_URL or "(not set)", "default": DEFAULT_HANDLER_URL or "(not set)"}}), 200

@app.route("/stats", methods=["GET"])
def stats():
    return jsonify({"stats": route_stats, "total": len(event_log), "recent": event_log[-20:]}), 200

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "events": len(event_log),
        "note": "Local dev server. Deploy Edge function for production latency."}), 200

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
