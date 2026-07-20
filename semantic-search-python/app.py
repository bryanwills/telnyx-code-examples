#!/usr/bin/env python3
"""Semantic Search — index support tickets via Telnyx embeddings and search by meaning, not keywords."""
import os, json, time, math, requests, numpy as np
from dotenv import load_dotenv
from flask import Flask, request, jsonify
load_dotenv()
app = Flask(__name__)
TELNYX_API_KEY = os.getenv("TELNYX_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "thenlper/gte-large")
EMBEDDINGS_URL = "https://api.telnyx.com/v2/ai/openai/embeddings"
SAMPLE_TICKETS_PATH = os.path.join(os.path.dirname(__file__), "sample_tickets.json")
tickets = {}
vectors = None
dims = 0
indexed_at = None

def get_embeddings(texts, batch_size=8):
    """Call Telnyx embeddings API. Returns list of float vectors."""
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        resp = requests.post(EMBEDDINGS_URL,
            headers={"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"},
            json={"input": batch, "model": EMBEDDING_MODEL}, timeout=40)
        resp.raise_for_status()
        data = resp.json().get("data", [])
        all_embeddings.extend([d["embedding"] for d in data])
    return all_embeddings

def cosine_similarity(vec, matrix):
    """Cosine similarity between a query vector and a matrix of doc vectors."""
    vec_norm = vec / (np.linalg.norm(vec) + 1e-10)
    matrix_norm = matrix / (np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-10)
    return np.dot(matrix_norm, vec_norm)

def load_sample_tickets():
    with open(SAMPLE_TICKETS_PATH, "r") as f:
        return json.load(f)

def build_index(ticket_list):
    global tickets, vectors, dims, indexed_at
    texts = [f"{t['subject']}. {t['body']}" for t in ticket_list]
    embeddings = get_embeddings(texts)
    vectors = np.array(embeddings, dtype=np.float32)
    dims = vectors.shape[1] if vectors.size else 0
    tickets = {t["id"]: t for t in ticket_list}
    indexed_at = time.strftime("%Y-%m-%dT%H:%M:%SZ")

@app.route("/index", methods=["POST"])
def index_tickets():
    data = request.get_json(silent=True) or {}
    ticket_list = data.get("tickets")
    if not ticket_list:
        ticket_list = load_sample_tickets()
    try:
        build_index(ticket_list)
        return jsonify({
            "status": "indexed",
            "ticket_count": len(tickets),
            "dimensions": dims,
            "model": EMBEDDING_MODEL,
            "indexed_at": indexed_at,
        }), 200
    except Exception:
        app.logger.exception("indexing failed")
        return jsonify({"error": "internal error"}), 500

@app.route("/search", methods=["POST"])
def search_tickets():
    global vectors
    data = request.get_json()
    if not data:
        return jsonify({"error": "invalid request body"}), 400
    query = data.get("query", "").strip()
    if not query:
        return jsonify({"error": "query field is required"}), 400
    top_k = int(data.get("top_k", 5))
    if top_k < 1 or top_k > 50:
        return jsonify({"error": "top_k must be between 1 and 50"}), 400
    if vectors is None or not tickets:
        return jsonify({"error": "index is empty — call POST /index first"}), 400
    try:
        query_vec = np.array(get_embeddings([query])[0], dtype=np.float32)
        scores = cosine_similarity(query_vec, vectors)
        ranked = np.argsort(scores)[::-1][:top_k]
        ticket_ids = list(tickets.keys())
        results = []
        for idx in ranked:
            tid = ticket_ids[idx]
            t = tickets[tid]
            results.append({
                "ticket_id": tid,
                "subject": t.get("subject"),
                "body": t.get("body"),
                "category": t.get("category"),
                "priority": t.get("priority"),
                "score": float(round(scores[idx], 4)),
            })
        return jsonify({
            "query": query,
            "model": EMBEDDING_MODEL,
            "results": results,
            "total_indexed": len(tickets),
        }), 200
    except Exception:
        app.logger.exception("search failed")
        return jsonify({"error": "internal error"}), 500

@app.route("/tickets", methods=["POST"])
def add_ticket():
    global vectors, tickets
    data = request.get_json()
    if not data:
        return jsonify({"error": "invalid request body"}), 400
    subject = data.get("subject", "").strip()
    body = data.get("body", "").strip()
    if not subject or not body:
        return jsonify({"error": "subject and body are required"}), 400
    if vectors is None or not tickets:
        return jsonify({"error": "index is empty — call POST /index first"}), 400
    ticket_id = data.get("id") or f"TKT-{int(time.time())}"
    ticket = {
        "id": ticket_id,
        "subject": subject,
        "body": body,
        "category": data.get("category"),
        "priority": data.get("priority"),
        "created_at": data.get("created_at") or time.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    try:
        embedding = get_embeddings([f"{subject}. {body}"])[0]
        new_vec = np.array([embedding], dtype=np.float32)
        vectors = np.vstack([vectors, new_vec])
        tickets[ticket_id] = ticket
        return jsonify({"status": "added", "ticket_id": ticket_id}), 201
    except Exception:
        app.logger.exception("add ticket failed")
        return jsonify({"error": "internal error"}), 500

@app.route("/tickets/<ticket_id>", methods=["GET"])
def get_ticket(ticket_id):
    t = tickets.get(ticket_id)
    if not t:
        return jsonify({"error": "ticket not found"}), 404
    return jsonify(t), 200

@app.route("/stats", methods=["GET"])
def stats():
    return jsonify({
        "ticket_count": len(tickets),
        "dimensions": dims,
        "model": EMBEDDING_MODEL,
        "indexed_at": indexed_at,
        "indexed": vectors is not None,
    }), 200

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "tickets": len(tickets), "indexed": vectors is not None, "version": "1.0.0"}), 200

if __name__ == "__main__":
    app.run(debug=False, host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", "5000")))
