#!/usr/bin/env python3
"""SMS Trivia Game Tournament — multi-player trivia via SMS. Players join, answer timed questions, scores tracked on a live leaderboard."""
import os, json, time, requests
from dotenv import load_dotenv
from flask import Flask, request, jsonify
load_dotenv()
app = Flask(__name__)
TELNYX_API_KEY = os.getenv("TELNYX_API_KEY")
AI_MODEL = os.getenv("AI_MODEL", "moonshotai/Kimi-K2.6")
TRIVIA_NUMBER = os.getenv("TRIVIA_NUMBER")
MESSAGING_PROFILE_ID = os.getenv("MESSAGING_PROFILE_ID", "")
INFERENCE_URL = "https://api.telnyx.com/v2/ai/chat/completions"
tournaments = {}
players = {}

def send_sms(to, text):
    try:
        requests.post("https://api.telnyx.com/v2/messages", headers={"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"},
            json={"from": TRIVIA_NUMBER, "to": to, "text": text, "messaging_profile_id": MESSAGING_PROFILE_ID}, timeout=10)
    except Exception: pass

def generate_question(category="general"):
    resp = requests.post(INFERENCE_URL, headers={"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"},
        json={"model": AI_MODEL, "messages": [{"role": "system", "content": f"Generate a {category} trivia question. Return JSON: question (string), options (list of 4 strings), correct_index (0-3), fun_fact (string, 1 sentence)."}],
            "max_tokens": 200, "temperature": 0.9}, timeout=15)
    resp.raise_for_status()
    return json.loads(resp.json()["choices"][0]["message"]["content"])

@app.route("/tournament/create", methods=["POST"])
def create_tournament():
    data = request.get_json()
    tid = f"T-{int(time.time())}"
    tournaments[tid] = {"name": data.get("name", "Trivia Night"), "category": data.get("category", "general"),
        "rounds": data.get("rounds", 5), "current_round": 0, "current_question": None, "players": {}, "status": "lobby"}
    return jsonify({"tournament_id": tid, "join_code": tid}), 200

@app.route("/webhooks/messaging", methods=["POST"])
def handle_sms():
    payload = request.get_json()
    data = payload.get("data", {})
    if data.get("event_type") != "message.received" or data.get("direction") != "inbound":
        return jsonify({"status": "ignored"}), 200
    phone = data.get("from", {}).get("phone_number", "")
    text = data.get("text", "").strip().upper()
    if text.startswith("JOIN "):
        tid = text.split(" ", 1)[1].strip()
        tournament = tournaments.get(tid)
        if tournament and tournament["status"] == "lobby":
            tournament["players"][phone] = {"score": 0, "answers": 0, "correct": 0}
            players[phone] = tid
            send_sms(phone, f"Joined {tournament['name']}! {len(tournament['players'])} players. Waiting for start.")
        else:
            send_sms(phone, "Tournament not found or already started.")
        return jsonify({"status": "joined"}), 200
    tid = players.get(phone)
    if tid and tid in tournaments:
        tournament = tournaments[tid]
        q = tournament.get("current_question")
        if q and text in ("A", "B", "C", "D", "1", "2", "3", "4"):
            idx = {"A": 0, "B": 1, "C": 2, "D": 3, "1": 0, "2": 1, "3": 2, "4": 3}.get(text, -1)
            player = tournament["players"].get(phone, {})
            player["answers"] = player.get("answers", 0) + 1
            if idx == q.get("correct_index"):
                player["score"] = player.get("score", 0) + 10
                player["correct"] = player.get("correct", 0) + 1
                send_sms(phone, f"Correct! +10 pts. Total: {player['score']}. {q.get('fun_fact', '')}")
            else:
                correct_letter = chr(65 + q["correct_index"])
                send_sms(phone, f"Wrong! Answer was {correct_letter}: {q['options'][q['correct_index']]}. Score: {player['score']}")
        return jsonify({"status": "answered"}), 200
    send_sms(phone, "Text JOIN <code> to enter a tournament.")
    return jsonify({"status": "info"}), 200

@app.route("/tournament/<tid>/next", methods=["POST"])
def next_round(tid):
    tournament = tournaments.get(tid)
    if not tournament: return jsonify({"error": "Not found"}), 404
    tournament["status"] = "active"
    tournament["current_round"] += 1
    if tournament["current_round"] > tournament["rounds"]:
        tournament["status"] = "finished"
        sorted_players = sorted(tournament["players"].items(), key=lambda x: x[1]["score"], reverse=True)
        for i, (phone, p) in enumerate(sorted_players):
            send_sms(phone, f"Tournament over! You placed #{i+1} with {p['score']} points!")
        return jsonify({"status": "finished"}), 200
    q = generate_question(tournament["category"])
    tournament["current_question"] = q
    opts = chr(10).join(f"{chr(65+i)}) {o}" for i, o in enumerate(q["options"]))
    msg = f"Round {tournament['current_round']}/{tournament['rounds']}:\n{q['question']}\n{opts}\nReply A/B/C/D"
    for phone in tournament["players"]:
        send_sms(phone, msg)
    return jsonify({"round": tournament["current_round"], "question": q["question"]}), 200

@app.route("/tournament/<tid>/leaderboard", methods=["GET"])
def leaderboard(tid):
    tournament = tournaments.get(tid)
    if not tournament: return jsonify({"error": "Not found"}), 404
    board = sorted([{"phone": p[-4:], "score": d["score"], "correct": d["correct"]} for p, d in tournament["players"].items()], key=lambda x: x["score"], reverse=True)
    return jsonify({"leaderboard": board}), 200

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "tournaments": len(tournaments)}), 200

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
