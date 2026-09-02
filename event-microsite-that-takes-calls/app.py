"""
Event Microsite That Takes Calls
A Flask app that serves an event microsite backed by Telnyx KV,
enables SMS/Voice/WebSocket contact with an AI concierge,
broadcasts schedule changes, qualifies exhibitor leads,
and transcribes post-event feedback into a sponsor report.
"""

import os
import json
import logging
from datetime import datetime, timezone
from flask import Flask, request, jsonify, render_template_string, abort
from dotenv import load_dotenv

import telnyx

# ---------------------------------------------------------------------------
# Configuration & initialization
# ---------------------------------------------------------------------------

load_dotenv()

app = Flask(__name__)
app.logger.setLevel(logging.INFO)

# Required environment variables
REQUIRED_ENV_VARS = [
    "TELNYX_API_KEY",
    "TELNYX_PUBLIC_KEY",
    "TELNYX_PHONE_NUMBER",
    "TELNYX_SMS_FROM",
    "TELNYX_WHATSAPP_FROM",
    "TELNYX_VOICE_CONNECTION_ID",
    "TELNYX_KV_NAMESPACE_ID",
    "TELNYX_SQLDB_CONNECTION_STRING",
    "TELNYX_INFERENCE_API_KEY",
    "TELNYX_AI_CONCIERGE_NAME",
    "TELNYX_AI_CONCIERGE_PROMPT",
    "TELNYX_SALES_REP_PHONE",
    "TELNYX_EVENT_DOMAIN",
    "TELNYX_DEMO_MODE",
]

_missing = [v for v in REQUIRED_ENV_VARS if not os.getenv(v)]
if _missing:
    app.logger.error("Missing required environment variables: %s", ", ".join(_missing))

# Telnyx SDK configuration
telnyx.api_key = os.getenv("TELNYX_API_KEY")
TELNYX_PUBLIC_KEY = os.getenv("TELNYX_PUBLIC_KEY")
TELNYX_PHONE_NUMBER = os.getenv("TELNYX_PHONE_NUMBER")
TELNYX_SMS_FROM = os.getenv("TELNYX_SMS_FROM")
TELNYX_WHATSAPP_FROM = os.getenv("TELNYX_WHATSAPP_FROM")
TELNYX_VOICE_CONNECTION_ID = os.getenv("TELNYX_VOICE_CONNECTION_ID")
TELNYX_KV_NAMESPACE_ID = os.getenv("TELNYX_KV_NAMESPACE_ID")
TELNYX_SQLDB_CONNECTION_STRING = os.getenv("TELNYX_SQLDB_CONNECTION_STRING")
TELNYX_INFERENCE_API_KEY = os.getenv("TELNYX_INFERENCE_API_KEY")
TELNYX_AI_CONCIERGE_NAME = os.getenv("TELNYX_AI_CONCIERGE_NAME", "Event Concierge")
TELNYX_AI_CONCIERGE_PROMPT = os.getenv("TELNYX_AI_CONCIERGE_PROMPT", "You are a helpful event concierge.")
TELNYX_SALES_REP_PHONE = os.getenv("TELNYX_SALES_REP_PHONE")
TELNYX_EVENT_DOMAIN = os.getenv("TELNYX_EVENT_DOMAIN")
DEMO_MODE = os.getenv("TELNYX_DEMO_MODE", "true").lower() in ("true", "1", "yes")

# ---------------------------------------------------------------------------
# Sample event data (fixtures)
# ---------------------------------------------------------------------------

SAMPLE_EVENT_DATA = {
    "event": {
        "name": "TechForward Summit 2025",
        "date": "2025-06-15",
        "location": "San Francisco Convention Center",
        "description": "Join industry leaders for two days of innovation and networking.",
    },
    "schedule": [
        {"id": "s1", "time": "09:00", "title": "Opening Keynote", "speaker": "Jane Doe", "room": "Main Hall"},
        {"id": "s2", "time": "10:30", "title": "AI in 2025", "speaker": "John Smith", "room": "Room A"},
        {"id": "s3", "time": "14:00", "title": "Networking Break", "speaker": "", "room": "Lobby"},
        {"id": "s4", "time": "15:30", "title": "Closing Panel", "speaker": "Panelists", "room": "Main Hall"},
    ],
    "speakers": [
        {"id": "sp1", "name": "Jane Doe", "title": "CEO, TechCorp", "bio": "Visionary leader in AI.", "photo": "https://via.placeholder.com/150"},
        {"id": "sp2", "name": "John Smith", "title": "CTO, InnovateX", "bio": "Architect of next-gen platforms.", "photo": "https://via.placeholder.com/150"},
    ],
    "venue": {
        "address": "800 Howard St, San Francisco, CA 94103",
        "map_url": "https://maps.google.com/?q=San+Francisco+Convention+Center",
        "wifi": "SSID: TechForward-Guest | Password: summit2025",
        "parking": "Valet parking available at the main entrance. $25/day.",
    },
    "sponsors": [
        {"id": "spon1", "name": "Telnyx", "tier": "Platinum", "logo": "https://via.placeholder.com/100"},
        {"id": "spon2", "name": "OpenAI", "tier": "Gold", "logo": "https://via.placeholder.com/100"},
        {"id": "spon3", "name": "Stripe", "tier": "Silver", "logo": "https://via.placeholder.com/100"},
    ],
}

# ---------------------------------------------------------------------------
# KV helpers (using Telnyx KV SDK)
# ---------------------------------------------------------------------------

def kv_get(key: str):
    """Retrieve a value from Telnyx KV namespace."""
    try:
        resp = telnyx.kv.Namespace.retrieve(
            TELNYX_KV_NAMESPACE_ID,
            key=key,
        )
        return json.loads(resp.value) if resp.value else None
    except Exception as e:
        app.logger.exception("KV get failed for key %s: %s", key, e)
        return None


def kv_put(key: str, value):
    """Store a value in Telnyx KV namespace."""
    try:
        telnyx.kv.Namespace.create_entry(
            TELNYX_KV_NAMESPACE_ID,
            key=key,
            value=json.dumps(value),
        )
        return True
    except Exception as e:
        app.logger.exception("KV put failed for key %s: %s", key, e)
        return False


def get_event_data():
    """Fetch event data from KV, falling back to sample data."""
    data = kv_get("event_data")
    if data is None:
        # Seed KV with sample data on first run
        kv_put("event_data", SAMPLE_EVENT_DATA)
        data = SAMPLE_EVENT_DATA
    return data


# ---------------------------------------------------------------------------
# SQLDB helpers (for lead capture & feedback)
# ---------------------------------------------------------------------------

def sqldb_execute(query: str, params: tuple = ()):
    """Execute a SQL query against Telnyx SQLDB."""
    try:
        conn = telnyx.sqldb.Connection(TELNYX_SQLDB_CONNECTION_STRING)
        cur = conn.cursor()
        cur.execute(query, params)
        conn.commit()
        rows = cur.fetchall() if query.strip().upper().startswith("SELECT") else []
        cur.close()
        conn.close()
        return rows
    except Exception as e:
        app.logger.exception("SQLDB execute failed: %s", e)
        return []


def init_sqldb():
    """Initialize SQLDB tables for leads and feedback."""
    sqldb_execute("""
        CREATE TABLE IF NOT EXISTS exhibitor_leads (
            id SERIAL PRIMARY KEY,
            company TEXT,
            company_size TEXT,
            budget TEXT,
            timeline TEXT,
            phone_number TEXT,
            is_hot_lead BOOLEAN,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    sqldb_execute("""
        CREATE TABLE IF NOT EXISTS post_event_feedback (
            id SERIAL PRIMARY KEY,
            phone_number TEXT,
            audio_url TEXT,
            transcript TEXT,
            summary TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)


# ---------------------------------------------------------------------------
# Webhook signature verification
# ---------------------------------------------------------------------------

def verify_webhook(req):
    """Verify Telnyx webhook signature using Ed25519."""
    signature = req.headers.get("Telnyx-Signature")
    if not signature:
        abort(401, description="Missing Telnyx signature header")
    try:
        telnyx.Webhook.verify_signature(
            payload=req.get_data(),
            signature=signature,
            public_key=TELNYX_PUBLIC_KEY,
        )
    except Exception as e:
        app.logger.exception("Webhook signature verification failed: %s", e)
        abort(401, description="Invalid webhook signature")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    """Render the event microsite from KV data."""
    data = get_event_data()
    html = render_template_string(MICROSITE_HTML, data=data, demo_mode=DEMO_MODE)
    return html


@app.route("/api/event")
def api_event():
    """Return event data as JSON."""
    return jsonify(get_event_data())


@app.route("/api/schedule")
def api_schedule():
    """Return schedule as JSON."""
    return jsonify(get_event_data()["schedule"])


@app.route("/api/speakers")
def api_speakers():
    """Return speakers as JSON."""
    return jsonify(get_event_data()["speakers"])


@app.route("/api/venue")
def api_venue():
    """Return venue info as JSON."""
    return jsonify(get_event_data()["venue"])


@app.route("/api/sponsors")
def api_sponsors():
    """Return sponsors as JSON."""
    return jsonify(get_event_data()["sponsors"])


# ---------------------------------------------------------------------------
# SMS / WhatsApp — AI Concierge
# ---------------------------------------------------------------------------

@app.route("/webhook/sms", methods=["POST"])
def webhook_sms():
    """Handle inbound SMS from attendees to the AI concierge."""
    verify_webhook(request)
    try:
        event = telnyx.Webhook.construct_event(
            payload=request.get_data(),
            signature=request.headers.get("Telnyx-Signature"),
            public_key=TELNYX_PUBLIC_KEY,
        )
        payload = event.data.payload
        from_number = payload.get("from", {}).get("phone_number")
        to_number = payload.get("to", {}).get("phone_number")
        message_text = payload.get("text", "")

        if isinstance(from_number, str) and from_number:
            masked_from_number = "*" * max(len(from_number) - 4, 0) + from_number[-4:]
        else:
            masked_from_number = "[redacted]"

        app.logger.info("SMS from %s: %s", masked_from_number, message_text)

        # AI concierge response using Inference
        response_text = get_ai_concierge_response(message_text)

        if DEMO_MODE:
            masked_from = (
                f"***{from_number[-2:]}"
                if isinstance(from_number, str) and len(from_number) >= 2
                else "***"
            )
            app.logger.info("[DEMO] Would send SMS to %s: %s", masked_from, response_text)
        else:
            telnyx.Message.create(
                from_=TELNYX_SMS_FROM,
                to=from_number,
                text=response_text,
            )

        return jsonify({"status": "ok", "response": response_text})
    except Exception as e:
        app.logger.exception("SMS webhook error: %s", e)
        return jsonify({"error": "Internal server error"}), 500


@app.route("/webhook/whatsapp", methods=["POST"])
def webhook_whatsapp():
    """Handle inbound WhatsApp messages."""
    verify_webhook(request)
    try:
        event = telnyx.Webhook.construct_event(
            payload=request.get_data(),
            signature=request.headers.get("Telnyx-Signature"),
            public_key=TELNYX_PUBLIC_KEY,
        )
        payload = event.data.payload
        from_number = payload.get("from", {}).get("phone_number")
        message_text = payload.get("text", {}).get("body", "")

        app.logger.info("WhatsApp from %s: %s", from_number, message_text)

        response_text = get_ai_concierge_response(message_text)

        if DEMO_MODE:
            app.logger.info("[DEMO] Would send WhatsApp to %s: %s", from_number, response_text)
        else:
            telnyx.Message.create(
                from_=TELNYX_WHATSAPP_FROM,
                to=from_number,
                text=response_text,
            )

        return jsonify({"status": "ok", "response": response_text})
    except Exception as e:
        app.logger.exception("WhatsApp webhook error: %s", e)
        return jsonify({"error": "Internal server error"}), 500


def get_ai_concierge_response(user_message: str) -> str:
    """Use Telnyx Inference to generate an AI concierge response."""
    try:
        response = telnyx.Inference.create_completion(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": TELNYX_AI_CONCIERGE_PROMPT},
                {"role": "user", "content": user_message},
            ],
            max_tokens=256,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        app.logger.exception("Inference error: %s", e)
        return "Sorry, I'm having trouble processing your request right now. Please try again later."


# ---------------------------------------------------------------------------
# Voice — AI Concierge via Voice AI WebSocket
# ---------------------------------------------------------------------------

@app.route("/webhook/voice", methods=["POST"])
def webhook_voice():
    """Handle inbound voice calls — connect to AI concierge via Voice AI WebSocket."""
    verify_webhook(request)
    try:
        event = telnyx.Webhook.construct_event(
            payload=request.get_data(),
            signature=request.headers.get("Telnyx-Signature"),
            public_key=TELNYX_PUBLIC_KEY,
        )
        payload = event.data.payload
        call_control_id = payload.get("call_control_id")
        call_leg_id = payload.get("call_leg_id")

        app.logger.info("Inbound voice call: %s", call_control_id)

        if DEMO_MODE:
            app.logger.info("[DEMO] Would answer call %s and connect to AI concierge", call_control_id)
            return jsonify({"status": "demo", "call_control_id": call_control_id})

        # Answer the call
        telnyx.Call.answer(
            call_control_id=call_control_id,
        )

        # Connect to Voice AI WebSocket for real-time conversation
        telnyx.Call.start_voice_ai(
            call_control_id=call_control_id,
            model="gpt-4o-mini",
            prompt=TELNYX_AI_CONCIERGE_PROMPT,
            voice="en-US-JennyNeural",
        )

        return jsonify({"status": "ok", "call_control_id": call_control_id})
    except Exception as e:
        app.logger.exception("Voice webhook error: %s", e)
        return jsonify({"error": "Internal server error"}), 500


@app.route("/webhook/voice-ai", methods=["POST"])
def webhook_voice_ai():
    """Handle Voice AI WebSocket events (transcription, AI responses)."""
    verify_webhook(request)
    try:
        event = telnyx.Webhook.construct_event(
            payload=request.get_data(),
            signature=request.headers.get("Telnyx-Signature"),
            public_key=TELNYX_PUBLIC_KEY,
        )
        payload = event.data.payload
        event_type = event.type

        app.logger.info("Voice AI event: %s", event_type)

        if event_type == "call.started":
            app.logger.info("Call started: %s", payload.get("call_control_id"))
        elif event_type == "call.answered":
            app.logger.info("Call answered: %s", payload.get("call_control_id"))
        elif event_type == "transcription.received":
            transcript = payload.get("transcript", "")
            app.logger.info("Transcript: %s", transcript)
        elif event_type == "call.ended":
            app.logger.info("Call ended: %s", payload.get("call_control_id"))

        return jsonify({"status": "ok"})
    except Exception as e:
        app.logger.exception("Voice AI webhook error: %s", e)
        return jsonify({"error": "Internal server error"}), 500


# ---------------------------------------------------------------------------
# Broadcast schedule changes over SMS and WhatsApp
# ---------------------------------------------------------------------------

@app.route("/api/broadcast-schedule-change", methods=["POST"])
def broadcast_schedule_change():
    """Broadcast a schedule change to all registered attendees via SMS and WhatsApp."""
    try:
        body = request.get_json() or {}
        change_description = body.get("change", "Schedule update")
        affected_session = body.get("session", "")

        # Fetch registered attendee phone numbers from SQLDB
        attendees = sqldb_execute(
            "SELECT phone_number FROM event_attendees WHERE opted_in = TRUE"
        )

        message = f"📢 Schedule Update: {change_description}"
        if affected_session:
            message += f" (Session: {affected_session})"

        sent_count = 0
        for row in attendees:
            phone = row[0]
            if DEMO_MODE:
                app.logger.info("[DEMO] Would broadcast to %s: %s", phone, message)
            else:
                # Send via SMS
                telnyx.Message.create(
                    from_=TELNYX_SMS_FROM,
                    to=phone,
                    text=message,
                )
                # Send via WhatsApp
                telnyx.Message.create(
                    from_=TELNYX_WHATSAPP_FROM,
                    to=phone,
                    text=message,
                )
            sent_count += 1

        return jsonify({
            "status": "ok",
            "message": message,
            "recipients": sent_count,
            "demo_mode": DEMO_MODE,
        })
    except Exception as e:
        app.logger.exception("Broadcast error: %s", e)
        return jsonify({"error": "Internal server error"}), 500


# ---------------------------------------------------------------------------
# Exhibitor lead qualification & routing
# ---------------------------------------------------------------------------

@app.route("/api/qualify-lead", methods=["POST"])
def qualify_lead():
    """Capture exhibitor lead info, qualify, and route hot leads to sales rep via SMS."""
    try:
        body = request.get_json() or {}
        company = body.get("company", "")
        company_size = body.get("company_size", "")
        budget = body.get("budget", "")
        timeline = body.get("timeline", "")
        phone_number = body.get("phone_number", "")

        if not all([company, company_size, budget, timeline, phone_number]):
            return jsonify({"error": "Missing required lead fields"}), 400

        # Qualify: hot lead if budget is high and timeline is near-term
        is_hot_lead = budget.lower() in ("high", "enterprise") and timeline.lower() in ("immediate", "q2 2025", "within 30 days")

        # Store lead in SQLDB
        sqldb_execute(
            "INSERT INTO exhibitor_leads (company, company_size, budget, timeline, phone_number, is_hot_lead) VALUES (%s, %s, %s, %s, %s, %s)",
            (company, company_size, budget, timeline, phone_number, is_hot_lead),
        )

        if is_hot_lead:
            lead_message = (
                f"🔥 HOT LEAD: {company} ({company_size}) "
                f"Budget: {budget} | Timeline: {timeline} | Phone: {phone_number}"
            )
            if DEMO_MODE:
                app.logger.info("[DEMO] Would SMS hot lead to sales rep %s: %s", TELNYX_SALES_REP_PHONE, lead_message)
            else:
                telnyx.Message.create(
                    from_=TELNYX_SMS_FROM,
                    to=TELNYX_SALES_REP_PHONE,
                    text=lead_message,
                )
            app.logger.info("Hot lead routed to sales rep: %s", company)

        return jsonify({
            "status": "ok",
            "company": company,
            "is_hot_lead": is_hot_lead,
            "routed_to_sales": is_hot_lead,
            "demo_mode": DEMO_MODE,
        })
    except Exception as e:
        app.logger.exception("Lead qualification error: %s", e)
        return jsonify({"error": "Internal server error"}), 500


# ---------------------------------------------------------------------------
# Post-event feedback transcription & sponsor report
# ---------------------------------------------------------------------------

@app.route("/api/submit-feedback", methods=["POST"])
def submit_feedback():
    """Accept post-event spoken feedback, transcribe via Inference, summarize into sponsor report."""
    try:
        body = request.get_json() or {}
        phone_number = body.get("phone_number", "")
        audio_url = body.get("audio_url", "")

        if not phone_number or not audio_url:
            return jsonify({"error": "Missing phone_number or audio_url"}), 400

        # Transcribe audio using Telnyx Inference (Whisper)
        transcript = transcribe_audio(audio_url)

        # Summarize transcript for sponsor report
        summary = summarize_feedback(transcript)

        # Store in SQLDB
        sqldb_execute(
            "INSERT INTO post_event_feedback (phone_number, audio_url, transcript, summary) VALUES (%s, %s, %s, %s)",
            (phone_number, audio_url, transcript, summary),
        )

        return jsonify({
            "status": "ok",
            "transcript": transcript,
            "summary": summary,
            "demo_mode": DEMO_MODE,
        })
    except Exception as e:
        app.logger.exception("Feedback submission error: %s", e)
        return jsonify({"error": "Internal server error"}), 500


def transcribe_audio(audio_url: str) -> str:
    """Transcribe audio using Telnyx Inference Whisper model."""
    try:
        response = telnyx.Inference.create_transcription(
            model="whisper-1",
            file=audio_url,
            prompt="Transcribe the following event feedback audio.",
        )
        return response.text.strip()
    except Exception as e:
        app.logger.exception("Transcription error: %s", e)
        return "[Transcription failed]"


def summarize_feedback(transcript: str) -> str:
    """Summarize feedback transcript using Telnyx Inference."""
    try:
        response = telnyx.Inference.create_completion(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a professional event analyst. Summarize the following feedback into a concise sponsor report."},
                {"role": "user", "content": transcript},
            ],
            max_tokens=512,
            temperature=0.5,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        app.logger.exception("Summarization error: %s", e)
        return "[Summarization failed]"


@app.route("/api/sponsor-report")
def sponsor_report():
    """Generate a sponsor report from all collected feedback."""
    try:
        rows = sqldb_execute(
            "SELECT company, phone_number, transcript, summary, created_at FROM post_event_feedback ORDER BY created_at DESC"
        )
        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_feedback_items": len(rows),
            "feedback": [
                {
                    "phone_number": row[1],
                    "transcript": row[2],
                    "summary": row[3],
                    "created_at": row[4],
                }
                for row in rows
            ],
        }
        return jsonify(report)
    except Exception as e:
        app.logger.exception("Sponsor report error: %s", e)
        return jsonify({"error": "Internal server error"}), 500


# ---------------------------------------------------------------------------
# In-browser voice WebSocket endpoint
# ---------------------------------------------------------------------------

@app.route("/api/voice-websocket-info")
def voice_websocket_info():
    """Return info for in-browser Voice AI WebSocket connection."""
    return jsonify({
        "connection_id": TELNYX_VOICE_CONNECTION_ID,
        "domain": TELNYX_EVENT_DOMAIN,
        "ai_concierge_name": TELNYX_AI_CONCIERGE_NAME,
        "demo_mode": DEMO_MODE,
    })


# ---------------------------------------------------------------------------
# HTML template for the microsite
# ---------------------------------------------------------------------------

MICROSITE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ data.event.name }}</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; margin: 0; padding: 0; background: #f5f5f5; color: #333; }
        header { background: #0062ff; color: white; padding: 2rem; text-align: center; }
        .container { max-width: 900px; margin: 0 auto; padding: 1rem; }
        .section { background: white; margin: 1rem 0; padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h2 { color: #0062ff; border-bottom: 2px solid #0062ff; padding-bottom: 0.5rem; }
        .schedule-item { border-left: 3px solid #0062ff; padding: 0.5rem 1rem; margin: 0.5rem 0; }
        .speaker-card { display: inline-block; margin: 0.5rem; padding: 1rem; border: 1px solid #ddd; border-radius: 8px; text-align: center; }
        .sponsor-card { display: inline-block; margin: 0.5rem; padding: 0.5rem; border: 1px solid #ddd; border-radius: 8px; }
        .contact-box { background: #e8f0fe; padding: 1rem; border-radius: 8px; text-align: center; }
        .badge { display: inline-block; background: #ff6b35; color: white; padding: 0.2rem 0.8rem; border-radius: 12px; font-size: 0.8rem; }
        footer { text-align: center; padding: 1rem; color: #666; }
    </style>
</head>
<body>
    <header>
        <h1>{{ data.event.name }}</h1>
        <p>{{ data.event.date }} • {{ data.event.location }}</p>
        {% if demo_mode %}<span class="badge">DEMO MODE</span>{% endif %}
    </header>
    <div class="container">
        <div class="section">
            <h2>About</h2>
            <p>{{ data.event.description }}</p>
        </div>
        <div class="section">
            <h2>Schedule</h2>
            {% for item in data.schedule %}
            <div class="schedule-item">
                <strong>{{ item.time }}</strong> — {{ item.title }}
                {% if item.speaker %}<br><em>by {{ item.speaker }}</em>{% endif %}
                <br><small>📍 {{ item.room }}</small>
            </div>
            {% endfor %}
        </div>
        <div class="section">
            <h2>Speakers</h2>
            {% for speaker in data.speakers %}
            <div class="speaker-card">
                <img src="{{ speaker.photo }}" width="80" height="80" style="border-radius: 50%;">
                <h3>{{ speaker.name }}</h3>
                <p>{{ speaker.title }}</p>
                <small>{{ speaker.bio }}</small>
            </div>
            {% endfor %}
        </div>
        <div class="section">
            <h2>Venue</h2>
            <p><strong>Address:</strong> {{ data.venue.address }}</p>
            <p><strong>WiFi:</strong> {{ data.venue.wifi }}</p>
            <p><strong>Parking:</strong> {{ data.venue.parking }}</p>
            <a href="{{ data.venue.map_url }}" target="_blank">View Map</a>
        </div>
        <div class="section">
            <h2>Sponsors</h2>
            {% for sponsor in data.sponsors %}
            <div class="sponsor-card">
                <img src="{{ sponsor.logo }}" width="60" height="60">
                <h3>{{ sponsor.name }}</h3>
                <span class="badge">{{ sponsor.tier }}</span>
            </div>
            {% endfor %}
        </div>
        <div class="section contact-box">
            <h2>Need Help?</h2>
            <p>Text, call, or talk in-browser to our AI Concierge:</p>
            <ul>
                <li><strong>SMS:</strong> {{ data.venue.wifi.split('|')[0].split(':')[0] }}</li>
                <li><strong>WhatsApp:</strong> Same number</li>
                <li><strong>Voice:</strong> Call the same number</li>
                <li><strong>In-browser:</strong> Click "Talk to Concierge" below</li>
            </ul>
            <button onclick="initVoiceAI()" style="padding: 0.8rem 2rem; background: #0062ff; color: white; border: none; border-radius: 6px; cursor: pointer;">
                Talk to Concierge
            </button>
            <p><small>Powered by Telnyx Voice AI</small></p>
        </div>
    </div>
    <footer>
        <p>&copy; {{ data.event.date.split('-')[0] }} {{ data.event.name }}. All rights reserved.</p>
    </footer>
    <script>
        function initVoiceAI() {
            alert("Voice AI WebSocket connection would initialize here.\\nConnection ID: " + "{{ TELNYX_VOICE_CONNECTION_ID }}");
        }
    </script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------

@app.errorhandler(401)
def unauthorized(e):
    return jsonify({"error": "Unauthorized"}), 401


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def internal_error(e):
    app.logger.exception("Internal server error: %s", e)
    return jsonify({"error": "Internal server error"}), 500


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    init_sqldb()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=DEMO_MODE)
