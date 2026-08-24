"""
AI Call Campaign Orchestrator

Durable outbound call campaign with rate limiting, SQL tracking, and SMS summary.
"""

import os
import time
import uuid
from datetime import datetime, timezone

import telnyx
from dotenv import load_dotenv
from flask import Flask, jsonify, request

load_dotenv()

app = Flask(__name__)

telnyx.api_key = os.getenv("TELNYX_API_KEY")
TELNYX_PUBLIC_KEY = os.getenv("TELNYX_PUBLIC_KEY")
TELNYX_PHONE_NUMBER = os.getenv("TELNYX_PHONE_NUMBER")
TELNYX_SMS_FROM = os.getenv("TELNYX_SMS_FROM", TELNYX_PHONE_NUMBER)
TELNYX_SMS_TO = os.getenv("TELNYX_SMS_TO")
CALL_RATE_LIMIT_PER_MINUTE = int(os.getenv("CALL_RATE_LIMIT_PER_MINUTE", "10"))
CALL_RATE_LIMIT_SECONDS = 60 / CALL_RATE_LIMIT_PER_MINUTE

# In-memory campaign state (for demo; use a real store in production)
campaigns = {}


class CampaignAgent:
    """Durable workflow agent for a single campaign."""

    def __init__(self, campaign_id, phone_numbers, storage):
        self.campaign_id = campaign_id
        self.phone_numbers = phone_numbers
        self.storage = storage
        self.queue = list(phone_numbers)
        self.results = []
        self.completed = False

    def on_task(self):
        """Entry point: queue all calls and start the rate-limited scheduler."""
        self._init_db()
        for number in self.phone_numbers:
            self.queue("make_call", {"to": number, "campaign_id": self.campaign_id})
        self.schedule(0, "process_next_batch")

    def queue(self, task_name, payload):
        """Queue a task (Agent SDK queue())."""
        # In a real Agent SDK, this enqueues a task. Here we store it.
        self.queue.append({"task": task_name, "payload": payload})

    def schedule(self, in_seconds, task_name):
        """Schedule a task (Agent SDK schedule())."""
        # In a real Agent SDK, this schedules. Here we simulate with a timer.
        # For the demo, we just call process_next_batch after the delay.
        import threading

        def _run():
            time.sleep(in_seconds)
            getattr(self, task_name)()

        threading.Thread(target=_run, daemon=True).start()

    def process_next_batch(self):
        """Rate-limited batch processor."""
        if not self.queue or self.completed:
            return

        # Take up to CALLS_PER_LIMIT calls from the queue
        batch = []
        for _ in range(min(CALLS_PER_LIMIT_PER_MINUTE, len(self.queue))):
            item = self.queue.pop(0)
            if item["task"] == "make_call":
                batch.append(item["payload"])

        for payload in batch:
            self.make_call(payload["to"], payload["campaign_id"])

        if self.queue:
            self.schedule(CALLS_PER_LIMIT_SECONDS, "process_next_batch")
        else:
            self.completed = True
            self._send_summary()

    def make_call(self, to, campaign_id):
        """Outbound Call Control call."""
        try:
            call = telnyx.Call.create(
                to=to,
                from_=TELNYX_PHONE_NUMBER,
                connection_id=os.getenv("TELNYX_CONNECTION_ID"),
                webhook_url=os.getenv("TELNYX_WEBHOOK_URL"),
                webhook_url_method="POST",
            )
            result = {"to": to, "status": "queued", "call_control_id": call.id}
        except Exception as e:
            app.logger.exception("Failed to place call to %s", to)
            result = {"to": to, "status": "failed", "error": str(e)}

        self._save_result(result)

    def _init_storage(self):
        """Create the results table if it doesn't exist."""
        try:
            self.storage.exec(
                """CREATE TABLE IF NOT EXISTS campaign_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    campaign_id TEXT NOT NULL,
                    phone_number TEXT NOT NULL,
                    status TEXT NOT NULL,
                    call_control_id TEXT,
                    created_at TEXT NOT NULL
                )"""
            )
        except Exception as e:
            app.logger.exception("Failed to init storage: %s", e)

    def _save_result(self, result):
        """Save a call result to SQL."""
        try:
            self.storage.exec(
                """INSERT INTO campaign_results
                   (campaign_id, phone_number, status, call_control_id, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    self.campaign_id,
                    result["to"],
                    result["status"],
                    result.get("call_control_id"),
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
        except Exception as e:
            app.logger.exception("Failed to save result: %s", e)

    def _send_summary(self):
        """Send SMS summary on completion."""
        if not TELNYX_SMS_TO:
            app.logger.warning("TELNYX_SMS_TO not set; skipping SMS summary")
            return

        try:
            # Count results from SQL
            rows = self.storage.query(
                "SELECT status, COUNT(*) FROM campaign_results WHERE campaign_id = ? GROUP BY status",
                (self.campaign_id,),
            )
            summary = ", ".join(f"{status}: {count}" for status, count in rows)
            text = f"Campaign {self.campaign_id} complete. Results: {summary}"

            telnyx.Message.create(
                from_=TELNYX_SMS_FROM,
                to=TELNYX_SMS_TO,
                text=text,
            )
            app.logger.info("SMS summary sent for campaign %s", self.campaign_id)
        except Exception as e:
            app.logger.exception("Failed to send SMS summary: %s", e)


@app.route("/campaign", methods=["POST"])
def create_campaign():
    """Create a new campaign."""
    data = request.get_json()
    if not data or "phone_numbers" not in data:
        return jsonify({"error": "phone_numbers is required"}), 400

    phone_numbers = data["phone_numbers"]
    if not isinstance(phone_numbers, list) or not phone_numbers:
        return jsonify({"error": "phone_numbers must be a non-empty list"}), 400

    campaign_id = str(uuid.uuid4())
    campaigns[campaign_id] = CampaignManager(campaign_id, phone_numbers, storage=None)

    # Start the campaign
    campaigns[campaign_id].on_task()

    return jsonify({"campaign_id": campaign_id, "status": "started"}), 202


@app.route("/campaign/<campaign_id>", methods=["GET"])
def get_campaign(campaign_id):
    """Get campaign status."""
    campaign = campaigns.get(campaign_id)
    if not campaign:
        return jsonify({"error": "Campaign not found"}), 404

    return jsonify(
        {
            "campaign_id": campaign_id,
            "total": len(campaign.phone_numbers),
            "completed": campaign.completed,
            "results": campaign.results,
        }
    )


@app.route("/webhooks/call", methods=["POST"])
def call_webhook():
    """Handle Call Control webhooks."""
    try:
        event = telnyx.webhooks.unwrap(request.data, TELNYX_PUBLIC_KEY)
    except Exception as e:
        app.logger.exception("Webhook verification failed: %s", e)
        return jsonify({"error": "Invalid signature"}), 403

    payload = event["data"]["payload"]
    call_control_id = payload.get("call_control_id")
    call_state = payload.get("call_leg_id")

    # Handle call states (answer, hangup, etc.)
    if payload.get("call_control_id"):
        # In a real implementation, you'd use Call Control commands here
        # e.g., answer, gather, hangup
        pass

    return jsonify({"status": "ok"}), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)
