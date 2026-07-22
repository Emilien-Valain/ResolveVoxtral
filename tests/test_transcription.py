import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest
import requests

from resolvevoxtral import transcription
from resolvevoxtral.errors import TranscriptionError


class FakeResponse:
    def __init__(self, status_code, json_data=None):
        self.status_code = status_code
        self.ok = 200 <= status_code < 300
        self._json_data = json_data or {}

    def json(self):
        return self._json_data


@pytest.fixture
def audio_file(tmp_path):
    path = tmp_path / "audio.wav"
    path.write_bytes(b"fake-audio")
    return path


def test_normalize_segment_reads_speaker_key():
    seg = transcription._normalize_segment({"start": 1, "end": 2, "text": "hi", "speaker": "SPEAKER_00"})
    assert seg.speaker == "SPEAKER_00"


def test_normalize_segment_falls_back_to_speaker_id_key():
    seg = transcription._normalize_segment({"start": 1, "end": 2, "text": "hi", "speaker_id": "SPEAKER_01"})
    assert seg.speaker == "SPEAKER_01"


def test_normalize_segment_defaults_speaker_to_none():
    seg = transcription._normalize_segment({"start": 1, "end": 2, "text": "hi"})
    assert seg.speaker is None


def test_transcribe_success_returns_segments(monkeypatch, audio_file):
    monkeypatch.setattr(requests, "post", lambda *a, **k: FakeResponse(200, {
        "segments": [{"start": 0, "end": 1, "text": "hello", "speaker": "SPEAKER_00"}]
    }))
    segments = transcription.transcribe(audio_file, "key")
    assert len(segments) == 1
    assert segments[0].text == "hello"


def test_transcribe_raises_on_invalid_key(monkeypatch, audio_file):
    monkeypatch.setattr(requests, "post", lambda *a, **k: FakeResponse(401))
    with pytest.raises(TranscriptionError, match="rejected"):
        transcription.transcribe(audio_file, "bad-key")


def test_transcribe_raises_on_rate_limit(monkeypatch, audio_file):
    monkeypatch.setattr(requests, "post", lambda *a, **k: FakeResponse(429))
    with pytest.raises(TranscriptionError, match="rate-limiting"):
        transcription.transcribe(audio_file, "key")


def test_transcribe_raises_on_connection_error(monkeypatch, audio_file):
    def raise_connection_error(*a, **k):
        raise requests.exceptions.ConnectionError()
    monkeypatch.setattr(requests, "post", raise_connection_error)
    with pytest.raises(TranscriptionError, match="internet connection"):
        transcription.transcribe(audio_file, "key")


def test_transcribe_falls_back_when_language_and_timestamps_conflict(monkeypatch, audio_file):
    calls = []

    def fake_post(url, headers, data, files, timeout):
        calls.append(dict(data))
        if "language" in data:
            return FakeResponse(400, {"message": "language incompatible with timestamp_granularities"})
        return FakeResponse(200, {"segments": [{"start": 0, "end": 1, "text": "bonjour", "speaker": "SPEAKER_00"}]})

    monkeypatch.setattr(requests, "post", fake_post)
    segments = transcription.transcribe(audio_file, "key", language_override="french")

    assert len(calls) == 2
    assert "language" in calls[0]
    assert "language" not in calls[1]
    assert segments[0].text == "bonjour"
