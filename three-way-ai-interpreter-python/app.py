#!/usr/bin/env python3
"""Three-Way Call with AI Interpreter — two humans speak different languages on the same call. AI translates in real-time and speaks the translation to each party via separate conference legs."""
import os
import json
import time
import base64
import requests
from dotenv import load_dotenv
from flask import Flask, request, jsonify

load_dotenv()
app = Flask(__name__)

TELNYX_API_KEY = os.getenv("TELNYX_API_KEY")
MAIN_NUMBER = os.getenv("MAIN_NUMBER")
CONNECTION_ID = os.getenv("CONNECTION_ID")
AI_MODEL = os.getenv("AI_MODEL", "moonshotai/Kimi-K2.6")
API = "https://api.telnyx.com/v2"
HEADERS = {"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"}

sessions = {}


def telnyx_post(path, data):
    resp = requests.post(f"{API}{path}", headers=HEADERS, json=data, timeout=10)
    resp.raise_for_status()
    return resp.json()


def telnyx_call_action(call_id, action, data=None):
    return telnyx_post(f"/calls/{call_id}/actions/{action}", data or {})


def call_inference(messages, max_tokens=200):
    resp = requests.post(f"{API}/ai/chat/completions", headers=HEADERS,
        json={"model": AI_MODEL, "messages": messages, "max_tokens": max_tokens, "temperature": 0.3}, timeout=15)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def translate(text, from_lang, to_lang):
    """Translate text using Telnyx AI Inference."""
    return call_inference([
        {"role": "system", "content": f"You are a real-time phone interpreter. Translate the following from {from_lang} to {to_lang}. Output ONLY the translation, nothing else. Keep the same tone and register. If the text is very short or a filler word, translate it naturally."},
        {"role": "user", "content": text},
    ], max_tokens=300)


@app.route("/interpret/start", methods=["POST"])
def start_session():
    """Start an interpreted call between two parties speaking different languages."""
    data = request.get_json() or {}
    party_a_phone = data.get("party_a")
    party_b_phone = data.get("party_b")
    lang_a = data.get("language_a", "English")
    lang_b = data.get("language_b", "Spanish")
    conf_name = f"interp-{int(time.time())}"

    session = {
        "conference": conf_name,
        "party_a": {"phone": party_a_phone, "language": lang_a, "call_id": None},
        "party_b": {"phone": party_b_phone, "language": lang_b, "call_id": None},
        "transcript": [],
        "created_at": time.time(),
        "status": "dialing",
    }
    sessions[conf_name] = session

    # Dial both parties
    for party_key, phone in [("party_a", party_a_phone), ("party_b", party_b_phone)]:
        resp = telnyx_post("/calls", {
            "connection_id": CONNECTION_ID,
            "from": MAIN_NUMBER,
            "to": phone,
            "webhook_url": request.url_root.rstrip("/") + "/webhooks/voice",
            "client_state": base64.b64encode(json.dumps({
                "conference": conf_name, "party": party_key,
            }).encode()).decode(),
        })
        session[party_key]["call_id"] = resp.get("data", {}).get("call_control_id", "")

    return jsonify({"session": conf_name, "languages": f"{lang_a} <-> {lang_b}"}), 201


@app.route("/webhooks/voice", methods=["POST"])
def handle_voice():
    payload = request.get_json()
    data = payload.get("data", {})
    event = data.get("event_type", "")
    call_id = data.get("call_control_id", "")
    client_state = {}
    if data.get("client_state"):
        try:
            client_state = json.loads(base64.b64decode(data["client_state"]))
        except Exception:
            pass

    conf_name = client_state.get("conference", "")
    session = sessions.get(conf_name)
    if not session:
        return jsonify({"status": "no_session"}), 200

    party_key = client_state.get("party", "")

    if event == "call.answered":
        party = session.get(party_key, {})
        lang = party.get("language", "English")

        # Join to conference
        telnyx_call_action(call_id, "join", {
            "name": conf_name,
            "start_conference_on_create": True,
            "hold": False, "mute": False,
            "supervisor_role": "none",
        })

        # Greet in their language
        if lang == "English":
            greeting = "You're connected to an interpreted call. Speak naturally and pause between sentences for translation."
        elif lang == "Spanish":
            greeting = "Está conectado a una llamada con intérprete. Hable con naturalidad y haga pausas entre oraciones para la traducción."
        elif lang == "French":
            greeting = "Vous êtes connecté à un appel interprété. Parlez naturellement et faites des pauses entre les phrases pour la traduction."
        elif lang == "Mandarin":
            greeting = "您已连接到口译电话。请自然地说话，在句子之间停顿以进行翻译。"
        elif lang == "Arabic":
            greeting = "أنت متصل بمكالمة مع مترجم. تحدث بشكل طبيعي وتوقف بين الجمل للترجمة."
        else:
            greeting = f"Connected. Interpretation between {session['party_a']['language']} and {session['party_b']['language']}."

        telnyx_call_action(call_id, "speak", {
            "payload": greeting,
            "language": "en-US", "voice": "female",
        })

        # Check if both parties are connected
        a_id = session["party_a"].get("call_id")
        b_id = session["party_b"].get("call_id")
        if a_id and b_id:
            session["status"] = "live"

        return jsonify({"status": "answered"}), 200

    if event == "call.speak.ended":
        # After greeting or translation, listen for speech
        telnyx_call_action(call_id, "gather_using_speak", {
            "payload": " ",
            "language": "en-US", "voice": "female",
            "minimum_digits": 1, "maximum_digits": 1,
            "inter_digit_timeout": 20,
            "valid_digits": "0123456789*#",
            "client_state": base64.b64encode(json.dumps({
                "conference": conf_name, "party": party_key, "listening": True,
            }).encode()).decode(),
        })
        return jsonify({"status": "listening"}), 200

    if event == "call.gather.ended":
        speech = data.get("speech", {}).get("result", "")
        if speech and session:
            party = session.get(party_key, {})
            from_lang = party.get("language", "English")

            # Determine the other party
            other_key = "party_b" if party_key == "party_a" else "party_a"
            other = session.get(other_key, {})
            to_lang = other.get("language", "English")
            other_call_id = other.get("call_id")

            # Log original
            session["transcript"].append({
                "time": time.time(),
                "speaker": party_key,
                "language": from_lang,
                "original": speech,
            })

            # Translate and speak to the other party
            if from_lang != to_lang and other_call_id:
                translation = translate(speech, from_lang, to_lang)
                session["transcript"][-1]["translation"] = translation

                telnyx_call_action(other_call_id, "speak", {
                    "payload": translation,
                    "language": "en-US",
                    "voice": "female",
                })

        # Continue listening on this leg
        telnyx_call_action(call_id, "gather_using_speak", {
            "payload": " ",
            "language": "en-US", "voice": "female",
            "minimum_digits": 1, "maximum_digits": 1,
            "inter_digit_timeout": 20,
            "valid_digits": "0123456789*#",
            "client_state": base64.b64encode(json.dumps({
                "conference": conf_name, "party": party_key, "listening": True,
            }).encode()).decode(),
        })
        return jsonify({"status": "translated"}), 200

    if event == "call.hangup":
        session["status"] = "ended"
        # Generate bilingual summary
        if session["transcript"]:
            lines = []
            for t in session["transcript"]:
                lines.append(f"{t['speaker']} ({t['language']}): {t['original']}")
                if t.get("translation"):
                    lines.append(f"  -> {t.get('translation')}")
            summary = call_inference([
                {"role": "system", "content": "Summarize this interpreted phone call in English. Note any agreements, next steps, or misunderstandings."},
                {"role": "user", "content": "\n".join(lines)},
            ])
            session["summary"] = summary
        return jsonify({"status": "ended"}), 200

    return jsonify({"status": "ok"}), 200


@app.route("/sessions", methods=["GET"])
def list_sessions():
    return jsonify({"sessions": [{
        "id": s["conference"], "status": s["status"],
        "languages": f"{s['party_a']['language']} <-> {s['party_b']['language']}",
        "turns": len(s["transcript"]),
    } for s in sessions.values()]}), 200


@app.route("/sessions/<sid>/transcript", methods=["GET"])
def get_transcript(sid):
    s = sessions.get(sid)
    if not s:
        return jsonify({"error": "not found"}), 404
    return jsonify({"transcript": s["transcript"], "summary": s.get("summary", "")}), 200


@app.route("/health", methods=["GET"])
def health():
    active = sum(1 for s in sessions.values() if s["status"] == "live")
    return jsonify({"status": "ok", "active_sessions": active, "total": len(sessions)}), 200


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
