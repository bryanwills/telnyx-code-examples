#!/usr/bin/env python3
"""AI Audiobook Narrator — submit text, inference chunks and adds pacing/emotion
markup, TTS narrates each chapter with consistent voice, stores final audio
in Telnyx Cloud Storage."""

import os, json, uuid, requests
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, request, jsonify

load_dotenv()
app = Flask(__name__)

TELNYX_API_KEY = os.getenv("TELNYX_API_KEY")
AI_MODEL = os.getenv("AI_MODEL", "moonshotai/Kimi-K2.6")
TTS_MODEL = os.getenv("TTS_MODEL", "telnyx/tts")
BUCKET_NAME = os.getenv("BUCKET_NAME", "audiobooks")
DEFAULT_VOICE = os.getenv("DEFAULT_VOICE", "nova")
API = "https://api.telnyx.com/v2"
HEADERS = {"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"}

NARRATOR_VOICES = {
    "warm_female": "nova",
    "deep_male": "onyx",
    "neutral_male": "echo",
    "bright_female": "shimmer",
    "calm_neutral": "alloy",
}

books = {}


def inference(messages, max_tokens=4000):
    resp = requests.post(f"{API}/ai/chat/completions", headers=HEADERS, json={
        "model": AI_MODEL, "messages": messages, "max_tokens": max_tokens, "temperature": 0.3
    }, timeout=60)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def tts_generate(text, voice=None):
    resp = requests.post(f"{API}/ai/generate", headers=HEADERS, json={
        "model": TTS_MODEL, "voice": voice or DEFAULT_VOICE,
        "text": text, "output_format": "mp3"
    }, timeout=60)
    resp.raise_for_status()
    return resp.content


def upload_to_storage(bucket, key, data, content_type="audio/mpeg"):
    """Upload audio to Telnyx Cloud Storage."""
    resp = requests.put(
        f"https://storage.telnyx.com/{bucket}/{key}",
        headers={"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": content_type},
        data=data, timeout=60
    )
    resp.raise_for_status()
    return f"https://storage.telnyx.com/{bucket}/{key}"


@app.route("/books/narrate", methods=["POST"])
def narrate_book():
    """Submit text for audiobook narration.

    Pipeline: AI chunks into chapters → adds pacing/emotion cues → TTS per chapter → Cloud Storage.
    """
    data = request.get_json() or {}
    title = data.get("title", "Untitled")
    text = data.get("text", "")
    voice = data.get("voice", DEFAULT_VOICE)
    author = data.get("author", "Unknown")

    if not text:
        return jsonify({"error": "Provide 'text' to narrate"}), 400

    book_id = f"book-{uuid.uuid4().hex[:8]}"
    books[book_id] = {
        "id": book_id, "title": title, "author": author, "voice": voice,
        "status": "chunking", "chapters": [], "total_audio_bytes": 0,
        "storage_urls": [], "created_at": datetime.utcnow().isoformat()
    }

    # Step 1: AI chunks text into chapters with narration cues
    try:
        chunking_result = inference([
            {"role": "system", "content": """You are an audiobook production assistant. Break this text into narrated chapters.
For each chapter, return JSON array with objects:
- "chapter_number": int
- "chapter_title": string (generate a title)
- "narration_text": string (the text to read, with natural pauses indicated by '...' and emphasis by *word*)
- "tone": string (warm, dramatic, contemplative, energetic, somber)
- "pacing": string (slow, moderate, brisk)
Keep each chapter under 2000 characters for optimal TTS quality."""},
            {"role": "user", "content": text[:15000]}
        ], max_tokens=4000)
        chapters = json.loads(chunking_result)
    except json.JSONDecodeError:
        # Fallback: split by paragraphs
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        chunk_size = max(1, len(paragraphs) // 5)
        chapters = []
        for i in range(0, len(paragraphs), chunk_size):
            chunk = "\n\n".join(paragraphs[i:i+chunk_size])
            chapters.append({
                "chapter_number": len(chapters) + 1,
                "chapter_title": f"Chapter {len(chapters) + 1}",
                "narration_text": chunk,
                "tone": "warm",
                "pacing": "moderate"
            })
    except Exception as e:
        books[book_id]["status"] = "failed"
        books[book_id]["error"] = str(e)
        return jsonify(books[book_id]), 500

    # Step 2: Generate TTS for each chapter
    books[book_id]["status"] = "narrating"
    for chapter in chapters:
        narration = chapter.get("narration_text", "")
        if not narration:
            continue

        try:
            audio = tts_generate(narration, voice=voice)
            chapter_data = {
                "number": chapter.get("chapter_number", 0),
                "title": chapter.get("chapter_title", ""),
                "tone": chapter.get("tone", "warm"),
                "pacing": chapter.get("pacing", "moderate"),
                "text_length": len(narration),
                "audio_bytes": len(audio)
            }

            # Step 3: Upload to Cloud Storage
            try:
                key = f"{book_id}/chapter-{chapter_data['number']:02d}.mp3"
                url = upload_to_storage(BUCKET_NAME, key, audio)
                chapter_data["storage_url"] = url
                books[book_id]["storage_urls"].append(url)
            except Exception as e:
                chapter_data["storage_error"] = str(e)

            books[book_id]["chapters"].append(chapter_data)
            books[book_id]["total_audio_bytes"] += len(audio)

        except Exception as e:
            books[book_id]["chapters"].append({
                "number": chapter.get("chapter_number", 0),
                "title": chapter.get("chapter_title", ""),
                "error": str(e)
            })

    books[book_id]["status"] = "complete"
    books[book_id]["completed_at"] = datetime.utcnow().isoformat()

    return jsonify({
        "book_id": book_id,
        "title": title,
        "status": "complete",
        "chapters": len(books[book_id]["chapters"]),
        "total_audio_mb": round(books[book_id]["total_audio_bytes"] / 1048576, 2),
        "voice": voice,
        "storage_urls": books[book_id]["storage_urls"]
    }), 201


@app.route("/books/<book_id>", methods=["GET"])
def get_book(book_id):
    book = books.get(book_id)
    if not book:
        return jsonify({"error": "Book not found"}), 404
    return jsonify(book)


@app.route("/books", methods=["GET"])
def list_books():
    return jsonify({"books": [{
        "id": b["id"], "title": b["title"], "author": b["author"],
        "status": b["status"], "chapters": len(b["chapters"]),
        "created_at": b["created_at"]
    } for b in books.values()]})


@app.route("/voices", methods=["GET"])
def list_voices():
    return jsonify({"voices": NARRATOR_VOICES})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok", "total_books": len(books),
        "bucket": BUCKET_NAME, "version": "1.0.0"
    })


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
