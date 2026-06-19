"""Edge Compute Webhook Proxy — receive Telnyx voice/SMS webhooks at the edge, validate, enrich, sign, and forward to your backend with minimal latency."""
import base64
import json
import hashlib
import hmac
import logging
import os
import time
from urllib.request import Request, urlopen
from urllib.error import URLError

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature

HTTP_SCOPE_TYPE = "http"
logger = logging.getLogger("webhook-proxy")

# Telnyx signs every webhook with Ed25519 (telnyx-signature-ed25519 / telnyx-timestamp
# headers over "<timestamp>|<raw body>"). The edge runtime has no Telnyx SDK, so verify
# directly with the public key (Portal > Keys & Credentials > Public Key).
TELNYX_PUBLIC_KEY = os.environ.get("TELNYX_PUBLIC_KEY", "")


def verify_telnyx_signature(body: bytes, headers: dict, tolerance: int = 300) -> bool:
    sig_b64 = headers.get("telnyx-signature-ed25519", "")
    timestamp = headers.get("telnyx-timestamp", "")
    if not (sig_b64 and timestamp and TELNYX_PUBLIC_KEY):
        return False
    try:
        if abs(time.time() - int(timestamp)) > tolerance:  # replay protection
            return False
        public_key = Ed25519PublicKey.from_public_bytes(base64.b64decode(TELNYX_PUBLIC_KEY))
        public_key.verify(base64.b64decode(sig_b64), f"{timestamp}|".encode() + body)
        return True
    except (InvalidSignature, ValueError, Exception):
        return False


def new():
    return WebhookProxy()


class WebhookProxy:
    def __init__(self):
        self.forward_url = os.environ.get("FORWARD_URL", "")
        self.secret = os.environ.get("FORWARD_SECRET", "")
        self.stats = {"received": 0, "forwarded": 0, "errors": 0}

    def _sign(self, body: bytes) -> str:
        if not self.secret:
            return ""
        return hmac.new(self.secret.encode(), body, hashlib.sha256).hexdigest()

    async def _read_body(self, receive) -> bytes:
        body = b""
        while True:
            msg = await receive()
            body += msg.get("body", b"")
            if not msg.get("more_body", False):
                break
        return body

    async def _respond(self, send, status: int, data: dict):
        payload = json.dumps(data).encode()
        await send({"type": "http.response.start", "status": status,
                     "headers": [[b"content-type", b"application/json"]]})
        await send({"type": "http.response.body", "body": payload})

    async def handle(self, scope, receive, send):
        if scope.get("type") != HTTP_SCOPE_TYPE:
            await self._respond(send, 400, {"error": "not http"})
            return

        path = scope.get("path", "/")
        method = scope.get("method", "GET")

        if path == "/health" and method == "GET":
            await self._respond(send, 200, {"status": "ok", **self.stats})
            return

        if path in ("/webhooks/voice", "/webhooks/sms", "/webhooks/messaging") and method == "POST":
            body = await self._read_body(receive)
            self.stats["received"] += 1

            # Verify the inbound Telnyx Ed25519 signature before trusting/forwarding.
            headers = {k.decode().lower(): v.decode() for k, v in scope.get("headers", [])}
            if not verify_telnyx_signature(body, headers):
                self.stats["errors"] += 1
                await self._respond(send, 401, {"error": "invalid signature"})
                return

            try:
                event = json.loads(body)
            except json.JSONDecodeError:
                self.stats["errors"] += 1
                await self._respond(send, 400, {"error": "invalid json"})
                return

            enriched = {
                "edge_received_at": time.time(),
                "edge_path": path,
                "original_event": event,
            }
            enriched_body = json.dumps(enriched).encode()

            if self.forward_url:
                try:
                    headers = {"Content-Type": "application/json"}
                    sig = self._sign(enriched_body)
                    if sig:
                        headers["X-Edge-Signature"] = f"sha256={sig}"
                    if not self.forward_url.startswith("https://"):  # only https forward targets
                        raise ValueError("forward_url must be https")
                    req = Request(self.forward_url, data=enriched_body, headers=headers, method="POST")
                    # nosemgrep: python.lang.security.audit.dynamic-urllib-use-detected -- forward_url validated https above.
                    urlopen(req, timeout=5)
                    self.stats["forwarded"] += 1
                except (URLError, Exception) as e:
                    logger.error("Forward failed: %s", e)
                    self.stats["errors"] += 1

            await self._respond(send, 200, {"status": "received", "forwarded": bool(self.forward_url)})
            return

        await self._respond(send, 404, {"error": "not found"})
