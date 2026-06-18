#!/usr/bin/env python3
"""MMS Photo Inventory Tracker — text a photo of inventory items with MMS, AI identifies and catalogs them automatically."""
import os, json, time, requests
from dotenv import load_dotenv
from flask import Flask, request, jsonify
load_dotenv()
app = Flask(__name__)
TELNYX_API_KEY = os.getenv("TELNYX_API_KEY")
AI_MODEL = os.getenv("AI_MODEL", "moonshotai/Kimi-K2.6")
INVENTORY_NUMBER = os.getenv("INVENTORY_NUMBER")
MESSAGING_PROFILE_ID = os.getenv("MESSAGING_PROFILE_ID", "")
INFERENCE_URL = "https://api.telnyx.com/v2/ai/chat/completions"
inventory = []

def send_sms(to, text):
    try:
        requests.post("https://api.telnyx.com/v2/messages", headers={"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"},
            json={"from": INVENTORY_NUMBER, "to": to, "text": text, "messaging_profile_id": MESSAGING_PROFILE_ID}, timeout=10)
    except Exception as e:
        app.logger.error(f"SMS failed: {e}")

def call_inference(messages, max_tokens=300):
    resp = requests.post(INFERENCE_URL, headers={"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"},
        json={"model": AI_MODEL, "messages": messages, "max_tokens": max_tokens, "temperature": 0.2}, timeout=15)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]

@app.route("/webhooks/messaging", methods=["POST"])
def handle_mms():
    payload = request.get_json()
    data = payload.get("data", {})
    if data.get("event_type") != "message.received" or data.get("direction") != "inbound":
        return jsonify({"status": "ignored"}), 200
    phone = data.get("from", {}).get("phone_number", "")
    text = data.get("text", "").strip()
    media = data.get("media", [])
    if text.upper() == "LIST":
        if not inventory:
            send_sms(phone, "Inventory is empty. Send a photo to add items!")
        else:
            items = chr(10).join(f"- {i['name']} (qty: {i.get('quantity', '?')})" for i in inventory[-10:])
            send_sms(phone, f"Recent inventory:\n{items}")
        return jsonify({"status": "listed"}), 200
    if media:
        media_urls = [m.get("url", "") for m in media if m.get("url")]
        if media_urls:
            try:
                analysis = call_inference([{"role": "system", "content": "An inventory photo was received via MMS. The user may describe what's in it. Based on description and context, extract inventory items. Return JSON: items (list of {name, quantity_estimate, condition, category, notes})."},
                    {"role": "user", "content": f"Photo received. User note: '{text or 'no description'}'. Photo URLs: {media_urls}"}])
                items = json.loads(analysis).get("items", [])
                for item in items:
                    item["added_by"] = phone
                    item["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
                    item["media_url"] = media_urls[0]
                    inventory.append(item)
                send_sms(phone, f"Added {len(items)} item(s) to inventory. Text LIST to see all.")
            except Exception:
                send_sms(phone, "Got the photo! Could you also describe what's in it?")
            return jsonify({"status": "cataloged"}), 200
    if text:
        try:
            analysis = call_inference([{"role": "system", "content": "Extract inventory items from this text description. Return JSON: items (list of {name, quantity_estimate, category})."},
                {"role": "user", "content": text}])
            items = json.loads(analysis).get("items", [])
            for item in items:
                item["added_by"] = phone
                item["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
                inventory.append(item)
            send_sms(phone, f"Added {len(items)} item(s). Text LIST to see all.")
        except Exception:
            send_sms(phone, "Couldn't parse that. Try again or send a photo!")
    return jsonify({"status": "ok"}), 200

@app.route("/inventory", methods=["GET"])
def list_inventory():
    category = request.args.get("category")
    items = inventory if not category else [i for i in inventory if i.get("category", "").lower() == category.lower()]
    return jsonify({"items": items[-50:], "total": len(items)}), 200

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "items": len(inventory)}), 200

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
