#!/usr/bin/env python3
"""SMS Escape Room Game — text-based adventure game over SMS. Solve puzzles, find clues, escape before time runs out."""
import os, json, time, requests
from dotenv import load_dotenv
from flask import Flask, request, jsonify
load_dotenv()
app = Flask(__name__)
TELNYX_API_KEY = os.getenv("TELNYX_API_KEY")
AI_MODEL = os.getenv("AI_MODEL", "moonshotai/Kimi-K2.6")
GAME_NUMBER = os.getenv("GAME_NUMBER")
MESSAGING_PROFILE_ID = os.getenv("MESSAGING_PROFILE_ID", "")
INFERENCE_URL = "https://api.telnyx.com/v2/ai/chat/completions"
games = {}

GAME_PROMPT = """You are running a text-based escape room game over SMS. The player is trapped in a mysterious library.
Room contains: a locked desk drawer, a bookshelf with a gap, a painting that seems crooked, a grandfather clock stuck at 3:15, and a note on the floor.
Puzzle chain: note has riddle -> answer reveals bookshelf book -> book has a 4-digit code -> code opens desk -> desk has a key -> key used on the door.
Keep responses under 160 chars when possible (SMS). Be atmospheric. Track what the player has found.
The code is 1847. The book is 'The Time Machine'. The riddle answer is 'time'.
If they solve it within 10 messages, they escaped FAST. Within 20, they escaped. After 20, time's up."""

def send_sms(to, text):
    try:
        requests.post("https://api.telnyx.com/v2/messages", headers={"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"},
            json={"from": GAME_NUMBER, "to": to, "text": text, "messaging_profile_id": MESSAGING_PROFILE_ID}, timeout=10)
    except Exception as e:
        app.logger.error(f"SMS failed: {e}")

def call_inference(messages, max_tokens=160):
    resp = requests.post(INFERENCE_URL, headers={"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"},
        json={"model": AI_MODEL, "messages": messages, "max_tokens": max_tokens, "temperature": 0.8}, timeout=15)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]

@app.route("/webhooks/messaging", methods=["POST"])
def handle_sms():
    payload = request.get_json()
    data = payload.get("data", {})
    if data.get("event_type") != "message.received" or data.get("direction") != "inbound":
        return jsonify({"status": "ignored"}), 200
    phone = data.get("from", {}).get("phone_number", "")
    text = data.get("text", "").strip()
    if text.upper() == "PLAY" or phone not in games:
        games[phone] = {"conversation": [{"role": "system", "content": GAME_PROMPT}], "moves": 0, "start": time.time(), "status": "playing"}
        intro = call_inference(games[phone]["conversation"] + [{"role": "user", "content": "Start the game. Describe the room."}])
        games[phone]["conversation"].append({"role": "assistant", "content": intro})
        send_sms(phone, intro)
        return jsonify({"status": "started"}), 200
    game = games[phone]
    if game["status"] != "playing":
        send_sms(phone, f"Game over! You escaped in {game['moves']} moves. Text PLAY for a new game.")
        return jsonify({"status": "game_over"}), 200
    game["moves"] += 1
    game["conversation"].append({"role": "user", "content": text})
    if game["moves"] > 20:
        game["status"] = "timeout"
        send_sms(phone, "The clock strikes midnight. You ran out of time! Text PLAY to try again.")
        return jsonify({"status": "timeout"}), 200
    response = call_inference(game["conversation"])
    game["conversation"].append({"role": "assistant", "content": response})
    if "escaped" in response.lower() or "freedom" in response.lower() or "you win" in response.lower():
        game["status"] = "won"
        elapsed = int(time.time() - game["start"])
    send_sms(phone, response)
    return jsonify({"status": "playing"}), 200

@app.route("/leaderboard", methods=["GET"])
def leaderboard():
    winners = [(p, g) for p, g in games.items() if g.get("status") == "won"]
    winners.sort(key=lambda x: x[1]["moves"])
    board = [{"phone": p[-4:], "moves": g["moves"]} for p, g in winners[:10]]
    return jsonify({"leaderboard": board}), 200

@app.route("/health", methods=["GET"])
def health():
    active = sum(1 for g in games.values() if g.get("status") == "playing")
    return jsonify({"status": "ok", "active_games": active, "total": len(games)}), 200

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
