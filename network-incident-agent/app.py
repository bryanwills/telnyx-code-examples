import os
import json
import time
import sqlite3
from datetime import datetime, timezone
from typing import Dict, List, Optional

from dotenv import load_dotenv
from flask import Flask, request, jsonify
import telnyx
from telnyx import Agent

load_dotenv()

app = Flask(__name__)

# Configure Telnyx
telnyx.api_key = os.getenv("TELNYX_API_KEY")
telnyx.public_key = os.getenv("TELNYX_PUBLIC_KEY")

# Database path for incident timeline
DB_PATH = os.getenv("INCIDENT_DB_PATH", "incident_timeline.db")


class NetworkIncidentAgent(Agent):
    """
    Network Incident Agent - an AI agent that acts as the incident itself.
    
    The agent maintains incident state, proactively notifies affected customers
    via SMS, answers incoming calls with incident context, schedules status
    checks, and generates RCA documents.
    """

    def __init__(self, incident_id: str, affected_customers: List[str], **kwargs):
        super().__init__(**kwargs)
        self.incident_id = incident_id
        self.affected_customers = affected_customers
        self.incident_state = {
            "status": "investigating",  # investigating, monitoring, resolved
            "severity": "SEV-1",
            "description": "",
            "affected_services": [],
            "start_time": datetime.now(timezone.utc).isoformat(),
            "resolution_time": None,
            "root_cause": None,
            "timeline": [],
        }
        self._init_db()
        self._log_event("incident_created", "Incident agent initialized")

    def _init_db(self):
        """Initialize SQLite database for incident timeline."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS incident_timeline (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                incident_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                description TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()

    def _add_event(self, event_type: str, description: str):
        """Add an event to the incident timeline in SQLite."""
        timestamp = datetime.now(timezone.utc).isoformat()
        self.incident_state["timeline"].append({
            "event_type": event_type,
            "description": description,
            "timestamp": timestamp,
        })
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO incident_timeline (incident_id, event_type, description, timestamp) VALUES (?, ?, ?, ?)",
                (self.incident_id, event_type, description, timestamp),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            app.logger.exception("Failed to write to incident timeline DB")

    def _send_sms(self, to_number: str, message: str):
        """Send an SMS via Telnyx."""
        try:
            telnyx.Message.create(
                from_=os.getenv("TELNYX_SMS_FROM_NUMBER"),
                to=to_number,
                text=message,
            )
            app.logger.info("SMS sent successfully")
        except Exception as e:
            app.logger.exception("Failed to send SMS")

    def notify_affected_customers(self, message: str):
        """Proactively notify all affected customers via SMS."""
        for customer in self.affected_customers:
            self._send_sms(customer, message)
        self._add_event("customer_notification", f"Notified {len(self.affected_customers)} customers via SMS")

    def update_incident_status(self, status: str, description: str = None):
        """Update incident status and notify customers."""
        self.incident_state["status"] = status
        if status == "resolved":
            self.incident_state["resolution_time"] = datetime.now(timezone.utc).isoformat()
        
        message = f"Update on incident {self.incident_id}: Status is now {status}."
        if description:
            message += f" {description}"
        
        self._add_event("status_update", f"Status changed to {status}")
        self.notify_affected_customers(message)

    def handle_inbound_call(self, call_control_id: str, from_number: str):
        """
        Handle an inbound customer call with incident context.
        This is called when a customer calls in about the incident.
        """
        self._add_event("inbound_call", "Inbound customer call received")
        
        # Build incident context message
        context_message = (
            f"Thank you for calling about incident {self.incident_id}. "
            f"Current status: {self.incident_state['status']}. "
            f"Description: {self.incident_state['description']}. "
            f"We are working to resolve this as quickly as possible."
        )
        
        # In a real implementation, this would use Telnyx Call Control APIs
        # to speak the message or play audio to the caller
        try:
            # Example: speak the message via call control
            telnyx.CallControl.Speak(
                call_control_id=call_context_id,
                payload=incident_message,
                voice="female",
                language="en-US",
            )
        except Exception as e:
            app.logger.exception("Failed to speak incident context to caller")

    def schedule_status_check(self, interval_seconds: int = 300):
        """
        Schedule periodic status checks for the incident.
        Uses this.schedule() for recurrence.
        """
        self.schedule(
            self._perform_status_check,
            interval_seconds=interval_seconds,
            recurring=True,
        )

    def _perform_status_check(self):
        """Perform a status check on the incident."""
        self._add_event("status_check", "Performing scheduled status check")
        # In a real implementation, this would check monitoring systems
        # and potentially update incident status
        app.logger.info(f"Status check performed for incident {self.incident_id}")

    def generate_rca_document(self, root_cause: str):
        """
        Generate an RCA (Root Cause Analysis) document and upload to CloudFS.
        """
        self.incident_state["root_cause"] = root_cause
        self._add_event("rca_generated", "RCA document generated")
        
        # Generate RCA content
        rca_content = {
            "incident_id": self.incident_id,
            "root_cause": root_cause,
            "timeline": self.incident_state["timeline"],
            "start_time": self.incident_state["start_time"],
            "resolution_time": self.incident_state["resolution_time"],
            "affected_customers": self.affected_customers,
        }
        
        # Upload to CloudFS
        try:
            telnyx.CloudFS.File.create(
                name=f"rca_{self.incident_id}.json",
                content=json.dumps(rca_content, indent=2),
                bucket=os.getenv("CLOUDFS_BUCKET"),
            )
            app.logger.info(f"RCA document uploaded to CloudFS for incident {self.incident_id}")
        except Exception as e:
            app.logger.exception("Failed to upload RCA document to CloudFS")


# Initialize the agent
agent = NetworkIncidentAgent(
    incident_id=os.getenv("INCIDENT_ID", "INC-001"),
    affected_customers=os.getenv("AFFECTED_CUSTOMERS", "").split(",") if os.getenv("AFFECTED_CUSTOMERS") else [],
)


@app.route("/webhooks/inbound-sms", methods=["POST"])
def inbound_sms_webhook():
    """Handle inbound SMS webhook from Telnyx."""
    try:
        event = telnyx.webhooks.unwrap(request.data, request.headers.get("Telnyx-Signature-Ed25519"))
        payload = event["data"]["payload"]
        
        # Extract message details
        from_number = payload["from"]["phone_number"]
        to_number = payload["to"][0]["phone_number"]
        text = payload["text"]
        
        app.logger.info("Received inbound SMS")
        
        # Handle the message - could be a customer response
        # For now, just acknowledge
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        app.logger.exception("Error processing inbound SMS webhook")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/webhook/call", methods=["POST"])
def call_webhook():
    """Handle inbound call webhook from Telnyx."""
    try:
        event = telnyx.webhooks.unwrap(request.get_data(), request.headers.get("Telnyx-Signature-Ed25519"))
        payload = event["data"]["payload"]
        
        call_control_id = payload["call_control_id"]
        from_number = payload["from"]
        
        # Handle the call with incident context
        agent.handle_inbound_call(call_control_id, from_number)
        
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        app.logger.exception("Error processing call webhook")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/incident/status", methods=["GET"])
def get_incident_status():
    """Get current incident status."""
    return jsonify(agent.incident_state), 200


@app.route("/incident/update", methods=["POST"])
def update_incident():
    """Update incident status."""
    data = request.get_json()
    if not data or "status" not in data:
        return jsonify({"error": "Status is required"}), 400
    
    status = data["status"]
    description = data.get("description")
    
    agent.update_incident_status(status, description)
    return jsonify({"status": "updated", "incident_state": agent.incident_state}), 200


@app.route("/incident/notify", methods=["POST"])
def notify_customers():
    """Proactively notify all affected customers."""
    data = request.get_json()
    message = data.get("message", f"Update on incident {agent.incident_id}")
    
    agent.notify_affected_customers(message)
    return jsonify({"status": "ok", "notified": len(agent.affected_customers)}), 200


@app.route("/incident/rca", methods=["POST"])
def generate_rca():
    """Generate RCA document."""
    data = request.get_json()
    if not data or "root_cause" not in data:
        return jsonify({"error": "Root cause is required"}), 400
    
    agent.generate_rca_document(data["root_cause"])
    return jsonify({"status": "ok"}), 200


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy"}), 200


if __name__ == "__main__":
    # Start the agent with scheduled status checks
    agent.schedule_status_check(interval_seconds=300)
    
    # Start Flask app
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
