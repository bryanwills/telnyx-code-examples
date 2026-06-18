#!/usr/bin/env python3
"""AI Phone Story Hotline — call a number, choose a genre, and listen to an AI-generated interactive story where your choices shape the narrative."""
import os, json, time, requests, telnyx
from dotenv import load_dotenv
from flask import Flask, request, jsonify
load_dotenv()
app = Flask(__name__)
client = telnyx.Telnyx(api_key=os.getenv("TELNYX_API_KEY"))
TELNYX_API_KEY = os.getenv("TELNYX_API_KEY")
AI_MODEL = os.getenv("AI_MODEL", "moonshotai/Kimi-K2.6")
STORY_NUMBER = os.getenv("STORY_NUMBER")
INFERENCE_URL = "https://api.telnyx.com/v2/ai/chat/completions"
active_calls = {}
GENRES = {"1": "mystery", "2": "sci-fi", "3": "fantasy", "4": "horror", "5": "romance"}

def call_inference(messages, max_tokens=250):
    resp = requests.post(INFERENCE_URL, headers={"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"},
        json={"model": AI_MODEL, "messages": messages, "max_tokens": max_tokens, "temperature": 0.9}, timeout=20)
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
        active_calls[ccid] = {"state": "genre_select", "conversation": [], "chapters": 0}
        client.calls.actions.answer(ccid)
        return jsonify({"status": "answering"}), 200
    elif event_type == "call.answered":
        client.calls.actions.speak(ccid, payload="Welcome to Story Hotline! Choose your adventure. Press 1 for Mystery, 2 for Sci-Fi, 3 for Fantasy, 4 for Horror, 5 for Romance.", voice="female", language_code="en-US")
        return jsonify({"status": "greeting"}), 200
    elif event_type == "call.speak.ended" and call:
        if call["state"] == "genre_select":
            client.calls.actions.gather(ccid, input_type="dtmf", timeout_secs=10, min_digits=1, max_digits=1)
        else:
            client.calls.actions.gather(ccid, input_type="speech dtmf", end_silence_timeout_secs=3, timeout_secs=20, language_code="en-US")
        return jsonify({"status": "listening"}), 200
    elif event_type == "call.gather.ended" and call:
        digits = data.get("digits", "")
        speech = data.get("speech", {}).get("result", "")
        if call["state"] == "genre_select":
            genre = GENRES.get(digits, "mystery")
            call["state"] = "story"
            call["conversation"] = [{"role": "system", "content": f"You are an interactive {genre} storyteller on a phone hotline. Tell a gripping story in short chapters (3-4 sentences each). End each chapter with exactly TWO choices: 'Press 1 to...' or 'Press 2 to...'. Make it vivid and cinematic. After 5 chapters, bring the story to a satisfying ending."}]
            story_start = call_inference(call["conversation"] + [{"role": "user", "content": "Begin the story."}])
            call["conversation"].append({"role": "assistant", "content": story_start})
            call["chapters"] = 1
            client.calls.actions.speak(ccid, payload=story_start, voice="female", language_code="en-US")
        elif call["state"] == "story":
            choice = digits or speech
            if not choice:
                client.calls.actions.speak(ccid, payload="Press 1 or 2 to choose your path.", voice="female", language_code="en-US")
                return jsonify({"status": "reprompting"}), 200
            call["conversation"].append({"role": "user", "content": f"I choose option {choice}"})
            call["chapters"] += 1
            if call["chapters"] >= 5:
                call["conversation"][-1]["content"] += ". Bring the story to a dramatic conclusion."
            continuation = call_inference(call["conversation"])
            call["conversation"].append({"role": "assistant", "content": continuation})
            client.calls.actions.speak(ccid, payload=continuation, voice="female", language_code="en-US")
        return jsonify({"status": "storytelling"}), 200
    elif event_type == "call.hangup":
        active_calls.pop(ccid, None)
        return jsonify({"status": "ended"}), 200
    return jsonify({"status": "ok"}), 200

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "active_stories": len(active_calls)}), 200

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
