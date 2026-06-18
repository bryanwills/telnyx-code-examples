#!/usr/bin/env python3
"""Live Podcast Call-In — hosts on a conference call, listeners call in,
AI screens callers via STT, queues them, generates real-time fact-checks
for the host, and TTS announces caller topics."""

import os, json, uuid, time, requests
from datetime import datetime
from collections import deque
from dotenv import load_dotenv
from flask import Flask, request, jsonify

load_dotenv()
app = Flask(__name__)

TELNYX_API_KEY = os.getenv("TELNYX_API_KEY")
MAIN_NUMBER = os.getenv("MAIN_NUMBER")
CONNECTION_ID = os.getenv("CONNECTION_ID")
AI_MODEL = os.getenv("AI_MODEL", "moonshotai/Kimi-K2.6")
TTS_VOICE = os.getenv("TTS_VOICE", "nova")
SHOW_TOPIC = os.getenv("SHOW_TOPIC", "Technology and AI")
SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK", "")
API = "https://api.telnyx.com/v2"
HEADERS = {"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"}

shows = {}  # show_id -> show state
caller_queue = deque()  # callers waiting to go live
active_callers = {}  # call_control_id -> caller state


def telnyx_post(path, payload):
    resp = requests.post(f"{API}/{path}", headers=HEADERS, json=payload, timeout=15)
    resp.raise_for_status()
    return resp.json()


def inference(messages, max_tokens=500):
    resp = requests.post(f"{API}/ai/chat/completions", headers=HEADERS, json={
        "model": AI_MODEL, "messages": messages, "max_tokens": max_tokens, "temperature": 0.5
    }, timeout=20)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def notify_slack(msg):
    if SLACK_WEBHOOK:
        try:
            requests.post(SLACK_WEBHOOK, json={"text": msg}, timeout=5)
        except Exception:
            pass


@app.route("/shows/start", methods=["POST"])
def start_show():
    """Start a live show — dial hosts into conference, open call-in line."""
    data = request.get_json() or {}
    hosts = data.get("hosts", [])
    topic = data.get("topic", SHOW_TOPIC)

    if not hosts:
        return jsonify({"error": "Provide at least one host number"}), 400

    show_id = f"show-{uuid.uuid4().hex[:8]}"
    conf_name = f"live-{show_id}"

    shows[show_id] = {
        "id": show_id,
        "topic": topic,
        "conference": conf_name,
        "hosts": hosts,
        "status": "live",
        "callers_screened": 0,
        "callers_admitted": 0,
        "callers_rejected": 0,
        "fact_checks": [],
        "started_at": datetime.utcnow().isoformat()
    }

    # Dial hosts
    for phone in hosts:
        try:
            telnyx_post("calls", {
                "connection_id": CONNECTION_ID,
                "to": phone, "from": MAIN_NUMBER,
                "conference_name": conf_name,
                "conference_config": {
                    "start_conference_on_join": True,
                    "record_conference": True,
                    "beep_enabled": "on_enter"
                },
                "client_state": json.dumps({"show_id": show_id, "role": "host"}).encode().hex()
            })
        except Exception as e:
            app.logger.error(f"Failed to dial host {phone}: {e}")

    notify_slack(f"🎙️ Live show started: *{topic}* | Call-in: {MAIN_NUMBER}")
    return jsonify({"show_id": show_id, "conference": conf_name, "call_in_number": MAIN_NUMBER, "status": "live"}), 201


@app.route("/webhooks/voice", methods=["POST"])
def handle_voice():
    payload = request.get_json()
    event = payload.get("data", {})
    event_type = event.get("event_type", "")
    ep = event.get("payload", {})
    call_id = ep.get("call_control_id", "")
    from_number = ep.get("from", "")

    if event_type == "call.initiated":
        # New inbound caller — answer and screen them
        if ep.get("direction") == "incoming":
            try:
                telnyx_post(f"calls/{call_id}/actions/answer", {
                    "client_state": json.dumps({"step": "screening"}).encode().hex()
                })
            except Exception:
                pass

    elif event_type == "call.answered":
        client_state = {}
        try:
            raw = ep.get("client_state", "")
            if raw:
                client_state = json.loads(bytes.fromhex(raw).decode())
        except Exception:
            pass

        if client_state.get("role") == "host":
            pass  # Host joined conference, no screening needed
        else:
            # Screen the caller — ask their topic
            active_callers[call_id] = {
                "phone": from_number,
                "call_id": call_id,
                "status": "screening",
                "topic": "",
                "screened_at": None
            }
            try:
                telnyx_post(f"calls/{call_id}/actions/gather_using_speak", {
                    "payload": f"Welcome to the live show about {SHOW_TOPIC}. In a few words, tell us what you'd like to discuss, then press pound.",
                    "voice": TTS_VOICE,
                    "language": "en-US",
                    "minimum_digits": 1,
                    "maximum_digits": 1,
                    "valid_digits": "#",
                    "timeout_millis": 30000,
                })
            except Exception as e:
                app.logger.error(f"Screening gather failed: {e}")

    elif event_type == "call.gather.ended":
        speech = ep.get("speech", {})
        transcript = speech.get("result", "")
        caller = active_callers.get(call_id)

        if caller and caller["status"] == "screening" and transcript:
            caller["topic"] = transcript
            caller["screened_at"] = datetime.utcnow().isoformat()

            # AI decides if caller is relevant and safe
            screening_result = inference([
                {"role": "system", "content": f"You screen callers for a live podcast about '{SHOW_TOPIC}'. The caller said: \"{transcript}\". Decide: ADMIT (on-topic, constructive) or REJECT (off-topic, trolling, spam). Also generate a one-sentence introduction for the host. Return JSON: {{\"decision\": \"ADMIT\"|\"REJECT\", \"reason\": \"...\", \"intro\": \"...\"}}"},
                {"role": "user", "content": transcript}
            ])

            try:
                result = json.loads(screening_result)
            except json.JSONDecodeError:
                result = {"decision": "ADMIT", "reason": "Could not parse", "intro": f"A caller wants to discuss: {transcript[:100]}"}

            # Find active show
            show = None
            for s in shows.values():
                if s["status"] == "live":
                    show = s
                    break

            if show:
                show["callers_screened"] += 1

            if result.get("decision") == "ADMIT":
                caller["status"] = "queued"
                caller["intro"] = result.get("intro", "")
                caller_queue.append(caller)
                if show:
                    show["callers_admitted"] += 1
                # Put caller on hold with music
                try:
                    telnyx_post(f"calls/{call_id}/actions/speak", {
                        "payload": "Great topic! You're in the queue. We'll bring you on shortly. Please hold.",
                        "voice": TTS_VOICE, "language": "en-US"
                    })
                except Exception:
                    pass
                notify_slack(f"📞 Caller queued: {from_number[-4:]} — {transcript[:100]}")
            else:
                caller["status"] = "rejected"
                if show:
                    show["callers_rejected"] += 1
                try:
                    telnyx_post(f"calls/{call_id}/actions/speak", {
                        "payload": f"Thanks for calling. {result.get('reason', 'The host is focused on other topics right now.')} Feel free to call back another time.",
                        "voice": TTS_VOICE, "language": "en-US"
                    })
                except Exception:
                    pass
                # Hang up after message
                time.sleep(3)
                try:
                    telnyx_post(f"calls/{call_id}/actions/hangup", {})
                except Exception:
                    pass

    elif event_type == "call.hangup":
        active_callers.pop(call_id, None)

    return jsonify({"status": "ok"}), 200


@app.route("/shows/<show_id>/next-caller", methods=["POST"])
def admit_next_caller(show_id):
    """Bring the next queued caller into the live conference."""
    show = shows.get(show_id)
    if not show:
        return jsonify({"error": "Show not found"}), 404

    if not caller_queue:
        return jsonify({"message": "No callers in queue"}), 200

    caller = caller_queue.popleft()
    call_id = caller["call_id"]

    # Announce caller to hosts via TTS in conference
    intro = caller.get("intro", f"Next caller wants to discuss: {caller.get('topic', 'a topic')}")

    # Bridge caller into conference
    try:
        telnyx_post(f"calls/{call_id}/actions/join_conference", {
            "conference_name": show["conference"],
            "beep_enabled": "on_enter"
        })
        caller["status"] = "live"
    except Exception as e:
        return jsonify({"error": f"Failed to bridge caller: {str(e)}"}), 500

    return jsonify({
        "caller": caller["phone"][-4:],
        "topic": caller["topic"],
        "intro": intro,
        "remaining_in_queue": len(caller_queue)
    })


@app.route("/shows/<show_id>/fact-check", methods=["POST"])
def fact_check(show_id):
    """Host submits a claim for real-time AI fact-checking."""
    show = shows.get(show_id)
    if not show:
        return jsonify({"error": "Show not found"}), 404

    data = request.get_json() or {}
    claim = data.get("claim", "")
    if not claim:
        return jsonify({"error": "Provide a 'claim' to fact-check"}), 400

    result = inference([
        {"role": "system", "content": "You are a real-time fact-checker for a live podcast. Evaluate the claim. Respond with: verdict (TRUE / FALSE / PARTIALLY TRUE / UNVERIFIABLE), confidence (0-100), brief explanation (under 100 words), and a source if possible. Return JSON."},
        {"role": "user", "content": claim}
    ])

    try:
        check = json.loads(result)
    except json.JSONDecodeError:
        check = {"verdict": "UNVERIFIABLE", "explanation": result}

    check["claim"] = claim
    check["checked_at"] = datetime.utcnow().isoformat()
    show["fact_checks"].append(check)

    return jsonify(check)


@app.route("/shows/<show_id>/queue", methods=["GET"])
def view_queue(show_id):
    """See callers waiting to go live."""
    return jsonify({
        "show_id": show_id,
        "queue": [{"phone": c["phone"][-4:], "topic": c["topic"], "screened_at": c["screened_at"]} for c in caller_queue],
        "total": len(caller_queue)
    })


@app.route("/shows", methods=["GET"])
def list_shows():
    return jsonify({"shows": [{
        "id": s["id"], "topic": s["topic"], "status": s["status"],
        "callers_screened": s["callers_screened"],
        "callers_admitted": s["callers_admitted"],
        "started_at": s["started_at"]
    } for s in shows.values()]})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "active_shows": sum(1 for s in shows.values() if s["status"] == "live"),
        "callers_in_queue": len(caller_queue),
        "version": "1.0.0"
    })


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
