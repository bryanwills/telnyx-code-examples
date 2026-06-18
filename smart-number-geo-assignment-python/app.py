#!/usr/bin/env python3
"""Smart Number Geo-Assignment — automatically purchase and assign local numbers based on caller geography to maximize answer rates."""
import os, json, time, requests
from dotenv import load_dotenv
from flask import Flask, request, jsonify
load_dotenv()
app = Flask(__name__)
TELNYX_API_KEY = os.getenv("TELNYX_API_KEY")
number_cache = {}
assignments = []

def search_local_number(area_code):
    try:
        resp = requests.get("https://api.telnyx.com/v2/available_phone_numbers",
            headers={"Authorization": f"Bearer {TELNYX_API_KEY}"},
            params={"filter[country_code]": "US", "filter[national_destination_code]": area_code, "filter[features][]": ["sms", "voice"], "page[size]": 1}, timeout=15)
        if resp.ok:
            numbers = resp.json().get("data", [])
            return numbers[0]["phone_number"] if numbers else None
    except Exception: pass
    return None

def purchase_number(phone_number):
    try:
        resp = requests.post("https://api.telnyx.com/v2/number_orders",
            headers={"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"},
            json={"phone_numbers": [{"phone_number": phone_number}]}, timeout=15)
        return resp.ok
    except Exception: return False

@app.route("/assign", methods=["POST"])
def assign_number():
    data = request.get_json()
    target_area_code = data.get("area_code")
    use_case = data.get("use_case", "outbound")
    if target_area_code in number_cache:
        return jsonify({"number": number_cache[target_area_code], "source": "cache"}), 200
    number = search_local_number(target_area_code)
    if not number:
        return jsonify({"error": f"No numbers available in area code {target_area_code}"}), 404
    if purchase_number(number):
        number_cache[target_area_code] = number
        assignments.append({"area_code": target_area_code, "number": number, "use_case": use_case, "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")})
        return jsonify({"number": number, "source": "purchased"}), 200
    return jsonify({"error": "Purchase failed"}), 500

@app.route("/lookup-and-assign", methods=["POST"])
def lookup_and_assign():
    data = request.get_json()
    target_number = data.get("target_number", "")
    if len(target_number) >= 5:
        area_code = target_number[2:5] if target_number.startswith("+1") else target_number[:3]
        return assign_number_internal(area_code)
    return jsonify({"error": "Invalid target number"}), 400

def assign_number_internal(area_code):
    if area_code in number_cache:
        return jsonify({"number": number_cache[area_code], "area_code": area_code, "source": "cache"}), 200
    number = search_local_number(area_code)
    if number and purchase_number(number):
        number_cache[area_code] = number
        return jsonify({"number": number, "area_code": area_code, "source": "purchased"}), 200
    return jsonify({"error": "No local number available"}), 404

@app.route("/inventory", methods=["GET"])
def inventory():
    return jsonify({"numbers": number_cache, "total": len(number_cache)}), 200

@app.route("/assignments", methods=["GET"])
def list_assignments():
    return jsonify({"assignments": assignments[-50:]}), 200

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "cached_numbers": len(number_cache)}), 200

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
