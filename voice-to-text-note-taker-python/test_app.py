#!/usr/bin/env python3
"""Tests for Voice Flashcards. Uses Flask test client with mocked Telnyx API."""

import io
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

os.environ["TELNYX_API_KEY"] = "test-key"
os.environ["STT_MODEL"] = "openai/whisper-large-v3-turbo"
os.environ["TRANSLATION_MODEL"] = "moonshotai/Kimi-K2.6"
os.environ["TTS_VOICE"] = "Telnyx.Ultra.test-uuid"

sys.path.insert(0, os.path.dirname(__file__))
from app import app, _store


class TestHealth(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_health_ok(self):
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertEqual(data["status"], "ok")
        self.assertIn("decks", data)


class TestDecks(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_list_decks(self):
        r = self.client.get("/decks")
        self.assertEqual(r.status_code, 200)
        decks = r.get_json()["decks"]
        self.assertTrue(len(decks) > 0)

    def test_get_deck(self):
        r = self.client.get("/deck/Spanish%20%E2%80%94%20Greetings")
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertEqual(data["language"], "Spanish")
        self.assertTrue(len(data["cards"]) > 0)

    def test_nonexistent_deck(self):
        r = self.client.get("/deck/Nonexistent")
        self.assertEqual(r.status_code, 404)


class TestSpeak(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()
        _store.clear()

    def test_no_text(self):
        r = self.client.post("/speak", json={"language": "Spanish"})
        self.assertEqual(r.status_code, 400)

    def test_unsupported_language(self):
        r = self.client.post("/speak", json={"text": "Hola", "language": "Korean"})
        self.assertEqual(r.status_code, 400)

    @patch("app._call_tts")
    def test_successful_speak(self, mock_tts):
        mock_tts.return_value = b"fake-audio"
        r = self.client.post("/speak", json={"text": "Hola", "language": "Spanish"})
        self.assertEqual(r.status_code, 200)
        result = r.get_json()
        self.assertIn("audio_id", result)
        self.assertIn("audio_url", result)

    @patch("app._call_tts")
    def test_tts_empty_audio(self, mock_tts):
        mock_tts.return_value = b""
        r = self.client.post("/speak", json={"text": "Hola", "language": "Spanish"})
        self.assertEqual(r.status_code, 502)


class TestCheck(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()
        _store.clear()

    def test_no_audio(self):
        r = self.client.post(
            "/check", data={"target_phrase": "Hola", "language": "Spanish"}
        )
        self.assertEqual(r.status_code, 400)

    def test_no_target_phrase(self):
        data = {"audio": (io.BytesIO(b"fake"), "test.webm")}
        r = self.client.post("/check", data=data, content_type="multipart/form-data")
        self.assertEqual(r.status_code, 400)

    def test_empty_audio(self):
        data = {
            "audio": (io.BytesIO(b""), "test.webm"),
            "target_phrase": "Hola",
            "language": "Spanish",
        }
        r = self.client.post("/check", data=data, content_type="multipart/form-data")
        self.assertEqual(r.status_code, 400)

    def test_unsupported_format(self):
        data = {
            "audio": (io.BytesIO(b"fake"), "test.xyz"),
            "target_phrase": "Hola",
            "language": "Spanish",
        }
        r = self.client.post("/check", data=data, content_type="multipart/form-data")
        self.assertEqual(r.status_code, 400)

    @patch("app._call_stt")
    @patch("app._call_check")
    def test_successful_check_correct(self, mock_check, mock_stt):
        mock_stt.return_value = {"text": "Hola, como estas?"}
        mock_check.return_value = {"score": "correct", "feedback": "Perfect!"}
        data = {
            "audio": (io.BytesIO(b"fake"), "test.webm"),
            "target_phrase": "Hola, como estas?",
            "language": "Spanish",
        }
        r = self.client.post("/check", data=data, content_type="multipart/form-data")
        self.assertEqual(r.status_code, 200)
        result = r.get_json()
        self.assertEqual(result["score"], "correct")
        self.assertEqual(result["feedback"], "Perfect!")
        self.assertEqual(result["target_phrase"], "Hola, como estas?")

    @patch("app._call_stt")
    @patch("app._call_check")
    def test_check_wrong(self, mock_check, mock_stt):
        mock_stt.return_value = {"text": "Hello there"}
        mock_check.return_value = {"score": "wrong", "feedback": "Try again"}
        data = {
            "audio": (io.BytesIO(b"fake"), "test.webm"),
            "target_phrase": "Hola",
            "language": "Spanish",
        }
        r = self.client.post("/check", data=data, content_type="multipart/form-data")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["score"], "wrong")

    @patch("app._call_stt")
    def test_empty_transcript(self, mock_stt):
        mock_stt.return_value = {"text": ""}
        data = {
            "audio": (io.BytesIO(b"fake"), "test.webm"),
            "target_phrase": "Hola",
            "language": "Spanish",
        }
        r = self.client.post("/check", data=data, content_type="multipart/form-data")
        self.assertEqual(r.status_code, 502)

    @patch("app._call_stt")
    @patch("app._call_check")
    def test_inference_failure(self, mock_check, mock_stt):
        mock_stt.return_value = {"text": "Hola"}
        mock_check.side_effect = ValueError("invalid JSON")
        data = {
            "audio": (io.BytesIO(b"fake"), "test.webm"),
            "target_phrase": "Hola",
            "language": "Spanish",
        }
        r = self.client.post("/check", data=data, content_type="multipart/form-data")
        self.assertEqual(r.status_code, 502)


class TestAudio(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()
        _store.clear()

    def test_nonexistent_audio(self):
        r = self.client.get("/audio/nonexistent")
        self.assertEqual(r.status_code, 404)

    @patch("app._call_tts")
    def test_serve_audio(self, mock_tts):
        mock_tts.return_value = b"fake-audio"
        r = self.client.post("/speak", json={"text": "Hola", "language": "Spanish"})
        audio_id = r.get_json()["audio_id"]
        r2 = self.client.get(f"/audio/{audio_id}")
        self.assertEqual(r2.status_code, 200)


if __name__ == "__main__":
    unittest.main()
