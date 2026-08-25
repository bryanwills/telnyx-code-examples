# Network Incident Agent — Step-by-Step Guide

This guide walks through the `network-incident-agent` code sample, explaining how it works, the Telnyx primitives it uses, and how to run it. By the end, you'll understand how to build an AI agent that acts as the incident itself — proactively notifying customers, answering calls with incident context, and generating RCA documents.

---

## Table of Contents

1. [What This Sample Does](#what-this-sample-does)
2. [Prerequisites](#prerequisites)
3. [Environment Setup](#environment-setup)
4. [Running the Application](#running-the-application)
5. [Code Walkthrough](#code-walkthrough)
   - [Agent Initialization & Incident State](#agent-initialization--incident-state)
   - [SQLite Incident Timeline](#sqlite-incident-timeline)
   - [Proactive SMS Notifications](#proactive-sms-notifications)
   - [Inbound Call Handling](#inbound-call-handling)
   - [Scheduled Status Checks](#scheduled-status-checks)
   - [RCA Document Generation](#rca-document-generation)
   - [Flask Webhook Endpoints](#flask-webhook-endpoints)
6. [Telnyx Primitives Used](#telnyx-primitives-used)
7. [Next Steps](#next-steps)

---

## What This Sample Does

The **Network Incident Agent** is an AI agent that embodies a network incident. Instead of being a conversation bot, the agent **is** the incident — it maintains incident state, proactively notifies affected customers via SMS, answers inbound calls with real-time incident context, schedules periodic status checks, and generates Root Cause Analysis (RCA) documents.

Key capabilities:

- **Proactive SMS** to all affected customers when status changes
- **Inbound call handling** with incident context (speaks the current status to callers)
- **Scheduled status checks** using `this.schedule()` for recurring tasks
- **RCA document generation** uploaded to Telnyx CloudFS
- **SQLite incident timeline** for auditability and post-incident analysis

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Network Incident Agent                    │
│                                                               │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────┐  │
│  │  Incident    │    │  Proactive   │    │  Inbound Call   │  │
│  │   State      │    │  SMS Alerts  │    │    Handling     │  │
│  └─────────────┘    └──────────────┘    └─────────────────┘  │
│                                                               │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────┐  │
│  │  Scheduled   │    │  RCA Doc     │    │  SQLite         │  │
│  │  Status      │──▶ │  Generation  │──▶ │  Timeline       │  │
│  │  Checks      │    │  (CloudFS)   │    │  (SQLite)       │  │
│  └─────────────┘    └──────────────┘    └─────────────────┘  │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │              Flask Webhook Endpoints                     │  │
│  │  /webhooks/inbound-sms  /webhook/call  /incident/*      │  │
│  └─────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

The agent uses Telnyx's **AI Communications Infrastructure** to bridge the gap between incident management and customer communication — sending proactive SMS, handling inbound calls, and persisting state.

---

## Prerequisites

Before you begin, you'll need:

1. **A Telnyx account** — [Sign up for free](https://portal.telnyx.com/sign-up)
2. **A Telnyx API Key** — Generate one in the [Telnyx Portal](https://portal.telnyx.com/#/app/api-keys)
3. **A Telnyx SMS-enabled number** — Purchase one in the [Numbers section](https://portal.telnyx.com/#/app/numbers)
4. **A Telnyx Public Key** — For verifying webhook signatures (Ed25519)
5. **Python 3.8+** installed on your machine
6. **A CloudFS bucket** — Create one in the [CloudFS section](https://portal.telnyx.com/#/app/cloudfs)

---

## Environment Setup

1. **Clone the repository** (if you haven't already):

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/network-incident-agent
```

2. **Create a virtual environment** (recommended):

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:

```bash
pip install -r requirements.txt
```

4. **Configure environment variables**:

Copy the `.env.example` file to `.env` and fill in your values:

```bash
cp .env.example .env
```

Your `.env` file should look like this:

```env
# Telnyx API credentials
TELNYX_API_KEY=your_telnyx_api_key_here
TELNYX_PUBLIC_KEY=your_telnyx_public_key_here

# SMS sender number (must be a Telnyx number)
TELNYX_SMS_FROM_NUMBER=+15551234567

# Incident configuration
INCIDENT_ID=INC-001
AFFECTED_CUSTOMERS=+15551112222,+15553334444,+15555556666

# CloudFS bucket for RCA documents
CLOUDFS_BUCKET=incident-rca-documents

# Database path for incident timeline
INCIDENT_DB_PATH=incident_timeline.db

# Server port
PORT=8080
```

> **⚠️ Security Note**: Never commit your `.env` file. The `.env.example` file is committed as a template with placeholder values only.

---

## Running the Application

Start the Flask server:

```bash
python app.py
```

The server will start on `http://0.0.0.0:8080` (or the port you specified in `PORT`).

### Testing the Endpoints

Once running, you can test the endpoints:

**Check incident status:**

```bash
curl http://localhost:8080/incident/status
```

**Update incident status (triggers SMS to all affected customers):**

```bash
curl -X POST http://localhost:8080/incident/update \
  -H "Content-Type: application/json" \
  -d '{"status": "monitoring", "description": "We have identified the issue and are monitoring."}'
```

**Notify customers manually:**

```bash
curl -X POST http://localhost:8080/incident/notify \
  -H "Content-Type: application/json" \
  -d '{"message": "We are aware of the issue and working on a fix."}'
```

**Generate RCA document:**

```bash
curl -X POST http://localhost:8080/incident/rca \
  -H "Content-Type: application/json" \
  -d '{"root_cause": "Router configuration error caused routing loop."}'
```

**Health check:**

```bash
curl http://localhost:8080/health
```

---

## Code Walkthrough

Now let's walk through the code section by section to understand how each piece works.

### Agent Initialization & Incident State

The `NetworkIncidentAgent` class extends the Telnyx `Agent` base class. This is the core of the sample — the agent **is** the incident.

```python
class NetworkIncidentAgent(Agent):
    def __init__(self, incident_id: str, affected_customers: List[str], **kwargs):
        super().__init__(**kwargs)
        self.incident_id = incident_id
        self.affected_customers = affected_customers
        self.incident_state = {
            "status": "investigating",
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
```

**Key points:**

- The agent stores **incident state** (status, severity, description, timeline) as instance attributes
- It extends the Telnyx `Agent` class, giving it access to `this.schedule()` for recurring tasks
- The agent is initialized with an incident ID and a list of affected customer phone numbers
- The incident state is the single source of truth for the incident — all actions reference it

### SQLite Incident Timeline

The agent persists every event to a SQLite database for auditability and post-incident analysis.

```python
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
```

The `_add_event` method appends to both the in-memory `timeline` list and the SQLite database:

```python
def _add_event(self, event_type: str, description: str):
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
```

**Key points:**

- The timeline is stored **both** in memory (for quick access) and in SQLite (for persistence)
- Every event — incident creation, status updates, customer notifications, inbound calls, status checks, RCA generation — is logged
- The SQLite database path is configurable via `INCIDENT_DB_PATH`

### Proactive SMS Notifications

The agent proactively notifies all affected customers via SMS when the incident status changes:

```python
def _send_sms(self, to_number: str, message: str):
    """Send an SMS via Telnyx."""
    try:
        telnyx.Message.create(
            from_=os.getenv("TELNYX_SMS_FROM_NUMBER"),
            to=to_number,
            text=message,
        )
        app.logger.info(f"SMS sent to {to_number}")
    except Exception as e:
        app.logger.exception(f"Failed to send SMS to {to_number}")

def notify_affected_customers(self, message: str):
    """Proactively notify all affected customers via SMS."""
    for customer in self.affected_customers:
        self._send_sms(customer, message)
    self._add_event("customer_notification", f"Notified {len(self.affected_customers)} customers via SMS")
```

**Key points:**
- Uses the Telnyx `Message.create()` API to send SMS
- The `from_` number is configured via `TELNYX_SMS_FROM_NUMBER` env var
- Each notification is logged to the incident timeline
- Errors are caught and logged without crashing the agent

### Inbound Call Handling

When a customer calls in, the agent answers with incident context:

```python
def handle_inbound_call(self, call_control_id: str, from_number: str):
    """Handle an inbound customer call with incident context."""
    self._add_event("inbound_call", f"Call from {from_number}")
    
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
```

**Key points:**
- The agent builds a **context-aware message** using the current incident state
- Uses Telnyx **Call Control** to speak the message to the caller
- The call is logged to the incident timeline
- In production, you'd wire this to the actual call control ID from the webhook

### Scheduled Status Checks

The agent uses `this.schedule()` for recurring status checks:

```python
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
```

**Key points:**
- `this.schedule()` is a Telnyx Agent primitive for **recurring tasks**
- The status check runs every 300 seconds (5 minutes) by default
- Each check is logged to the timeline
- In production, you'd integrate with your monitoring system to check actual network health

### RCA Document Generation

When the incident is resolved, the agent generates an RCA document and uploads it to CloudFS:

```python
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
```

**Key points:**
- The RCA document includes the full incident timeline, root cause, and affected customers
- Uploaded to **Telnyx CloudFS** using the `telnyx.CloudFS.File.create()` API
- The bucket name is configurable via `CLOUDFS_BUCKET`
- The document is stored as JSON for easy parsing and analysis

### Flask Webhook Endpoints

The Flask app exposes webhook endpoints for Telnyx to call:

**Inbound SMS Webhook:**

```python
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
        
        app.logger.info(f"Inbound SMS from {from_number}: {text}")
        
        # Handle the message - could be a customer response
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        app.logger.exception("Error processing inbound SMS webhook")
        return jsonify({"error": "Internal server error"}), 500
```

**Inbound Call Webhook:**

```python
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
```

**Key points:**
- Both webhooks verify the **Telnyx Ed25519 signature** using `telnyx.webhooks.unwrap()`
- The inbound call webhook passes the call control ID and caller number to the agent
- Errors are logged and a generic 500 response is returned (no internal details leaked)

---

## Telnyx Primitives Used

This sample demonstrates several Telnyx primitives:

| Primitive | Usage |
|-----------|-------|
| **SMS Messaging** | `telnyx.Message.create()` to send proactive SMS to affected customers |
| **Call Control** | `telnyx.CallControl.Speak()` to speak incident context to callers |
| **CloudFS** | `telnyx.CloudFS.File.create()` to store RCA documents |
| **Webhooks** | Inbound SMS and call webhooks with Ed25519 signature verification |
| **Agent Scheduling** | `this.schedule()` for recurring status checks |
| **Agent State** | The agent maintains incident state as its core identity |

---

## Next Steps

Now that you understand how the Network Incident Agent works, here are some ways to extend it:

1. **Integrate with monitoring systems** — Replace the placeholder `_perform_status_check` with real network monitoring integration (e.g., ping, SNMP, API calls to your infrastructure).

2. **Add two-way SMS conversation** — Use the inbound SMS webhook to let customers reply with questions, and have the agent respond with incident context.

3. **Implement full Call Control** — Use the full Telnyx Call Control API to play audio, gather input, or transfer calls to a human operator.

4. **Add severity escalation** — Automatically escalate severity based on incident duration or customer impact.

5. **Generate richer RCA documents** — Include metrics, logs, or screenshots in the RCA document.

6. **Add incident resolution workflows** — Automatically resolve incidents when monitoring checks pass, and notify customers of resolution.

### Useful Documentation

- [Telnyx SMS API](https://developers.telnyx.com/docs/api/v2/messages)
- [Telnyx Call Control API](https://developers.telnyx.com/docs/api/v2/call-control)
- [Telnyx CloudFS API](https://developers.telnyx.com/docs/api/v2/cloudfs)
- [Telnyx Webhooks](https://developers.telnyx.com/docs/api/v2/webhooks)
- [Telnyx Agent Framework](https://developers.telnyx.com/docs/ai/agent-framework)
- [Telnyx Python SDK](https://developers.telnyx.com/docs/api/v2/python-sdk)

---

Happy building! 🚀
