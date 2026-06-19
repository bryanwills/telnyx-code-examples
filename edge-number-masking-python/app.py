"""Edge Number Masking — marketplace proxy number pool for two-party anonymity.
Dynamically assigns number pairs per booking, routes calls through, records for
disputes, auto-expires masks at checkout."""
import os, json, time, base64, logging
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import requests
import boto3

load_dotenv()
app = Flask(__name__)
app.logger.setLevel(logging.INFO)

TELNYX_API_KEY = os.getenv("TELNYX_API_KEY")
TELNYX_PUBLIC_KEY = os.getenv("TELNYX_PUBLIC_KEY", "")
STORAGE_BUCKET = os.getenv("STORAGE_BUCKET", "call-recordings")
MESSAGING_PROFILE = os.getenv("MESSAGING_PROFILE_ID", "")
HOST = os.getenv("HOST", "127.0.0.1")
HEADERS = {"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"}

s3 = boto3.client("s3", endpoint_url="https://storage.telnyx.com",
                   aws_access_key_id=TELNYX_API_KEY, aws_secret_access_key=TELNYX_API_KEY)

proxy_pool = []  # Available proxy numbers
active_masks = {}  # proxy_number -> {party_a, party_b, booking_id, expires_at}
bookings = {}  # booking_id -> mask info
MAX_ENTRIES = 10000

def ttl_cleanup_masks():
    now = time.time()
    expired = [k for k, v in active_masks.items() if v.get("expires_at", float("inf")) < now]
    for k in expired:
        booking_id = active_masks[k].get("booking_id")
        proxy_pool.append(k)
        del active_masks[k]
        bookings.pop(booking_id, None)
        app.logger.info("Expired mask for booking %s, returned %s to pool", booking_id, k)

def encode_state(data):
    return base64.b64encode(json.dumps(data).encode()).decode()

def decode_state(b64):
    try: return json.loads(base64.b64decode(b64).decode())
    except: return {}

@app.route("/pool", methods=["POST"])
def add_to_pool():
    data = request.get_json() or {}
    numbers = data.get("numbers", [])
    if not numbers:
        return jsonify({"error": "numbers array required"}), 400
    proxy_pool.extend(numbers)
    return jsonify({"status": "added", "pool_size": len(proxy_pool)})

@app.route("/bookings", methods=["POST"])
def create_booking():
    ttl_cleanup_masks()
    data = request.get_json() or {}
    party_a = data.get("party_a")
    party_b = data.get("party_b")
    booking_id = data.get("booking_id", f"book-{int(time.time())}")
    hours = data.get("duration_hours", 24)
    if not party_a or not party_b:
        return jsonify({"error": "party_a and party_b required"}), 400
    if not proxy_pool:
        return jsonify({"error": "No proxy numbers available"}), 503
    proxy = proxy_pool.pop(0)
    mask = {"proxy": proxy, "party_a": party_a, "party_b": party_b,
            "booking_id": booking_id, "expires_at": time.time() + hours * 3600, "created": time.time()}
    active_masks[proxy] = mask
    bookings[booking_id] = mask
    return jsonify({"status": "created", "booking_id": booking_id, "proxy_number": proxy,
                    "expires_at": mask["expires_at"]})

@app.route("/bookings/<booking_id>", methods=["DELETE"])
def expire_booking(booking_id):
    mask = bookings.pop(booking_id, None)
    if not mask:
        return jsonify({"error": "Not found"}), 404
    proxy = mask["proxy"]
    active_masks.pop(proxy, None)
    proxy_pool.append(proxy)
    return jsonify({"status": "expired", "booking_id": booking_id, "proxy_returned": proxy})

@app.route("/webhooks/voice", methods=["POST"])
def handle_voice():
    payload = request.get_json()
    if not payload:
        return jsonify({"error": "No payload"}), 400
    event = payload.get("data", {})
    event_type = event.get("event_type", "")
    ep = event.get("payload", {})
    cc_id = ep.get("call_control_id")
    if not cc_id:
        return jsonify({"error": "Missing call_control_id"}), 400
    ttl_cleanup_masks()

    if event_type == "call.initiated" and ep.get("direction") == "incoming":
        called = ep.get("to", "")
        caller = ep.get("from", "")
        mask = active_masks.get(called)
        if not mask:
            requests.post(f"https://api.telnyx.com/v2/calls/{cc_id}/actions/reject",
                          headers=HEADERS, timeout=10, json={"cause": "UNALLOCATED_NUMBER"})
            return jsonify({"status": "no_mask"})
        target = mask["party_b"] if caller == mask["party_a"] else mask["party_a"]
        requests.post(f"https://api.telnyx.com/v2/calls/{cc_id}/actions/answer",
                      headers=HEADERS, timeout=10,
                      json={"client_state": encode_state({"target": target, "booking": mask["booking_id"]})})

    elif event_type == "call.answered":
        state = decode_state(ep.get("client_state", ""))
        target = state.get("target")
        if target:
            requests.post(f"https://api.telnyx.com/v2/calls/{cc_id}/actions/transfer",
                          headers=HEADERS, timeout=10, json={"to": target})
            requests.post(f"https://api.telnyx.com/v2/calls/{cc_id}/actions/record_start",
                          headers=HEADERS, timeout=10, json={"format": "mp3", "channels": "dual"})

    elif event_type == "call.recording.saved":
        recording_url = ep.get("recording_urls", {}).get("mp3")
        if recording_url:
            try:
                audio = requests.get(recording_url, headers=HEADERS, timeout=30).content
                key = f"recordings/{ep.get('call_session_id', 'unknown')}.mp3"
                s3.put_object(Bucket=STORAGE_BUCKET, Key=key, Body=audio, ContentType="audio/mpeg")
                app.logger.info("Archived recording: %s", key)
            except Exception as e:
                app.logger.error("Recording archive failed: %s", e)

    elif event_type == "call.hangup":
        pass

    return jsonify({"status": "ok"})

@app.route("/bookings", methods=["GET"])
def list_bookings():
    ttl_cleanup_masks()
    return jsonify({"bookings": list(bookings.values()), "pool_available": len(proxy_pool)})

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "edge-number-masking", "pool": len(proxy_pool), "active": len(active_masks)})

if __name__ == "__main__":
    app.run(host=HOST, port=int(os.getenv("PORT", "5000")), debug=False)
