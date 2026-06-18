#!/usr/bin/env python3
"""AI Price Quote Phone Agent — caller describes what they need, AI generates a customized price quote in real time with line items."""
import os, json, time, requests, telnyx
from dotenv import load_dotenv
from flask import Flask, request, jsonify
load_dotenv()
app = Flask(__name__)
client = telnyx.Telnyx(api_key=os.getenv("TELNYX_API_KEY"))
TELNYX_API_KEY = os.getenv("TELNYX_API_KEY")
AI_MODEL = os.getenv("AI_MODEL", "moonshotai/Kimi-K2.6")
QUOTE_NUMBER = os.getenv("QUOTE_NUMBER")
INFERENCE_URL = "https://api.telnyx.com/v2/ai/chat/completions"
active_calls = {}
quotes = []

PRICING = {"voice_minutes": 0.005, "sms_messages": 0.004, "local_numbers": 1.00, "toll_free_numbers": 2.00,
    "sip_trunking_channel": 2.50, "ai_inference_1k_tokens": 0.01, "cloud_storage_gb": 0.05, "fax_pages": 0.07}

SYSTEM_PROMPT = f"You are a pricing specialist. Available products and per-unit pricing: {json.dumps(PRICING)}. Ask what the caller needs, estimate quantities, build a quote. Keep responses under 2 sentences. After gathering requirements (usually 3-4 questions), summarize the quote with line items and monthly total."

def call_inference(messages, max_tokens=250):
    resp = requests.post(INFERENCE_URL, headers={"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"},
        json={"model": AI_MODEL, "messages": messages, "max_tokens": max_tokens, "temperature": 0.5}, timeout=15)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]

@app.route("/webhooks/voice", methods=["POST"])
def handle_voice():
    payload = request.get_json()
    event_type = payload.get("data", {}).get("event_type")
    ccid = payload.get("data", {}).get("call_control_id")
    data = payload.get("data", {})
    call = active_calls.get(ccid)
    if event_type == "call.initiated" and data.get("direction") == "incoming":
        active_calls[ccid] = {"caller": data.get("from"), "conversation": [{"role": "system", "content": SYSTEM_PROMPT}], "start": time.time()}
        client.calls.actions.answer(ccid)
        return jsonify({"status": "answering"}), 200
    elif event_type == "call.answered":
        client.calls.actions.speak(ccid, payload="Hi! I can put together a custom quote for you right now. What kind of communication services are you looking for?", voice="female", language_code="en-US")
        return jsonify({"status": "greeting"}), 200
    elif event_type == "call.speak.ended" and call:
        client.calls.actions.gather(ccid, input_type="speech", end_silence_timeout_secs=2, timeout_secs=20, language_code="en-US")
        return jsonify({"status": "listening"}), 200
    elif event_type == "call.gather.ended" and call:
        speech = data.get("speech", {}).get("result", "")
        if not speech:
            client.calls.actions.speak(ccid, payload="Could you tell me more about what you need?", voice="female", language_code="en-US")
            return jsonify({"status": "reprompting"}), 200
        call["conversation"].append({"role": "user", "content": speech})
        response = call_inference(call["conversation"])
        call["conversation"].append({"role": "assistant", "content": response})
        client.calls.actions.speak(ccid, payload=response, voice="female", language_code="en-US")
        return jsonify({"status": "responding"}), 200
    elif event_type == "call.hangup":
        call = active_calls.pop(ccid, None)
        if call and len(call.get("conversation", [])) > 3:
            extract = [{"role": "system", "content": "Extract the price quote. Return JSON: line_items (list of {product, quantity, unit_price, subtotal}), monthly_total (number), notes (string)."},
                {"role": "user", "content": chr(10).join(f"{m['role']}: {m['content']}" for m in call["conversation"] if m["role"] != "system")}]
            try:
                quote = json.loads(call_inference(extract, max_tokens=400))
                quote["caller"] = call["caller"]
                quote["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
                quotes.append(quote)
            except Exception: pass
        return jsonify({"status": "ended"}), 200
    return jsonify({"status": "ok"}), 200

@app.route("/quotes", methods=["GET"])
def list_quotes():
    return jsonify({"quotes": quotes[-20:]}), 200

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "quotes": len(quotes)}), 200

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
