#!/usr/bin/env python3
"""CDR Usage Analytics Dashboard - pull Call Detail Records, build usage analytics with cost breakdowns, peak-hour analysis, and AI-powered insights."""
import os, json, time, requests, statistics
from dotenv import load_dotenv
from flask import Flask, request, jsonify
load_dotenv()
app = Flask(__name__)
TELNYX_API_KEY = os.getenv("TELNYX_API_KEY")
AI_MODEL = os.getenv("AI_MODEL", "moonshotai/Kimi-K2.6")
API = "https://api.telnyx.com/v2"
INFERENCE_URL = f"{API}/ai/chat/completions"
headers = {"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"}

def fetch_cdrs(start, end, page_size=250):
    try:
        resp = requests.get(f"{API}/reports/cdrs", headers=headers,
            params={"filter[start_date]": start, "filter[end_date]": end, "page[size]": page_size}, timeout=30)
        return resp.json().get("data", [])
    except Exception:
        return []

@app.route("/cdrs", methods=["GET"])
def get_cdrs():
    start = request.args.get("start_date", time.strftime("%Y-%m-%d", time.gmtime(time.time() - 86400)))
    end = request.args.get("end_date", time.strftime("%Y-%m-%d"))
    return jsonify({"data": fetch_cdrs(start, end), "period": {"start": start, "end": end}}), 200

@app.route("/analytics/summary", methods=["GET"])
def usage_summary():
    start = request.args.get("start_date", time.strftime("%Y-%m-%d", time.gmtime(time.time() - 7 * 86400)))
    end = request.args.get("end_date", time.strftime("%Y-%m-%d"))
    cdrs = fetch_cdrs(start, end)
    if not cdrs:
        return jsonify({"period": {"start": start, "end": end}, "total_calls": 0}), 200
    durations = [float(c.get("duration_secs", 0)) for c in cdrs]
    costs = [float(c.get("cost", 0)) for c in cdrs]
    by_dir = {}
    by_type = {}
    by_status = {}
    for c in cdrs:
        by_dir[c.get("direction", "unknown")] = by_dir.get(c.get("direction", "unknown"), 0) + 1
        by_type[c.get("call_type", "unknown")] = by_type.get(c.get("call_type", "unknown"), 0) + 1
        by_status[c.get("status", "unknown")] = by_status.get(c.get("status", "unknown"), 0) + 1
    return jsonify({"period": {"start": start, "end": end}, "total_calls": len(cdrs),
        "duration": {"total_mins": round(sum(durations) / 60, 1),
            "avg_secs": round(statistics.mean(durations), 1),
            "median_secs": round(statistics.median(durations), 1),
            "p95_secs": round(sorted(durations)[int(len(durations) * 0.95)], 1) if durations else 0},
        "cost": {"total_usd": round(sum(costs), 2), "avg_usd": round(statistics.mean(costs), 4),
            "max_usd": round(max(costs), 4) if costs else 0},
        "by_direction": by_dir, "by_type": by_type, "by_status": by_status}), 200

@app.route("/analytics/peak-hours", methods=["GET"])
def peak_hours():
    cdrs = fetch_cdrs(time.strftime("%Y-%m-%d", time.gmtime(time.time() - 7 * 86400)), time.strftime("%Y-%m-%d"))
    hourly = {str(h).zfill(2): 0 for h in range(24)}
    for c in cdrs:
        ts = c.get("start_time", "")
        if "T" in ts:
            hour = ts.split("T")[1][:2]
            hourly[hour] = hourly.get(hour, 0) + 1
    peak = max(hourly, key=hourly.get) if any(hourly.values()) else "00"
    return jsonify({"hourly": hourly, "peak_hour": f"{peak}:00", "total": len(cdrs)}), 200

@app.route("/analytics/top-routes", methods=["GET"])
def top_routes():
    cdrs = fetch_cdrs(time.strftime("%Y-%m-%d", time.gmtime(time.time() - 7 * 86400)), time.strftime("%Y-%m-%d"))
    routes = {}
    for c in cdrs:
        route = f"{c.get('from', '')[:6]}... -> {c.get('to', '')[:6]}..."
        routes.setdefault(route, {"calls": 0, "cost": 0, "duration": 0})
        routes[route]["calls"] += 1
        routes[route]["cost"] += float(c.get("cost", 0))
        routes[route]["duration"] += float(c.get("duration_secs", 0))
    top = sorted(routes.items(), key=lambda x: x[1]["calls"], reverse=True)[:15]
    return jsonify({"top_routes": [{"route": r, "calls": d["calls"], "cost": round(d["cost"], 2),
        "avg_duration_secs": round(d["duration"] / max(d["calls"], 1), 1)} for r, d in top]}), 200

@app.route("/analytics/ai-insights", methods=["GET"])
def ai_insights():
    cdrs = fetch_cdrs(time.strftime("%Y-%m-%d", time.gmtime(time.time() - 7 * 86400)), time.strftime("%Y-%m-%d"))
    if not cdrs:
        return jsonify({"insights": "No data for analysis"}), 200
    durations = [float(c.get("duration_secs", 0)) for c in cdrs]
    costs = [float(c.get("cost", 0)) for c in cdrs]
    short = sum(1 for d in durations if d < 10)
    summary = f"{len(cdrs)} calls, ${sum(costs):.2f} total, avg {statistics.mean(durations):.0f}s, {short} short (<10s, {short*100//max(len(cdrs),1)}%)"
    try:
        resp = requests.post(INFERENCE_URL, headers=headers,
            json={"model": AI_MODEL, "messages": [
                {"role": "system", "content": "You are a telecom analyst. Give 3-5 actionable insights about these calling patterns. Be specific about cost optimization and potential issues."},
                {"role": "user", "content": summary}], "max_tokens": 300, "temperature": 0.3}, timeout=15)
        return jsonify({"summary": summary, "insights": resp.json()["choices"][0]["message"]["content"]}), 200
    except Exception:
        return jsonify({"summary": summary, "insights": "AI unavailable."}), 200

@app.route("/analytics/daily", methods=["GET"])
def daily_breakdown():
    days = int(request.args.get("days", 7))
    daily = []
    for i in range(days):
        date = time.strftime("%Y-%m-%d", time.gmtime(time.time() - i * 86400))
        cdrs = fetch_cdrs(date, date)
        daily.append({"date": date, "calls": len(cdrs),
            "cost": round(sum(float(c.get("cost", 0)) for c in cdrs), 2)})
    return jsonify({"daily": daily}), 200

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
