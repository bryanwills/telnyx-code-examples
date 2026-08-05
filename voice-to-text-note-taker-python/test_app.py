#!/usr/bin/env python3
"""Tests for the Telnyx Speech Translator app. Uses Flask test client
with mocked Telnyx API responses."""

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
        self.assertIn("target_languages", data)


class TestTranscribe(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()
        _store.clear()

    def test_no_audio_file(self):
        r = self.client.post("/transcribe")
        self.assertEqual(r.status_code, 400)
        self.assertIn("audio", r.get_json()["error"].lower())

    def test_empty_audio(self):
        data = {"audio": (io.BytesIO(b""), "test.webm")}
        r = self.client.post(
            "/transcribe", data=data, content_type="multipart/form-data"
        )
        self.assertEqual(r.status_code, 400)
        self.assertIn("empty", r.get_json()["error"].lower())

    def test_unsupported_format(self):
        data = {"audio": (io.BytesIO(b"fake"), "test.xyz")}
        r = self.client.post(
            "/transcribe", data=data, content_type="multipart/form-data"
        )
        self.assertEqual(r.status_code, 400)
        self.assertIn("unsupported", r.get_json()["error"].lower())

    @patch("app._call_stt")
    def test_successful_transcription(self, mock_stt):
        mock_stt.return_value = {"text": "Hello world", "language": "English"}
        data = {"audio": (io.BytesIO(b"fake-audio-data"), "test.webm")}
        r = self.client.post(
            "/transcribe", data=data, content_type="multipart/form-data"
        )
        self.assertEqual(r.status_code, 200)
        result = r.get_json()
        self.assertEqual(result["transcript"], "Hello world")
        self.assertEqual(result["detected_language"], "English")
        self.assertIn("note_id", result)
        self.assertIn("download_url", result)

    @patch("app._call_stt")
    def test_empty_transcript_from_stt(self, mock_stt):
        mock_stt.return_value = {"text": "", "language": "English"}
        data = {"audio": (io.BytesIO(b"fake"), "test.webm")}
        r = self.client.post(
            "/transcribe", data=data, content_type="multipart/form-data"
        )
        self.assertEqual(r.status_code, 502)
        self.assertIn("empty transcript", r.get_json()["error"].lower())

    @patch("app._call_stt")
    def test_stt_http_error(self, mock_stt):
        import requests

        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.text = "Unauthorized"
        mock_stt.side_effect = requests.HTTPError(response=mock_resp)
        data = {"audio": (io.BytesIO(b"fake"), "test.webm")}
        r = self.client.post(
            "/transcribe", data=data, content_type="multipart/form-data"
        )
        self.assertEqual(r.status_code, 502)


class TestTranslate(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()
        _store.clear()

    def test_no_source_text(self):
        r = self.client.post("/translate", json={"target_language": "Spanish"})
        self.assertEqual(r.status_code, 400)

    def test_unsupported_language(self):
        r = self.client.post(
            "/translate", json={"source_text": "Hello", "target_language": "Korean"}
        )
        self.assertEqual(r.status_code, 400)
        self.assertIn("unsupported", r.get_json()["error"].lower())

    @patch("app._call_translate")
    def test_successful_translation(self, mock_translate):
        mock_translate.return_value = "Hola mundo"
        r = self.client.post(
            "/translate",
            json={"source_text": "Hello world", "target_language": "Spanish"},
        )
        self.assertEqual(r.status_code, 200)
        result = r.get_json()
        self.assertEqual(result["translated_text"], "Hola mundo")
        self.assertEqual(result["target_language"], "Spanish")
        self.assertIn("translation_id", result)

    @patch("app._call_translate")
    def test_translation_model_failure(self, mock_translate):
        mock_translate.side_effect = ValueError("empty content")
        r = self.client.post(
            "/translate", json={"source_text": "Hello", "target_language": "Spanish"}
        )
        self.assertEqual(r.status_code, 502)


class TestSynthesize(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()
        _store.clear()

    def test_no_text(self):
        r = self.client.post("/synthesize", json={"target_language": "Spanish"})
        self.assertEqual(r.status_code, 400)

    def test_unsupported_language(self):
        r = self.client.post(
            "/synthesize", json={"text": "Hola", "target_language": "Korean"}
        )
        self.assertEqual(r.status_code, 400)

    @patch("app._call_tts")
    def test_successful_synthesis(self, mock_tts):
        mock_tts.return_value = b"fake-audio-bytes"
        r = self.client.post(
            "/synthesize", json={"text": "Hola mundo", "target_language": "Spanish"}
        )
        self.assertEqual(r.status_code, 200)
        result = r.get_json()
        self.assertIn("audio_id", result)
        self.assertIn("audio_url", result)
        self.assertIn("download_url", result)

    @patch("app._call_tts")
    def test_tts_empty_audio(self, mock_tts):
        mock_tts.return_value = b""
        r = self.client.post(
            "/synthesize", json={"text": "Hola", "target_language": "Spanish"}
        )
        self.assertEqual(r.status_code, 502)


class TestDownloads(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()
        _store.clear()

    def test_download_nonexistent_note(self):
        r = self.client.get("/notes/nonexistent-id/download")
        self.assertEqual(r.status_code, 404)

    def test_download_nonexistent_audio(self):
        r = self.client.get("/audio/nonexistent-id/download")
        self.assertEqual(r.status_code, 404)

    @patch("app._call_stt")
    def test_download_transcript_after_transcription(self, mock_stt):
        mock_stt.return_value = {"text": "Test transcript", "language": "English"}
        data = {"audio": (io.BytesIO(b"fake"), "test.webm")}
        r = self.client.post(
            "/transcribe", data=data, content_type="multipart/form-data"
        )
        note_id = r.get_json()["note_id"]
        r2 = self.client.get(f"/notes/{note_id}/download")
        self.assertEqual(r2.status_code, 200)

    @patch("app._call_tts")
    def test_download_audio_after_synthesis(self, mock_tts):
        mock_tts.return_value = b"fake-audio"
        r = self.client.post(
            "/synthesize", json={"text": "Hola", "target_language": "Spanish"}
        )
        audio_id = r.get_json()["audio_id"]
        r2 = self.client.get(f"/audio/{audio_id}/download")
        self.assertEqual(r2.status_code, 200)


if __name__ == "__main__":
    unittest.main()
