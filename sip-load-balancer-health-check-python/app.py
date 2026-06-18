#!/usr/bin/env python3
"""SIP Load Balancer Health Check — monitor SIP trunk health across multiple endpoints, auto-failover to healthy trunks, track uptime metrics."""
import os, json, time, requests
from dotenv import load_dotenv
from flask import Flask, request, jsonify
load_dotenv()
app = Flask(__name__)
TELNYX_API_KEY = os.getenv("TELNYX_API_KEY")

endpoints = {
    "primary": {"host": "sip1.example.com", "port": 5060, "weight": 70, "status": "healthy", "last_check": 0, "uptime_checks": 0, "uptime_passes": 0},
    "secondary": {"host": "sip2.example.com", "port": 5060, "weight": 20, "status": "healthy", "last_check": 0, "uptime_checks": 0, "uptime_passes": 0},
    "tertiary": {"host": "sip3.example.com", "port": 5060, "weight": 10, "status": "healthy", "last_check": 0, "uptime_checks": 0, "uptime_passes": 0},
}
health_log = []

@app.route("/check", methods=["POST"])
def health_check():
    results = []
    for name, ep in endpoints.items():
        ep["uptime_checks"] += 1
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((ep["host"], ep["port"]))
            sock.close()
            healthy = result == 0
        except Exception:
            healthy = False
        old_status = ep["status"]
        ep["status"] = "healthy" if healthy else "unhealthy"
        ep["last_check"] = time.time()
        if healthy: ep["uptime_passes"] += 1
        if old_status != ep["status"]:
            health_log.append({"endpoint": name, "old": old_status, "new": ep["status"], "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")})
        results.append({"endpoint": name, "host": ep["host"], "status": ep["status"], "uptime_pct": round(ep["uptime_passes"] / max(ep["uptime_checks"], 1) * 100, 1)})
    return jsonify({"results": results}), 200

@app.route("/route", methods=["GET"])
def get_route():
    healthy = {n: e for n, e in endpoints.items() if e["status"] == "healthy"}
    if not healthy:
        return jsonify({"error": "No healthy endpoints", "fallback": "primary"}), 503
    total_weight = sum(e["weight"] for e in healthy.values())
    route = max(healthy.items(), key=lambda x: x[1]["weight"])
    return jsonify({"endpoint": route[0], "host": route[1]["host"], "port": route[1]["port"],
        "healthy_count": len(healthy), "total_endpoints": len(endpoints)}), 200

@app.route("/endpoints", methods=["GET"])
def list_endpoints():
    return jsonify({"endpoints": {n: {"host": e["host"], "status": e["status"],
        "uptime": round(e["uptime_passes"] / max(e["uptime_checks"], 1) * 100, 1)} for n, e in endpoints.items()}}), 200

@app.route("/endpoints", methods=["POST"])
def add_endpoint():
    data = request.get_json()
    name = data.get("name")
    endpoints[name] = {"host": data.get("host"), "port": data.get("port", 5060), "weight": data.get("weight", 10),
        "status": "unknown", "last_check": 0, "uptime_checks": 0, "uptime_passes": 0}
    return jsonify({"status": "added"}), 200

@app.route("/log", methods=["GET"])
def get_log():
    return jsonify({"log": health_log[-100:]}), 200

@app.route("/health", methods=["GET"])
def health():
    healthy = sum(1 for e in endpoints.values() if e["status"] == "healthy")
    return jsonify({"status": "ok", "healthy": healthy, "total": len(endpoints)}), 200

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
