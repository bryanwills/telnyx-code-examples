"""Edge Webhook Aggregator — multi-tenant SaaS webhook consolidation.
Receives all Telnyx webhooks, classifies by tenant, batches, and forwards one
consolidated payload per tenant per interval. Reduces backend traffic by 90%."""
import os, json, time, base64, ipaddress, threading, logging, socket
from urllib.parse import urlparse
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import requests
import boto3
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

load_dotenv()
app = Flask(__name__)
app.logger.setLevel(logging.INFO)

TELNYX_API_KEY = os.getenv("TELNYX_API_KEY")
TELNYX_PUBLIC_KEY = os.getenv("TELNYX_PUBLIC_KEY", "")
STORAGE_BUCKET = os.getenv("STORAGE_BUCKET", "webhook-overflow")
BATCH_INTERVAL = int(os.getenv("BATCH_INTERVAL_SECONDS", "5"))
HOST = os.getenv("HOST", "127.0.0.1")

s3 = boto3.client("s3", endpoint_url="https://storage.telnyx.com",
                   aws_access_key_id=TELNYX_API_KEY, aws_secret_access_key=TELNYX_API_KEY)

# Telnyx public key (Portal > Keys & Credentials) is a base64-encoded 32-byte Ed25519 key.
_TELNYX_VERIFY_KEY = None
if TELNYX_PUBLIC_KEY:
    try:
        _TELNYX_VERIFY_KEY = Ed25519PublicKey.from_public_bytes(base64.b64decode(TELNYX_PUBLIC_KEY))
    except Exception as e:
        app.logger.error("Invalid TELNYX_PUBLIC_KEY, webhook verification disabled: %s", e)

MAX_SKEW_SECONDS = 300

def verify_telnyx_signature(raw_body, headers):
    """Verify the Telnyx Ed25519 signature over ``<timestamp>|<raw body>`` before
    trusting the webhook. Headers are telnyx-signature-ed25519 (base64) and
    telnyx-timestamp. Rejects signatures older than MAX_SKEW_SECONDS (replay)."""
    if _TELNYX_VERIFY_KEY is None:
        return False
    signature = headers.get("telnyx-signature-ed25519", "")
    timestamp = headers.get("telnyx-timestamp", "")
    if not signature or not timestamp:
        return False
    try:
        if abs(time.time() - int(timestamp)) > MAX_SKEW_SECONDS:
            return False
        signed = f"{timestamp}|".encode() + raw_body
        _TELNYX_VERIFY_KEY.verify(base64.b64decode(signature), signed)
        return True
    except (InvalidSignature, ValueError, TypeError):
        return False

def safe_callback_url(url):
    """Tenant callback URLs are arbitrary external endpoints, so we cannot pin them to
    a single host — but a tenant must not be able to point us at internal/metadata
    services. Require https and reject any URL that resolves to a private, loopback,
    link-local, or otherwise non-global address (SSRF guard)."""
    try:
        parts = urlparse(url or "")
    except ValueError:
        return False
    host = (parts.hostname or "").lower()
    if parts.scheme != "https" or not host:
        return False
    try:
        infos = socket.getaddrinfo(host, parts.port or 443, proto=socket.IPPROTO_TCP)
    except (socket.gaierror, UnicodeError):
        return False
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if not ip.is_global or ip.is_multicast or ip.is_reserved:
            return False
    return True

tenant_map = {}  # phone_number -> tenant_id
event_batches = {}  # tenant_id -> [events]
tenant_endpoints = {}  # tenant_id -> callback_url
flush_lock = threading.Lock()
MAX_ENTRIES = 10000

def ttl_cleanup(store, max_size=MAX_ENTRIES):
    if isinstance(store, dict) and len(store) > max_size:
        oldest = sorted(store, key=lambda k: len(store.get(k, [])) if isinstance(store.get(k), list) else 0)
        for k in oldest[:len(store) - max_size]:
            del store[k]

def flush_batches():
    """Flush accumulated events to tenant endpoints."""
    while True:
        time.sleep(BATCH_INTERVAL)
        with flush_lock:
            for tenant_id, events in list(event_batches.items()):
                if not events:
                    continue
                batch = events.copy()
                event_batches[tenant_id] = []
                endpoint = tenant_endpoints.get(tenant_id)
                if endpoint:
                    try:
                        requests.post(endpoint, json={"tenant_id": tenant_id, "events": batch,
                                                       "count": len(batch), "flushed_at": time.time()},
                                      timeout=10)
                        app.logger.info("Flushed %s events to tenant %s", len(batch), tenant_id)
                    except Exception as e:
                        app.logger.error("Flush to %s failed: %s — archiving to storage", tenant_id, e)
                        try:
                            key = f"overflow/{tenant_id}/{int(time.time())}.json"
                            s3.put_object(Bucket=STORAGE_BUCKET, Key=key,
                                          Body=json.dumps(batch), ContentType="application/json")
                        except Exception as se:
                            app.logger.error("Storage archive failed: %s", se)

flush_thread = threading.Thread(target=flush_batches, daemon=True)
flush_thread.start()

@app.route("/webhooks/ingest", methods=["POST"])
def ingest_webhook():
    # Verify the Telnyx Ed25519 signature against the RAW body before trusting anything.
    raw_body = request.get_data()
    if not verify_telnyx_signature(raw_body, request.headers):
        return jsonify({"error": "invalid signature"}), 401
    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({"error": "No payload"}), 400
    event = payload.get("data", {})
    event_payload = event.get("payload", {})
    phone = event_payload.get("to", event_payload.get("from", ""))
    if isinstance(phone, list):
        phone = phone[0].get("phone_number", "") if phone else ""
    elif isinstance(phone, dict):
        phone = phone.get("phone_number", phone)
    tenant_id = tenant_map.get(phone, "unassigned")
    with flush_lock:
        if tenant_id not in event_batches:
            event_batches[tenant_id] = []
        event_batches[tenant_id].append({
            "event_type": event.get("event_type"),
            "payload": event_payload,
            "received_at": time.time()
        })
        ttl_cleanup(event_batches)
    return jsonify({"status": "queued", "tenant": tenant_id})

@app.route("/tenants", methods=["POST"])
def register_tenant():
    data = request.get_json() or {}
    tenant_id = data.get("tenant_id")
    phones = data.get("phone_numbers", [])
    endpoint = data.get("callback_url")
    if not tenant_id or not endpoint:
        return jsonify({"error": "tenant_id and callback_url required"}), 400
    # callback_url is attacker-controllable; reject anything that could reach an
    # internal/metadata host before we ever POST batched events to it (SSRF guard).
    if not safe_callback_url(endpoint):
        return jsonify({"error": "callback_url must be a public https URL"}), 400
    for phone in phones:
        tenant_map[phone] = tenant_id
    tenant_endpoints[tenant_id] = endpoint
    if tenant_id not in event_batches:
        event_batches[tenant_id] = []
    return jsonify({"status": "registered", "tenant_id": tenant_id, "numbers": len(phones)})

@app.route("/tenants", methods=["GET"])
def list_tenants():
    return jsonify({"tenants": {tid: {"endpoint": tenant_endpoints.get(tid, ""), "pending": len(event_batches.get(tid, []))}
                                for tid in tenant_endpoints}})

@app.route("/stats", methods=["GET"])
def stats():
    return jsonify({"tenants": len(tenant_endpoints), "mapped_numbers": len(tenant_map),
                    "pending_events": sum(len(v) for v in event_batches.values())})

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "edge-webhook-aggregator"})

if __name__ == "__main__":
    app.run(host=HOST, port=int(os.getenv("PORT", "5000")), debug=False)
